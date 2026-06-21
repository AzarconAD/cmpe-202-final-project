from typing import Any, Dict, List
from models.process import PageReplacementAlgorithm, PageResult, PageStep


class FIFOPageReplacement(PageReplacementAlgorithm):
    """First-in, first-out page replacement."""

    def run(self) -> PageResult:
        frm: List[int | None] = [None] * self.frm
        q: List[int] = []
        hit = 0
        fault = 0
        steps: List[PageStep] = []

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

    def run(self) -> PageResult:
        frm: List[int | None] = [None] * self.frm
        hit = 0
        fault = 0
        steps: List[PageStep] = []

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
                        idx = j

                rep = frm[idx]

            frm[idx] = pg
            steps.append(self._step(pg, frm, False, rep))

        return self._res(hit, fault, frm, steps)


class LRUPageReplacement(PageReplacementAlgorithm):
    """Least recently used page replacement."""

    def run(self) -> PageResult:
        frm: List[int | None] = [None] * self.frm
        last: Dict[int, int] = {}
        hit = 0
        fault = 0
        steps: List[PageStep] = []

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

    def run(self) -> PageResult:
        frm: List[int | None] = [None] * self.frm
        bit: List[int] = [0] * self.frm
        ptr = 0
        hit = 0
        fault = 0
        steps: List[PageStep] = []

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

    def run(self) -> PageResult:
        frm: List[int | None] = [None] * self.frm
        cnt: Dict[int, int] = {}
        age: Dict[int, int] = {}
        hit = 0
        fault = 0
        steps: List[PageStep] = []

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


# ============= Algorithm Router =============
PAGE_ALGORITHMS = {
    'fifo': FIFOPageReplacement,
    'optimal': OptimalPageReplacement,
    'lru': LRUPageReplacement,
    'lru_approx': LRUApproximationPageReplacement,
    'lfu': LFUPageReplacement,
}


def run_page_algorithm(algorithm: str, ref: List[int], frm: int) -> Dict[str, Any]:
    """Public entry point for Flask API. Returns a plain dict for JSON serialization."""
    if algorithm not in PAGE_ALGORITHMS:
        raise ValueError(f"Unknown page replacement algorithm: {algorithm}")
    return PAGE_ALGORITHMS[algorithm](ref, frm).run().to_dict()


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
        print(f"hit={res.hit} fault={res.fault} ratio_hit={res.ratio_hit:.2f} ratio_fault={res.ratio_fault:.2f}")
        print(f"final_frm={res.final_frm}")
        print("steps:")
        for i, st in enumerate(res.steps, 1):
            rep = st.replaced_page
            rep_txt = "None" if rep is None else str(rep)
            print(
                f"  {i:02d}. pg={st.pg} frm={st.frm} status={st.status} replaced_page={rep_txt}"
            )
        print()