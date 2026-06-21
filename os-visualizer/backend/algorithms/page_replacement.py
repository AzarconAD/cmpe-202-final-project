"""Page replacement algorithms for an operating systems simulator."""

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


def _v_ref(ref: object) -> List[int]:
    """Validate the reference string."""

    if not isinstance(ref, Sequence) or isinstance(ref, (str, bytes)):
        raise TypeError("ref must be a list of integers.")

    out: List[int] = []
    for i, x in enumerate(ref):
        if isinstance(x, bool) or not isinstance(x, int):
            raise TypeError(f"ref[{i}] must be an integer.")
        out.append(x)

    if not out:
        raise ValueError("ref must not be empty.")

    return out


class PageReplacementAlgorithm(ABC):
    """Abstract base class for page replacement algorithms."""

    def __init__(self, ref: Sequence[int], frm: int) -> None:
        self.ref = _v_ref(ref)
        self.frm = _v_int(frm, "frm", 1)

    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """Run the simulation and return a result dictionary."""

    def _step(
        self,
        pg: int,
        frames: Sequence[int | None],
        hit: bool,
        replaced_page: int | None = None,
    ) -> Dict[str, Any]:
        """Build a single simulation step."""

        return {
            "pg": pg,
            "frm": [x for x in frames if x is not None],
            "status": "Hit" if hit else "Fault",
            "replaced_page": replaced_page,
        }

    def _res(
        self,
        hit: int,
        fault: int,
        frames: Sequence[int | None],
        steps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build the shared result dictionary."""

        tot = hit + fault
        return {
            "hit": hit,
            "fault": fault,
            "ratio_hit": hit / tot if tot else 0.0,
            "ratio_fault": fault / tot if tot else 0.0,
            "final_frm": [x for x in frames if x is not None],
            "steps": steps,
        }


class FIFOPageReplacement(PageReplacementAlgorithm):
    """First-in, first-out page replacement."""

    def run(self) -> Dict[str, Any]:
        frm: List[int | None] = [None] * self.frm
        q: List[int] = []
        hit = 0
        fault = 0
        steps: List[Dict[str, Any]] = []

        for pg in self.ref:
            # Check whether the page is already loaded.
            if pg in frm:
                hit += 1
                steps.append(self._step(pg, frm, True))
                continue

            fault += 1
            rep: int | None = None

            # Fill an empty frame first, then evict the oldest loaded page.
            if None in frm:
                idx = frm.index(None)
            else:
                idx = q.pop(0)
                rep = frm[idx]

            frm[idx] = pg
            q.append(idx)
            steps.append(self._step(pg, frm, False, rep))

        return self._res(hit, fault, frm, steps)


class OptimalPageReplacement(PageReplacementAlgorithm):
    """Optimal page replacement."""

    def run(self) -> Dict[str, Any]:
        frm: List[int | None] = [None] * self.frm
        hit = 0
        fault = 0
        steps: List[Dict[str, Any]] = []

        for i, pg in enumerate(self.ref):
            if pg in frm:
                hit += 1
                steps.append(self._step(pg, frm, True))
                continue

            fault += 1
            rep: int | None = None

            if None in frm:
                idx = frm.index(None)
            else:
                best_i = -1
                best_n = -1
                idx = 0

                for j, cur in enumerate(frm):
                    assert cur is not None
                    try:
                        nxt = self.ref.index(cur, i + 1)
                    except ValueError:
                        nxt = len(self.ref) + 1

                    if nxt > best_n:
                        best_n = nxt
                        best_i = j

                idx = best_i
                rep = frm[idx]

            frm[idx] = pg
            steps.append(self._step(pg, frm, False, rep))

        return self._res(hit, fault, frm, steps)


class LRUPageReplacement(PageReplacementAlgorithm):
    """Least recently used page replacement."""

    def run(self) -> Dict[str, Any]:
        frm: List[int | None] = [None] * self.frm
        last: Dict[int, int] = {}
        hit = 0
        fault = 0
        steps: List[Dict[str, Any]] = []

        for i, pg in enumerate(self.ref):
            if pg in frm:
                hit += 1
                last[frm.index(pg)] = i
                steps.append(self._step(pg, frm, True))
                continue

            fault += 1
            rep: int | None = None

            if None in frm:
                idx = frm.index(None)
            else:
                idx = min((j for j, x in enumerate(frm) if x is not None), key=lambda j: (last.get(j, -1), j))
                rep = frm[idx]

            frm[idx] = pg
            last[idx] = i
            steps.append(self._step(pg, frm, False, rep))

        return self._res(hit, fault, frm, steps)


class LRUApproximationPageReplacement(PageReplacementAlgorithm):
    """Second-chance / clock page replacement."""

    def run(self) -> Dict[str, Any]:
        frm: List[int | None] = [None] * self.frm
        bit: List[int] = [0] * self.frm
        ptr = 0
        hit = 0
        fault = 0
        steps: List[Dict[str, Any]] = []

        for pg in self.ref:
            if pg in frm:
                hit += 1
                bit[frm.index(pg)] = 1
                steps.append(self._step(pg, frm, True))
                continue

            fault += 1
            rep: int | None = None

            if None in frm:
                idx = frm.index(None)
                frm[idx] = pg
                bit[idx] = 1
            else:
                while bit[ptr] == 1:
                    bit[ptr] = 0
                    ptr = (ptr + 1) % self.frm

                idx = ptr
                rep = frm[idx]
                frm[idx] = pg
                bit[idx] = 1
                ptr = (ptr + 1) % self.frm

            steps.append(self._step(pg, frm, False, rep))

        return self._res(hit, fault, frm, steps)


class LFUPageReplacement(PageReplacementAlgorithm):
    """Least frequently used page replacement."""

    def run(self) -> Dict[str, Any]:
        frm: List[int | None] = [None] * self.frm
        cnt: Dict[int, int] = {}
        age: Dict[int, int] = {}
        hit = 0
        fault = 0
        steps: List[Dict[str, Any]] = []

        for i, pg in enumerate(self.ref):
            if pg in frm:
                hit += 1
                idx = frm.index(pg)
                cnt[idx] = cnt.get(idx, 0) + 1
                steps.append(self._step(pg, frm, True))
                continue

            fault += 1
            rep: int | None = None

            if None in frm:
                idx = frm.index(None)
            else:
                idx = min(
                    (j for j, x in enumerate(frm) if x is not None),
                    key=lambda j: (cnt.get(j, 0), age.get(j, 0), j),
                )
                rep = frm[idx]

            frm[idx] = pg
            cnt[idx] = 1
            age[idx] = i
            steps.append(self._step(pg, frm, False, rep))

        return self._res(hit, fault, frm, steps)


def _demo() -> None:
    """Print a readable CLI demo for direct module execution."""

    ref = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2]
    frm = 3
    algs = [
        FIFOPageReplacement(ref, frm),
        OptimalPageReplacement(ref, frm),
        LRUPageReplacement(ref, frm),
        LRUApproximationPageReplacement(ref, frm),
        LFUPageReplacement(ref, frm),
    ]

    print("PAGE REPLACEMENT DEMO")
    print(f"ref = {ref}")
    print(f"frm = {frm}")
    print()

    for alg in algs:
        res = alg.run()
        print(f"[{alg.__class__.__name__}]")
        print(f"hit={res['hit']} fault={res['fault']} ratio_hit={res['ratio_hit']:.2f} ratio_fault={res['ratio_fault']:.2f}")
        print(f"final_frm={res['final_frm']}")
        print("steps:")
        for i, st in enumerate(res["steps"], 1):
            rep = st["replaced_page"]
            rep_txt = "None" if rep is None else str(rep)
            print(
                f"  {i:02d}. pg={st['pg']} frm={st['frm']} status={st['status']} replaced_page={rep_txt}"
            )
        print()


if __name__ == "__main__":
    _demo()