"""Disk scheduling algorithms for an operating systems simulator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Sequence


def _v_int(v: object, n: str, min_v: int | None = None) -> int:
    """Validate an integer value."""

    if isinstance(v, bool) or not isinstance(v, int):
        raise TypeError(f"{n} must be an integer.")
    if min_v is not None and v < min_v:
        raise ValueError(f"{n} must be >= {min_v}.")
    return v


def _v_req(req: object) -> List[int]:
    """Validate the request queue."""

    if not isinstance(req, Sequence) or isinstance(req, (str, bytes)):
        raise TypeError("req must be a list of integers.")

    out: List[int] = []
    for i, x in enumerate(req):
        if isinstance(x, bool) or not isinstance(x, int):
            raise TypeError(f"req[{i}] must be an integer.")
        out.append(x)

    if not out:
        raise ValueError("req must not be empty.")

    return out


def _v_dir(v: object) -> str:
    """Validate the direction."""

    if not isinstance(v, str):
        raise TypeError("dir must be a string.")
    d = v.strip().lower()
    if d not in {"left", "right"}:
        raise ValueError("dir must be either 'left' or 'right'.")
    return d


class DiskSchedulingAlgorithm(ABC):
    """Abstract base class for disk scheduling algorithms."""

    def __init__(self, req: Sequence[int], head: int, size: int, dir: str) -> None:
        self.req = _v_req(req)
        self.head = _v_int(head, "head", 0)
        self.size = _v_int(size, "size", 1)
        self.dir = _v_dir(dir)

        if self.head >= self.size:
            raise ValueError("head must be smaller than size.")

        for i, x in enumerate(self.req):
            if x < 0 or x >= self.size:
                raise ValueError(f"req[{i}] must be within 0 and {self.size - 1}.")

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """Run the simulation and return a result dictionary."""

    def _step(self, a: int, b: int, c: int) -> Dict[str, Any]:
        """Build one movement step."""

        return {"from": a, "to": b, "dist": abs(b - a), "cum_move": c}

    def _res(self, order: List[int], move: int, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build the shared result dictionary."""

        return {
            "order": order,
            "move": move,
            "avg": move / len(self.req) if self.req else 0.0,
            "steps": steps,
        }


class FCFSDiskScheduling(DiskSchedulingAlgorithm):
    """First-come, first-served disk scheduling."""

    def run(self) -> Dict[str, Any]:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[Dict[str, Any]] = []

        for r in self.req:
            d = abs(cur - r)
            move += d
            steps.append(self._step(cur, r, move))
            order.append(r)
            cur = r

        return self._res(order, move, steps)


class SSTFDiskScheduling(DiskSchedulingAlgorithm):
    """Shortest seek time first disk scheduling."""

    def run(self) -> Dict[str, Any]:
        rem = list(self.req)
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[Dict[str, Any]] = []

        while rem:
            i, r = min(enumerate(rem), key=lambda t: (abs(t[1] - cur), t[0]))
            rem.pop(i)
            d = abs(cur - r)
            move += d
            steps.append(self._step(cur, r, move))
            order.append(r)
            cur = r

        return self._res(order, move, steps)


class SCANDiskScheduling(DiskSchedulingAlgorithm):
    """SCAN disk scheduling."""

    def run(self) -> Dict[str, Any]:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[Dict[str, Any]] = []

        up = sorted(r for r in self.req if r >= cur)
        dn = sorted((r for r in self.req if r < cur), reverse=True)

        if self.dir == "right":
            for r in up:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r

            if self.req and cur != self.size - 1:
                nxt = self.size - 1
                move += abs(cur - nxt)
                steps.append(self._step(cur, nxt, move))
                cur = nxt

            for r in dn:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r
        else:
            for r in dn:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r

            if self.req and cur != 0:
                nxt = 0
                move += abs(cur - nxt)
                steps.append(self._step(cur, nxt, move))
                cur = nxt

            for r in up:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r

        return self._res(order, move, steps)


