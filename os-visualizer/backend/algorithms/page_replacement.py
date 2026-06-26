from typing import Any, Dict, List
from backend.models.process import PageReplacementAlgorithm, PageResult, PageStep

# Each replacement class inherits from PageReplacementAlgorithm, which gives
# common methods: _step (record one step) and _res (build final result).

class FIFOPageReplacement(PageReplacementAlgorithm):
    """First-in, first-out page replacement."""

    def run(self) -> PageResult:
        frm: List[int | None] = [None] * self.frm   # frame contents (None = empty)
        q: List[int] = []                           # queue of frame indices (for FIFO)
        hit = 0
        fault = 0
        steps: List[PageStep] = []

        for pg in self.ref:
            # If the page is already in a frame → hit.
            if pg in frm:
                hit += 1
                steps.append(self._step(pg, frm, True))
                continue

            fault += 1
            rep: int | None = None

            # If there is an empty frame, use it.
            if None in frm:
                idx = frm.index(None)
            else:
                # Otherwise, evict the oldest page (the one at the front of the queue).
                idx = q.pop(0)
                rep = frm[idx]

            frm[idx] = pg
            q.append(idx)    # remember the order of pages (FIFO)
            steps.append(self._step(pg, frm, False, rep))

        return self._res(hit, fault, frm, steps)


class OptimalPageReplacement(PageReplacementAlgorithm):
    """Optimal page replacement (clairvoyant)."""

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
                # Find the page whose next use is farthest in the future (or never used again).
                best_n = -1
                idx = 0
                for j, cur in enumerate(frm):
                    assert cur is not None
                    try:
                        nxt = self.ref.index(cur, i + 1)   # next occurrence after i
                    except ValueError:
                        nxt = len(self.ref) + 1            # never used again → far future
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
        last: Dict[int, int] = {}   # frame index -> last used time (i)
        hit = 0
        fault = 0
        steps: List[PageStep] = []

        for i, pg in enumerate(self.ref):
            if pg in frm:
                hit += 1
                last[frm.index(pg)] = i   # update last used time
                steps.append(self._step(pg, frm, True))
                continue

            fault += 1
            rep: int | None = None

            if None in frm:
                idx = frm.index(None)
            else:
                # Find the frame that was used least recently (smallest last time).
                # We include the frame index as a tie‑breaker.
                idx = min((j for j, x in enumerate(frm) if x is not None),
                          key=lambda j: (last.get(j, -1), j))
                rep = frm[idx]

            frm[idx] = pg
            last[idx] = i
            steps.append(self._step(pg, frm, False, rep))

        return self._res(hit, fault, frm, steps)


class LRUApproximationPageReplacement(PageReplacementAlgorithm):
    """Second-chance / clock page replacement (LRU approximation)."""

    def run(self) -> PageResult:
        frm: List[int | None] = [None] * self.frm
        bit: List[int] = [0] * self.frm   # reference bits (1 = recently used)
        ptr = 0                           # clock hand
        hit = 0
        fault = 0
        steps: List[PageStep] = []

        for pg in self.ref:
            if pg in frm:
                hit += 1
                bit[frm.index(pg)] = 1   # mark as recently used
                steps.append(self._step(pg, frm, True))
                continue

            fault += 1
            rep: int | None = None

            if None in frm:
                idx = frm.index(None)
                frm[idx] = pg
                bit[idx] = 1
            else:
                # Advance the clock hand until we find a frame with bit == 0.
                while bit[ptr] == 1:
                    bit[ptr] = 0       # give a second chance
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
        cnt: Dict[int, int] = {}   # frame index -> frequency count
        age: Dict[int, int] = {}   # frame index -> time of first insertion (for tie‑breaking)
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
                # Find the frame with the lowest frequency; if tie, use age (older first).
                idx = min((j for j, x in enumerate(frm) if x is not None),
                          key=lambda j: (cnt.get(j, 0), age.get(j, 0), j))
                rep = frm[idx]

            frm[idx] = pg
            cnt[idx] = 1          # reset frequency
            age[idx] = i          # remember when it was inserted
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
    if algorithm not in PAGE_ALGORITHMS:
        raise ValueError(f"Unknown page replacement algorithm: {algorithm}")
    return PAGE_ALGORITHMS[algorithm](ref, frm).run().to_dict()

# Simple demo for page replacement algorithms.
def _demo() -> None:
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