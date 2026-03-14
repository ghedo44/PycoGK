class PicoGKError(RuntimeError):
    """Base exception for picogk-python."""


class PicoGKLoadError(PicoGKError):
    """Raised when the native runtime cannot be loaded."""


class PicoGKDisposedError(PicoGKError):
    """Raised when a disposed native wrapper is used."""


class PicoGKInvalidHandleError(PicoGKError):
    """Raised when the runtime returns a null/invalid handle."""
