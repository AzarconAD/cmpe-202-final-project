from typing import Any, Dict, List, Optional, Sequence
from backend.models.process import Process, MemoryBlock, MemoryRequest

def calculate_metrics(processes: List[Process]):
    """Calculate waiting and turnaround times"""
    for p in processes:
        p.turnaround_time = p.finish_time - p.arrival
        p.waiting_time = p.turnaround_time - p.burst

def format_gantt(gantt: List[Dict]) -> List[Dict]:
    """Merge consecutive same-PID entries"""
    merged = []
    for entry in gantt:
        if merged and merged[-1]['pid'] == entry['pid']:
            merged[-1]['end'] = entry['end']
        else:
            merged.append(entry)
    return merged

def build_result(algorithm: str, gantt, procs) -> Dict[str, Any]:
    """Standardize JSON output for all algorithms"""
    return {
        'algorithm': algorithm,
        'gantt': format_gantt(gantt),
        'processes': [p.to_dict() for p in procs],
        'avg_waiting': sum(p.waiting_time for p in procs) / len(procs),
        'avg_turnaround': sum(p.turnaround_time for p in procs) / len(procs),
    }

def build_memory_result(algorithm: str, blocks: List[MemoryBlock], requests: List[MemoryRequest]) -> Dict[str, Any]:
    """Standardize memory allocation output"""
    total = sum(b.size for b in blocks)
    return {
        'algorithm': algorithm,
        'blocks': [b.to_dict() for b in blocks],
        'requests': [
            {
                'process_id': r.process_id,
                'size': r.size,
                'allocated_block': r.allocated_block,
                'status': 'allocated' if r.allocated_block is not None else 'waiting'
            }
            for r in requests
        ],
        'total_memory': total,
        'used_memory': sum(b.size for b in blocks if b.is_allocated),
        'free_memory': sum(b.size for b in blocks if not b.is_allocated),
        'memory_utilization': (sum(b.size for b in blocks if b.is_allocated) / total * 100) if total else 0
    }

def initialize_memory(block_sizes: List[int]) -> List[MemoryBlock]:
    """Create memory blocks from list of sizes"""
    blocks = []
    start = 0
    for i, size in enumerate(block_sizes):
        blocks.append(MemoryBlock(
            id=i,
            start=start,
            end=start + size,
            size=size,
            is_allocated=False,
            process_id=None
        ))
        start += size
    return blocks

def allocate_block(block: MemoryBlock, request: MemoryRequest, blocks: List[MemoryBlock]):
    """
    Allocate a block to a request. If the block is larger than the
    request, split off the unused remainder as a new free block
    immediately after it.
    """
    if block.size > request.size:
        next_id = max((b.id for b in blocks), default=-1) + 1
        remainder = MemoryBlock(
            id=next_id,
            start=block.start + request.size,
            end=block.end,
            size=block.size - request.size,
            is_allocated=False,
            process_id=None
        )
        block.end = block.start + request.size
        block.size = request.size
        blocks.insert(blocks.index(block) + 1, remainder)
    block.is_allocated = True
    block.process_id = request.process_id
    request.allocated_block = block.id
    return block

def free_block(block: MemoryBlock, blocks: List[MemoryBlock]):
    """Free an allocated block, then coalesce with adjacent free blocks."""
    block.is_allocated = False
    block.process_id = None
    coalesce_free_blocks(blocks)

def coalesce_free_blocks(blocks: List[MemoryBlock]):
    """Merge adjacent free blocks so freed memory can satisfy bigger future requests."""
    blocks.sort(key=lambda b: b.start)
    i = 0
    while i < len(blocks) - 1:
        current = blocks[i]
        nxt = blocks[i + 1]
        if current.is_allocated and nxt.is_allocated and current.end == nxt.start:
            current.end = nxt.end
            current.size = current.end - current.start
            blocks.pop(i + 1)
        else:
            i += 1
