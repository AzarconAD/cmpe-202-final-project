from typing import Any, Dict, List
from backend.models.process import DiskSchedulingAlgorithm, DiskResult, DiskStep

class FCFSDiskScheduling(DiskSchedulingAlgorithm):
    """First-come, first-served disk scheduling."""

    def run(self) -> DiskResult:
        cur = self.head          # current head position
        move = 0                 # total distance moved
        order: List[int] = []    # order of tracks served
        steps: List[DiskStep] = []  # detailed steps

        # Simply serve requests in the order they appear.
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
        rem = list(self.req)     # copy of remaining requests
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

        while rem:
            # Pick the request with the smallest distance from the current head.
            # If tie, take the one with the smallest index (stable).
            i, r = min(enumerate(rem), key=lambda t: (abs(t[1] - cur), t[0]))
            rem.pop(i)
            d = abs(cur - r)
            move += d
            steps.append(self._step(cur, r, move))
            order.append(r)
            cur = r

        return self._res(order, move, steps)


class SCANDiskScheduling(DiskSchedulingAlgorithm):
    """SCAN disk scheduling (elevator algorithm)."""

    def run(self) -> DiskResult:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

        # Split requests into those >= head (up) and those < head (down).
        up = sorted(r for r in self.req if r >= cur)   # ascending
        dn = sorted((r for r in self.req if r < cur), reverse=True)  # descending

        if self.dir == "right":
            # Service up requests in ascending order.
            for r in up:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r

            # Go to the end of the disk (size-1).
            if self.req and cur != self.size - 1:
                nxt = self.size - 1
                move += abs(cur - nxt)
                steps.append(self._step(cur, nxt, move))
                cur = nxt

            # Then service down requests in descending order.
            for r in dn:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r
        else:  # direction == "left"
            # Service down requests first (descending).
            for r in dn:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r

            # Go to the start of the disk (track 0).
            if self.req and cur != 0:
                nxt = 0
                move += abs(cur - nxt)
                steps.append(self._step(cur, nxt, move))
                cur = nxt

            # Then service up requests (ascending).
            for r in up:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r

        return self._res(order, move, steps)


class CSCANDiskScheduling(DiskSchedulingAlgorithm):
    """C-SCAN disk scheduling (circular SCAN)."""

    def run(self) -> DiskResult:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

        up = sorted(r for r in self.req if r >= cur)
        dn = sorted(r for r in self.req if r < cur)

        if self.dir == "right":
            # Service up requests in ascending order.
            for r in up:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r

            if dn:
                # Go to the end, then jump to track 0 (no service on the way back).
                if cur != self.size - 1:
                    nxt = self.size - 1
                    move += abs(cur - nxt)
                    steps.append(self._step(cur, nxt, move))
                    cur = nxt

                nxt = 0
                move += abs(cur - nxt)
                steps.append(self._step(cur, nxt, move))
                cur = nxt

                # Service down requests in ascending order (since we wrapped).
                for r in dn:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
                    cur = r
        else:  # direction == "left"
            # Service down requests in descending order.
            dn_desc = sorted((r for r in self.req if r < cur), reverse=True)
            up_desc = sorted((r for r in self.req if r >= cur), reverse=True)

            for r in dn_desc:
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r

            if up_desc:
                # Go to 0, then jump to the end.
                if cur != 0:
                    nxt = 0
                    move += abs(cur - nxt)
                    steps.append(self._step(cur, nxt, move))
                    cur = nxt

                nxt = self.size - 1
                move += abs(cur - nxt)
                steps.append(self._step(cur, nxt, move))
                cur = nxt

                # Service up requests in descending order.
                for r in up_desc:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
                    cur = r

        return self._res(order, move, steps)


class LOOKDiskScheduling(DiskSchedulingAlgorithm):
    """LOOK disk scheduling (SCAN without going to the end)."""

    def run(self) -> DiskResult:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

        up = sorted(r for r in self.req if r >= cur)
        dn = sorted((r for r in self.req if r < cur), reverse=True)

        # Simply concatenate the two lists depending on direction.
        seq = up + dn if self.dir == "right" else dn + up
        for r in seq:
            d = abs(cur - r)
            move += d
            steps.append(self._step(cur, r, move))
            order.append(r)
            cur = r

        return self._res(order, move, steps)


class CLOOKDiskScheduling(DiskSchedulingAlgorithm):
    """C-LOOK disk scheduling (circular LOOK)."""

    def run(self) -> DiskResult:
        cur = self.head
        move = 0
        order: List[int] = []
        steps: List[DiskStep] = []

        up = sorted(r for r in self.req if r >= cur)
        dn = sorted(r for r in self.req if r < cur)

        if self.dir == "right":
            # Service up requests in ascending order.
            if up:
                for r in up:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
                    cur = r

            # Then wrap directly to the first down request (no jump to end).
            if dn:
                r = dn[0]
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r
                # Service the remaining down requests.
                for r in dn[1:]:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
                    cur = r
        else:  # direction == "left"
            dn_desc = sorted((r for r in self.req if r < cur), reverse=True)
            up_desc = sorted((r for r in self.req if r >= cur), reverse=True)

            # Service down requests in descending order.
            if dn_desc:
                for r in dn_desc:
                    d = abs(cur - r)
                    move += d
                    steps.append(self._step(cur, r, move))
                    order.append(r)
                    cur = r

            # Wrap directly to the first up request.
            if up_desc:
                r = up_desc[0]
                d = abs(cur - r)
                move += d
                steps.append(self._step(cur, r, move))
                order.append(r)
                cur = r
                # Service remaining up requests.
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
    if algorithm not in DISK_ALGORITHMS:
        raise ValueError(f"Unknown disk algorithm: {algorithm}")
    # Create an instance of the algorithm class, run it, and convert the result to a dict.
    return DISK_ALGORITHMS[algorithm](req, head, size, dir).run().to_dict()

# Simple demo to test disk algorithms.
def _demo() -> None:
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

if __name__ == "__main__":
    _demo()