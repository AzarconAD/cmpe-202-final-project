from dataclasses import dataclass
from typing import Optional

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
            'turnaround_time': self.turnaround_time
        }