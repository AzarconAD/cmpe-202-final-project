from typing import Any, Dict, List
from backend.models.process import DiskSchedulingAlgorithm, DiskResult, DiskStep


class FCFSDiskScheduling(DiskSchedulingAlgorithm):
    """First-come, first-served disk scheduling."""

    def run(self) -> DiskResult:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

        for r in self.req:
            d = abs(cur - r)
            move += d
            steps.append(self._step(cur, r, move))
            order.append(r)
            cur = r

        return self._res(order, move, steps)


class SSTFDiskScheduling(DiskSchedulingAlgorithm):
    """Shortest seek time first disk scheduling."""

    def run(self) -> DiskResult:
        rem = list(self.req)
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

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

    def run(self) -> DiskResult:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

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

    def run(self) -> DiskResult:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

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
                    cur = r
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

    def run(self) -> DiskResult:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

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

    def run(self) -> DiskResult:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

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


# ============= Algorithm Router =============
DISK_ALGORITHMS = {
    'fcfs': FCFSDiskScheduling,
    'sstf': SSTFDiskScheduling,
    'scan': SCANDiskScheduling,
    'cscan': CSCANDiskScheduling,
    'look': LOOKDiskScheduling,
    'clook': CLOOKDiskScheduling,
}


def run_disk_algorithm(algorithm: str, req: List[int], head: int, size: int, dir: str) -> Dict[str, Any]:
    """Public entry point for Flask API. Returns a plain dict for JSON serialization."""
    if algorithm not in DISK_ALGORITHMS:
        raise ValueError(f"Unknown disk algorithm: {algorithm}")
    return DISK_ALGORITHMS[algorithm](req, head, size, dir).run().to_dict()


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
        print(f"order={res.order}")
        print(f"move={res.move} avg={res.avg:.2f}")
        print("steps:")
        for i, st in enumerate(res.steps, 1):
            print(
                f"  {i:02d}. from={st.from_} to={st.to} dist={st.dist} cum_move={st.cum_move}"
            )
        print()