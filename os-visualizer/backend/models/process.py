from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence
from backend.utils.validators import valid_int, valid_request_queue, valid_direction, valid_reference

# ============================================================
# CPU Scheduling: Process dataclass
# ============================================================
@dataclass
class Process:
    """Represents a process for CPU scheduling."""
    pid: str
    arrival: int
    burst: int
    priority: Optional[int] = None
    remaining: Optional[int] = None
    start_time: Optional[int] = None
    finish_time: Optional[int] = None
    waiting_time: Optional[int] = None
    turnaround_time: Optional[int] = None
    queue: Optional[str] = None          # 'system' or 'user' for MLQ
    memory_required: Optional[int] = None
    memory_start: Optional[int] = None
    memory_end: Optional[int] = None

    def to_dict(self):
        """Convert the process object to a dictionary (JSON‑friendly)."""
        return {
            'pid': self.pid,
            'arrival': self.arrival,
            'burst': self.burst,
            'priority': self.priority,
            'remaining': self.remaining,
            'start_time': self.start_time,
            'finish_time': self.finish_time,
            'waiting_time': self.waiting_time,
            'turnaround_time': self.turnaround_time,
            'memory_required': self.memory_required,
            'memory_start': self.memory_start,
            'memory_end': self.memory_end,
            'queue': self.queue
        }


# ============================================================
# Memory Management: Block and Request dataclasses
# ============================================================
@dataclass
class MemoryBlock:
    """A contiguous chunk of memory – can be free or allocated to a process."""
    id: int
    start: int
    end: int
    size: int
    is_allocated: bool = False
    process_id: Optional[str] = None

    def to_dict(self):
        return {
            'id': self.id,
            'start': self.start,
            'end': self.end,
            'size': self.size,
            'is_allocated': self.is_allocated,
            'process_id': self.process_id
        }


@dataclass
class MemoryRequest:
    """A request from a process to allocate a certain amount of memory."""
    process_id: str
    size: int
    allocated_block: Optional[int] = None
    allocated_time: Optional[int] = None


# ============================================================
# Page Replacement: Step and Result dataclasses + Abstract Base
# ============================================================
@dataclass
class PageStep:
    """One step in a page replacement trace: which page, frame contents, hit/fault."""
    pg: int
    frm: List[int]
    status: str          # "Hit" or "Fault"
    replaced_page: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pg": self.pg,
            "frm": self.frm,
            "status": self.status,
            "replaced_page": self.replaced_page,
        }


@dataclass
class PageResult:
    """Final result of a page replacement algorithm."""
    hit: int
    fault: int
    ratio_hit: float
    ratio_fault: float
    final_frm: List[int]
    steps: List[PageStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hit": self.hit,
            "fault": self.fault,
            "ratio_hit": self.ratio_hit,
            "ratio_fault": self.ratio_fault,
            "final_frm": self.final_frm,
            "steps": [s.to_dict() for s in self.steps],
        }


class PageReplacementAlgorithm(ABC):
    """Base class for all page replacement algorithms (FIFO, LRU, etc.)."""

    def __init__(self, ref: Sequence[int], frm: int) -> None:
        # Validate the reference string and the number of frames.
        self.ref = valid_reference(ref)
        self.frm = valid_int(frm, "frm", 1)

    @abstractmethod
    def run(self) -> PageResult:
        """Run the simulation – must be implemented by each subclass."""
        pass

    def _step(self, pg: int, frames: Sequence[int | None], hit: bool,
              replaced_page: int | None = None) -> PageStep:
        """Build one step of the trace (called inside run())."""
        return PageStep(
            pg=pg,
            frm=[x for x in frames if x is not None],
            status="Hit" if hit else "Fault",
            replaced_page=replaced_page,
        )

    def _res(self, hit: int, fault: int, frames: Sequence[int | None],
             steps: List[PageStep]) -> PageResult:
        """Build the final result (called at the end of run())."""
        tot = hit + fault
        return PageResult(
            hit=hit,
            fault=fault,
            ratio_hit=hit / tot if tot else 0.0,
            ratio_fault=fault / tot if tot else 0.0,
            final_frm=[x for x in frames if x is not None],
            steps=steps,
        )


# ============================================================
# Disk Scheduling: Step and Result dataclasses + Abstract Base
# ============================================================
@dataclass
class DiskStep:
    """One head movement step in a disk scheduling trace."""
    from_: int
    to: int
    dist: int
    cum_move: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_,
            "to": self.to,
            "dist": self.dist,
            "cum_move": self.cum_move,
        }


@dataclass
class DiskResult:
    """Final result of a disk scheduling algorithm."""
    order: List[int]
    move: int
    avg: float
    steps: List[DiskStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "move": self.move,
            "avg": self.avg,
            "steps": [s.to_dict() for s in self.steps],
        }


class DiskSchedulingAlgorithm(ABC):
    """Base class for disk scheduling algorithms (FCFS, SSTF, etc.)."""

    def __init__(self, req: Sequence[int], head: int, size: int, dir: str) -> None:
        # Validate inputs.
        self.req = valid_request_queue(req)
        self.head = valid_int(head, "head", 0)
        self.size = valid_int(size, "size", 1)
        self.dir = valid_direction(dir)

        if self.head >= self.size:
            raise ValueError("head must be smaller than size.")

        for i, x in enumerate(self.req):
            if x < 0 or x >= self.size:
                raise ValueError(f"req[{i}] must be within 0 and {self.size - 1}.")

    @abstractmethod
    def run(self) -> DiskResult:
        """Run the simulation – must be implemented by each subclass."""
        pass

    def _step(self, a: int, b: int, c: int) -> DiskStep:
        """Build one movement step (called inside run())."""
        return DiskStep(from_=a, to=b, dist=abs(b - a), cum_move=c)

    def _res(self, order: List[int], move: int, steps: List[DiskStep]) -> DiskResult:
        """Build the final result (called at the end of run())."""
        return DiskResult(
            order=order,
            move=move,
            avg=move / len(self.req) if self.req else 0.0,
            steps=steps,
        )