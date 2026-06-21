from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    priority: Optional[int] = None
    remaining: Optional[int] = None
    start_time: Optional[int] = None
    finish_time: Optional[int] = None
    waiting_time: Optional[int] = None
    turnaround_time: Optional[int] = None
    queue: Optional[str] = None
    memory_required: Optional[int] = None
    memory_start: Optional[int] = None
    memory_end: Optional[int] = None

    def to_dict(self):
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


@dataclass
class MemoryBlock:
    """Represents a memory block/hole"""
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
    """Represents a process requesting memory"""
    process_id: str
    size: int
    allocated_block: Optional[int] = None
    allocated_time: Optional[int] = None