
from dataclasses import dataclass
from enum import IntEnum
import math
from pathlib import Path
import time
from typing import Sequence

from .slice import PolyContour, PolySlice, PolySliceStack
from .utils import Utils


class Cli:
    class EFormat(IntEnum):
        UseEmptyFirstLayer = 0
        FirstLayerWithContent = 1

    @dataclass
    class Result:
        oSlices: PolySliceStack
        oBBoxFile: tuple[tuple[float, float, float], tuple[float, float, float]]
        bBinary: bool
        fUnitsHeader: float
        b32BitAlign: bool
        nVersion: int
        strHeaderDate: str
        nLayers: int
        strWarnings: str

    @staticmethod
    def _extract_parameter(line: str) -> tuple[bool, str, str]:
        if not line:
            return (False, "", line)
        if line[0] not in "/,":
            return (False, "", line)
        line = line[1:]
        end = len(line)
        for i, ch in enumerate(line):
            if ch in "$/,":
                end = i
                break
        param = line[:end]
        rest = line[end:]
        return (True, param, rest)

    @staticmethod
    def _safe_float(text: str, context: str) -> float:
        try:
            return float(text)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid parameter for {context}: {text}") from exc

    @staticmethod
    def _safe_uint(text: str, context: str) -> int:
        try:
            value = int(text)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Invalid parameter for {context}: {text}") from exc
        if value < 0:
            raise ValueError(f"Invalid parameter for {context}: {text}")
        return value

    @staticmethod
    def WriteSlicesToCliFile(
        oSlices: PolySliceStack | Sequence[PolySlice],
        strFilePath: str | Path,
        eFormat: "Cli.EFormat" = EFormat.FirstLayerWithContent,
        strDate: str = "",
        fUnitsInMM: float = 0.0,
    ) -> None:
        stack = oSlices if isinstance(oSlices, PolySliceStack) else PolySliceStack(oSlices)

        if stack.nCount() < 1 or (math.isinf(stack.oBBox().vecMin[0]) and math.isinf(stack.oBBox().vecMin[1])):
            raise ValueError("No valid slices detected (empty)")

        if fUnitsInMM <= 0.0:
            fUnitsInMM = 1.0
        if not strDate:
            strDate = time.strftime("%Y-%m-%d")

        bbox = stack.oBBox()
        nSliceCount = stack.nCount() + (1 if eFormat == Cli.EFormat.UseEmptyFirstLayer else 0)
        strDim = (
            f"{bbox.vecMin[0]:08.5f},{bbox.vecMin[1]:08.5f},{0.0:08.5f},"
            f"{bbox.vecMax[0]:08.5f},{bbox.vecMax[1]:08.5f},{stack.oSliceAt(stack.nCount() - 1).fZPos():08.5f}"
        )

        with open(strFilePath, "w", encoding="ascii", newline="\n") as handle:
            handle.write("$$HEADERSTART\n")
            handle.write("$$ASCII\n")
            handle.write(f"$$UNITS/{fUnitsInMM}\n")
            handle.write("$$VERSION/200\n")
            handle.write("$$LABEL/1,default\n")
            handle.write(f"$$DATE/{strDate}\n")
            handle.write(f"$$DIMENSION/{strDim}\n")
            handle.write(f"$$LAYERS/{nSliceCount:05d}\n")
            handle.write("$$HEADEREND\n")
            handle.write("$$GEOMETRYSTART\n")

            if eFormat == Cli.EFormat.UseEmptyFirstLayer:
                handle.write("$$LAYER/0.0\n")

            for nLayer in range(stack.nCount()):
                sl = stack.oSliceAt(nLayer)
                handle.write(f"$$LAYER/{(sl.fZPos() / fUnitsInMM):0.5f}\n")

                for nPass in range(3):
                    for nPolyline in range(sl.nContours()):
                        poly = sl.oContourAt(nPolyline)
                        if nPass == 0 and poly.eWinding() != PolyContour.EWinding.COUNTERCLOCKWISE:
                            continue
                        if nPass == 1 and poly.eWinding() != PolyContour.EWinding.CLOCKWISE:
                            continue
                        if nPass == 2 and poly.eWinding() != PolyContour.EWinding.UNKNOWN:
                            continue

                        nWinding = 2
                        if poly.eWinding() == PolyContour.EWinding.CLOCKWISE:
                            nWinding = 0
                        elif poly.eWinding() == PolyContour.EWinding.COUNTERCLOCKWISE:
                            nWinding = 1

                        entries = ["$$POLYLINE/1", str(nWinding), str(poly.nCount())]
                        for nVertex in range(poly.nCount()):
                            vx, vy = poly.vecVertex(nVertex)
                            entries.append(f"{(vx / fUnitsInMM):0.5f}")
                            entries.append(f"{(vy / fUnitsInMM):0.5f}")
                        handle.write(",".join(entries) + "\n")

            handle.write("$$GEOMETRYEND\n")

    @staticmethod
    def oSlicesFromCliFile(strFilePath: str | Path) -> "Cli.Result":
        with open(strFilePath, "r", encoding="ascii", errors="ignore") as handle:
            raw_lines = handle.readlines()

        warnings: list[str] = []
        in_comment = False
        n_label = None
        n_header_layer_numbers = 0
        b_binary = False
        f_units_header = 0.0
        b_32bit_align = False
        n_version = 0
        str_header_date = ""
        bbox_file = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]

        i = 0
        b_header_started = False
        b_header_ended = False
        while i < len(raw_lines) and not b_header_ended:
            line = raw_lines[i]
            i += 1

            while line != "":
                line = line.strip()
                if line.startswith("//"):
                    in_comment = True
                    line = line[2:]

                if in_comment:
                    end = line.find("//")
                    if end == -1:
                        line = ""
                        continue
                    line = line[end + 2 :].strip()
                    in_comment = False

                if not b_header_started:
                    idx = line.find("$$HEADERSTART")
                    if idx == -1:
                        break
                    line = line[idx + len("$$HEADERSTART") :].strip()
                    b_header_started = True
                    continue

                if not line.startswith("$$"):
                    break

                if line.startswith("$$BINARY"):
                    line = line[len("$$BINARY") :]
                    b_binary = True
                    continue
                if line.startswith("$$ASCII"):
                    line = line[len("$$ASCII") :]
                    b_binary = False
                    continue
                if line.startswith("$$ALIGN"):
                    line = line[len("$$ALIGN") :]
                    b_32bit_align = True
                    continue
                if line.startswith("$$UNITS"):
                    line = line[len("$$UNITS") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$UNITS")
                    f_units_header = Cli._safe_float(param, "$$UNITS")
                    if f_units_header <= 0.0:
                        raise ValueError(f"Invalid parameter for $$UNITS: {param}")
                    continue
                if line.startswith("$$VERSION"):
                    line = line[len("$$VERSION") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$VERSION")
                    n_version = Cli._safe_uint(param, "$$VERSION")
                    continue
                if line.startswith("$$LABEL"):
                    line = line[len("$$LABEL") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$LABEL")
                    if n_label is not None:
                        raise NotImplementedError("Currently we do not support multiple labels and objects in one CLI file")
                    n_label = Cli._safe_uint(param, "$$LABEL")
                    ok, _, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$LABEL (text)")
                    continue
                if line.startswith("$$DATE"):
                    line = line[len("$$DATE") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$DATE")
                    str_header_date = param.strip()
                    continue
                if line.startswith("$$DIMENSION"):
                    line = line[len("$$DIMENSION") :]
                    values: list[float] = []
                    for _ in range(6):
                        ok, param, line = Cli._extract_parameter(line)
                        if not ok:
                            raise ValueError("Missing parameter after $$DIMENSION")
                        values.append(Cli._safe_float(param, "$$DIMENSION"))
                    bbox_file[0] = [values[0], values[1], values[2]]
                    bbox_file[1] = [values[3], values[4], values[5]]
                    continue
                if line.startswith("$$LAYERS"):
                    line = line[len("$$LAYERS") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$LAYERS")
                    n_header_layer_numbers = Cli._safe_uint(param, "$$LAYERS")
                    continue
                if line.startswith("$$HEADEREND"):
                    b_header_ended = True
                    break

                break

        if not b_header_ended:
            raise ValueError("End of file while searching for valid header")

        if b_binary:
            raise NotImplementedError("Binary CLI Files are not yet supported")

        b_geometry_started = False
        b_geometry_ended = False
        o_current_slice: PolySlice | None = None
        slices: list[PolySlice] = []
        f_prev_z = float("-inf")

        while i < len(raw_lines) and not b_geometry_ended:
            line = raw_lines[i]
            i += 1
            while line != "":
                line = line.strip()
                if line.startswith("//"):
                    in_comment = True
                    line = line[2:]

                if in_comment:
                    end = line.find("//")
                    if end == -1:
                        line = ""
                        continue
                    line = line[end + 2 :].strip()
                    in_comment = False

                if not b_geometry_started:
                    idx = line.find("$$GEOMETRYSTART")
                    if idx == -1:
                        break
                    line = line[idx + len("$$GEOMETRYSTART") :].strip()
                    b_geometry_started = True
                    continue

                if line.startswith("$$LAYER"):
                    line = line[len("$$LAYER") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$LAYER")
                    f_z = Cli._safe_float(param, "$$LAYER") * f_units_header

                    if f_prev_z != float("-inf") and f_z < f_prev_z:
                        raise ValueError(f"Z position in current layer is smaller than in previous {param}")

                    if f_z > 0.0:
                        if o_current_slice is not None:
                            slices.append(o_current_slice)
                        o_current_slice = PolySlice(f_z)
                        f_prev_z = f_z
                    continue

                if line.startswith("$$POLYLINE"):
                    if o_current_slice is None:
                        raise ValueError("There should not be contours at z position 0")

                    line = line[len("$$POLYLINE") :]
                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$POLYLINE")
                    n_id = Cli._safe_uint(param, "$$POLYLINE")

                    if n_label is None:
                        n_label = n_id
                    if n_id != n_label:
                        raise NotImplementedError("We do not support CLI labels and multiple models yet")

                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter after $$POLYLINE")
                    n_winding = Cli._safe_uint(param, "$$POLYLINE direction")
                    if n_winding == 0:
                        declared = PolyContour.EWinding.CLOCKWISE
                    elif n_winding == 1:
                        declared = PolyContour.EWinding.COUNTERCLOCKWISE
                    elif n_winding == 2:
                        declared = PolyContour.EWinding.UNKNOWN
                    else:
                        raise ValueError(f"Invalid parameter for $$POLYLINE direction: {param}")

                    ok, param, line = Cli._extract_parameter(line)
                    if not ok:
                        raise ValueError("Missing parameter polygon count after $$POLYLINE")
                    n_count = Cli._safe_uint(param, "$$POLYLINE polygon count")

                    vertices: list[tuple[float, float]] = []
                    while n_count > 0:
                        ok, param, line = Cli._extract_parameter(line)
                        if not ok:
                            raise ValueError("Missing vertices in $$POLYLINE")
                        fx = Cli._safe_float(param, "$$POLYLINE vertex X") * f_units_header
                        ok, param, line = Cli._extract_parameter(line)
                        if not ok:
                            raise ValueError("Missing vertices in $$POLYLINE")
                        fy = Cli._safe_float(param, "$$POLYLINE vertex Y") * f_units_header
                        vertices.append((fx, fy))
                        n_count -= 1

                    if len(vertices) < 3:
                        warnings.append(f"Line: {i} Discarding POLYLINE with {len(vertices)} vertices which is degenerate")
                        continue

                    poly = PolyContour(vertices)
                    actual = poly.eWinding()
                    if actual == PolyContour.EWinding.UNKNOWN:
                        warnings.append(
                            f"Line: {i} Discarding POLYLINE with area 0 (degenerate) - defined with winding {PolyContour.strWindingAsString(declared)}"
                        )
                        continue
                    if actual != declared:
                        warnings.append(
                            f"Line: {i} POLYLINE defined with winding {PolyContour.strWindingAsString(declared)} actual winding is {PolyContour.strWindingAsString(actual)} (using actual)"
                        )
                    o_current_slice.AddContour(poly)
                    continue

                if line.startswith("$$GEOMETRYEND"):
                    b_geometry_ended = True
                    break

                if line.startswith("$$"):
                    warnings.append(f"Line: {i} Unsupported command {Utils.strShorten(line, 20)}")
                    line = ""
                    continue

                line = ""

        if o_current_slice is not None:
            slices.append(o_current_slice)

        result_stack = PolySliceStack(slices)
        return Cli.Result(
            oSlices=result_stack,
            oBBoxFile=((bbox_file[0][0], bbox_file[0][1], bbox_file[0][2]), (bbox_file[1][0], bbox_file[1][1], bbox_file[1][2])),
            bBinary=b_binary,
            fUnitsHeader=f_units_header,
            b32BitAlign=b_32bit_align,
            nVersion=n_version,
            strHeaderDate=str_header_date,
            nLayers=n_header_layer_numbers,
            strWarnings="\n".join(warnings),
        )


class CliIo(Cli):
    @staticmethod
    def WriteSlicesToCliFile(
        oSlices: PolySliceStack | Sequence[PolySlice],
        strFilePath: str | Path,
        eFormat: "Cli.EFormat" = Cli.EFormat.FirstLayerWithContent,
        strDate: str = "",
        fUnitsInMM: float = 0.0,
    ) -> None:
        Cli.WriteSlicesToCliFile(oSlices, strFilePath, eFormat, strDate, fUnitsInMM)

    @staticmethod
    def oSlicesFromCliFile(strFilePath: str | Path) -> "Cli.Result":
        return Cli.oSlicesFromCliFile(strFilePath)