class CSCANDiskScheduling(DiskSchedulingAlgorithm):
    """C-SCAN disk scheduling."""

    def run(self) -> Dict[str, Any]:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[Dict[str, Any]] = []

        up = sorted(r for r in self.req if r >= cur)
        dn = sorted(r for r in self.req if r < cur)

        if self.dir == "right":
            for r in up:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r

            if dn:
                if cur != self.size - 1:
                    nxt = self.size - 1
                    move += abs(cur - nxt)
                    steps.append(self._step(cur, nxt, move))
                    cur = nxt

                nxt = 0
                move += abs(cur - nxt)
                steps.append(self._step(cur, nxt, move))
                cur = nxt

                for r in dn:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
        else:
            dn_desc = sorted((r for r in self.req if r < cur), reverse=True)
            up_desc = sorted((r for r in self.req if r >= cur), reverse=True)

            for r in dn_desc:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r

            if up_desc:
                if cur != 0:
                    nxt = 0
                    move += abs(cur - nxt)
                    steps.append(self._step(cur, nxt, move))
                    cur = nxt

                nxt = self.size - 1
                move += abs(cur - nxt)
                steps.append(self._step(cur, nxt, move))
                cur = nxt

                for r in up_desc:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
                    cur = r

        return self._res(order, move, steps)

class LOOKDiskScheduling(DiskSchedulingAlgorithm):
    """LOOK disk scheduling."""

    def run(self) -> Dict[str, Any]:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[Dict[str, Any]] = []

        up = sorted(r for r in self.req if r >= cur)
        dn = sorted((r for r in self.req if r < cur), reverse=True)

        seq = up + dn if self.dir == "right" else dn + up
        for r in seq:
            d = abs(cur - r)
            move += d
            steps.append(self._step(cur, r, move))
            order.append(r)
            cur = r

        return self._res(order, move, steps)


class CLOOKDiskScheduling(DiskSchedulingAlgorithm):
    """C-LOOK disk scheduling."""

    def run(self) -> Dict[str, Any]:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[Dict[str, Any]] = []

        up = sorted(r for r in self.req if r >= cur)
        dn = sorted(r for r in self.req if r < cur)

        if self.dir == "right":
            if up:
                for r in up:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
                    cur = r
            if dn:
                r = dn[0]
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r
                for r in dn[1:]:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
                    cur = r
        else:
            dn_desc = sorted((r for r in self.req if r < cur), reverse=True)
            up_desc = sorted((r for r in self.req if r >= cur), reverse=True)

            if dn_desc:
                for r in dn_desc:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
                    cur = r
            if up_desc:
                r = up_desc[0]
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r
                for r in up_desc[1:]:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
                    cur = r

        return self._res(order, move, steps)


def _demo() -> None:
    """Print a readable CLI demo for direct module execution."""

    req = [98, 183, 37, 122, 14, 124, 65, 67]
    head = 53
    size = 200
    dir = "right"
    algs = [
        FCFSDiskScheduling(req, head, size, dir),
        SSTFDiskScheduling(req, head, size, dir),
        SCANDiskScheduling(req, head, size, dir),
        CSCANDiskScheduling(req, head, size, dir),
        LOOKDiskScheduling(req, head, size, dir),
        CLOOKDiskScheduling(req, head, size, dir),
    ]

    print("DISK SCHEDULING DEMO")
    print(f"req = {req}")
    print(f"head = {head}  size = {size}  dir = {dir}")
    print()

    for alg in algs:
        res = alg.run()
        print(f"[{alg.__class__.__name__}]")
        print(f"order={res['order']}")
        print(f"move={res['move']} avg={res['avg']:.2f}")
        print("steps:")
        for i, st in enumerate(res["steps"], 1):
            print(
                f"  {i:02d}. from={st['from']} to={st['to']} dist={st['dist']} cum_move={st['cum_move']}"
            )
        print()


if __name__ == "__main__":
    _demo()