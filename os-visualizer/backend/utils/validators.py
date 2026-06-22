from typing import List, Sequence


def valid_int(v: object, n: str, min_v: int | None = None) -> int:
    if isinstance(v, bool) or not isinstance(v, int):
        raise TypeError(f"{n} must be an integer.")
    if min_v is not None and v < min_v:
        raise ValueError(f"{n} must be >= {min_v}.")
    return v


def valid_reference(ref: object) -> List[int]:
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
    """Validate the request queue."""

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
    """Validate the direction."""

    if not isinstance(v, str):
        raise TypeError("direction must be a string.")
    d = v.strip().lower()
    if d not in {"left", "right"}:
        raise ValueError("direction must be either 'left' or 'right'.")
    return d