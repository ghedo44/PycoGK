# Chapter 1: Orientation

## What pycogk Is

pycogk is a Python wrapper around the PicoGK native runtime.

It is designed to make computational geometry scripting practical in Python while preserving familiar PicoGK concepts.

This is not the official PicoGK package. It is a community-maintained Python package that references the official runtime and APIs.

## Official vs Unofficial

1. Official runtime and core engine are part of the official PicoGK project.
2. pycogk provides Python ergonomics, packaging, and workflow tooling around that runtime.

Official PicoGK: https://github.com/leap71/PicoGK

## What Problems It Solves

pycogk is useful when you need:

1. Programmatic geometry generation for engineering.
2. Voxel booleans and offsets for manufacturable shapes.
3. Scripted export to STL, VDB, CLI, and image outputs.
4. Fast iteration in Python notebooks and scripts.

## Mental Model

Think in five steps:

1. Create geometry (lattice, mesh, fields).
2. Voxelize and process.
3. Convert to mesh/slices/fields.
4. Export or visualize.
5. Integrate into pipelines.

## API Regions

The main API is exposed from `picogk`:

1. Runtime orchestration: `go`, `Library`
2. Geometry: `Lattice`, `Voxels`, `Mesh`, `PolyLine`
3. Fields: `ScalarField`, `VectorField`, `FieldMetadata`
4. IO: `OpenVdbFile`, `MeshIo`, `Cli`, `TgaIo`
5. Utilities: `FieldUtils`, `Utils`, `Vector3Ext`, `Animation`

## Chapter Summary

You now know what pycogk is and how it relates to official PicoGK.

Next: install and runtime setup.
