from typing import List, Sequence

# These functions are used to check that the user input is valid:
# - integers are actually integers
# - lists are lists of integers
# - direction is 'left' or 'right'
# They raise clear errors if something is wrong.

def valid_int(v: object, n: str, min_v: int | None = None) -> int:
    """Check that `v` is an integer and optionally greater than or equal to `min_v`."""
    if isinstance(v, bool) or not isinstance(v, int):
        raise TypeError(f"{n} must be an integer.")
    if min_v is not None and v < min_v:
        raise ValueError(f"{n} must be >= {min_v}.")
    return v


def valid_reference(ref: object) -> List[int]:
    """Check that `ref` is a list of integers and is not empty."""
    if not isinstance(ref, Sequence) or isinstance(ref, (str, bytes)):
        raise TypeError("reference must be a list of integers.")

    out: List[int] = []
    for i, x in enumerate(ref):
        if isinstance(x, bool) or not isinstance(x, int):
            raise TypeError(f"reference[{i}] must be an integer.")
        out.append(x)

    if not out:
        raise ValueError("reference must not be empty.")
    return out


def valid_request_queue(req: object) -> List[int]:
    """Check that `req` is a list of integers and is not empty (for disk requests)."""
    if not isinstance(req, Sequence) or isinstance(req, (str, bytes)):
        raise TypeError("request queue must be a list of integers.")

    out: List[int] = []
    for i, x in enumerate(req):
        if isinstance(x, bool) or not isinstance(x, int):
            raise TypeError(f"request queue[{i}] must be an integer.")
        out.append(x)

    if not out:
        raise ValueError("request queue must not be empty.")
    return out


def valid_direction(v: object) -> str:
    """Check that `v` is either 'left' or 'right' (case‑insensitive)."""
    if not isinstance(v, str):
        raise TypeError("direction must be a string.")
    d = v.strip().lower()
    if d not in {"left", "right"}:
        raise ValueError("direction must be either 'left' or 'right'.")
    return d