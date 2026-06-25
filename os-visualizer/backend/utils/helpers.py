from typing import Any, Dict, List, Optional, Tuple
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
        if not current.is_allocated and not nxt.is_allocated and current.end == nxt.start:
            current.end = nxt.end
            current.size = current.end - current.start
            blocks.pop(i + 1)
        else:
            i += 1

def find_first_fit(blocks, size):
    for b in blocks:
        if not b.is_allocated and b.size >= size:
            return b
    return None

def find_next_fit(blocks, size, pointer):
    n = len(blocks)
    for i in range(n):
        idx = (pointer + i) % n
        b = blocks[idx]
        if not b.is_allocated and b.size >= size:
            return b, (idx + 1) % n
    return None, pointer

def find_best_fit(blocks, size):
    best = None
    best_size = float('inf')
    for b in blocks:
        if not b.is_allocated and b.size >= size and b.size < best_size:
            best = b
            best_size = b.size
    return best

def find_worst_fit(blocks, size):
    worst = None
    worst_size = -1
    for b in blocks:
        if not b.is_allocated and b.size >= size and b.size > worst_size:
            worst = b
            worst_size = b.size
    return worst

def allocate_with_algorithm(blocks: List[MemoryBlock], size: int, algorithm: str, pointer: int = 0) -> Tuple[Optional[MemoryBlock], int]:
    if algorithm == 'first_fit':
        return find_first_fit(blocks, size), pointer
    elif algorithm == 'next_fit':
        return find_next_fit(blocks, size, pointer)
    elif algorithm == 'best_fit':
        return find_best_fit(blocks, size), pointer
    elif algorithm == 'worst_fit':
        return find_worst_fit(blocks, size), pointer
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

def compact_memory(blocks: List[MemoryBlock]) -> List[MemoryBlock]:
    """Move all allocated blocks to the start, merge free space at the end."""
    allocated_blocks = [b for b in blocks if b.is_allocated]
    total_size = sum(b.size for b in blocks)
    # BUG FIX: compute next_id BEFORE mutating blocks[:], otherwise the list
    # only contains allocated blocks at that point and we may get id=0 collision
    # when all blocks happen to be free.
    next_id = max((b.id for b in blocks), default=-1) + 1
    compacted = []
    cursor = 0
    for b in allocated_blocks:
        b.start = cursor
        b.end = cursor + b.size
        cursor += b.size
        compacted.append(b)
    leftover = total_size - cursor
    if leftover > 0:
        free_block_obj = MemoryBlock(
            id=next_id,
            start=cursor,
            end=cursor + leftover,
            size=leftover,
            is_allocated=False,
            process_id=None
        )
        compacted.append(free_block_obj)
    blocks[:] = compacted
    return blocks

def release_process(blocks: List[MemoryBlock], process_id: str) -> List[MemoryBlock]:
    matching = [b for b in blocks if b.is_allocated and b.process_id == process_id]
    for b in matching:
        free_block(b, blocks)
    return blocks

def calculate_utilization_at_time(blocks: List[MemoryBlock], time: int) -> Dict[str, Any]:
    total = sum(b.size for b in blocks)
    used = sum(b.size for b in blocks if b.is_allocated)
    free = total - used
    utilization = (used / total * 100) if total else 0.0
    return {
        'time': time,
        'total_memory': total,
        'used_memory': used,
        'free_memory': free,
        'utilization_percent': round(utilization, 2)
    }

def simulate_memory_scheduling(processes: List[Dict], total_memory: int, algorithm: str, compaction: bool = False) -> Dict[str, Any]:
    blocks = [MemoryBlock(id=0, start=0, end=total_memory, size=total_memory, is_allocated=False, process_id=None)]
    procs = sorted(processes, key=lambda p: p['arrival'])
    ready_queue = []
    in_memory = {}   # pid -> remaining burst
    timeline = []
    t = 0
    idx = 0
    n = len(procs)
    pointer = 0

    # BUG FIX 3: use len() not any() — any({'P1': 0}) is False (0 is falsy),
    # so a process on its last tick would cause the loop to exit one tick early.
    while idx < n or ready_queue or len(in_memory) > 0:

        # Admit newly arrived processes
        while idx < n and procs[idx]['arrival'] <= t:
            ready_queue.append(procs[idx])
            idx += 1

        # BUG FIX 1: removed the unconditional compact_memory() call here.
        # Compaction now only fires inside the allocation loop, AFTER a specific
        # process fails to find a block — so the snapshot reflects reality.

        allocated_this_tick = []
        new_ready = []
        for proc in ready_queue:
            size = proc['memory']

            # BUG FIX 4: recalculate pointer by finding the current index of the
            # block we last allocated into, rather than trusting a stale integer
            # index that shifts whenever allocate_block() splits a block.
            block, new_pointer = allocate_with_algorithm(blocks, size, algorithm, pointer)

            # BUG FIX 1: only compact and retry if allocation actually failed
            if block is None and compaction:
                compact_memory(blocks)
                # After compaction, pointer must reset to 0 (block list rebuilt)
                block, new_pointer = allocate_with_algorithm(blocks, size, algorithm, 0)

            if block is not None:
                req = MemoryRequest(proc['pid'], size)
                allocate_block(block, req, blocks)
                in_memory[proc['pid']] = proc['burst']
                allocated_this_tick.append(proc['pid'])
                pointer = new_pointer
            else:
                new_ready.append(proc)
        ready_queue = new_ready

        # BUG FIX 2: record the snapshot BEFORE decrementing/releasing so the
        # memory map at tick t shows what was in memory DURING tick t, and the
        # finished[] list correctly labels who completed at the END of tick t.
        total_mem = sum(b.size for b in blocks)
        used = sum(b.size for b in blocks if b.is_allocated)
        util = (used / total_mem * 100) if total_mem else 0.0

        # Decrement burst for running processes and collect who finishes
        finished = []
        for pid in list(in_memory.keys()):
            in_memory[pid] -= 1
            if in_memory[pid] == 0:
                finished.append(pid)

        # Release finished processes AFTER snapshot so the map shows them as
        # still allocated during the tick they complete
        for pid in finished:
            release_process(blocks, pid)
            del in_memory[pid]

        timeline.append({
            'time': t,
            'blocks': [b.to_dict() for b in blocks],
            'utilization': round(util, 2),
            'allocated': allocated_this_tick,
            'finished': finished,
            'waiting': [p['pid'] for p in ready_queue],
            'running': list(in_memory.keys()),
        })
        t += 1

    return {
        'algorithm': algorithm,
        'compaction': compaction,
        'timeline': timeline,
        'total_memory': total_memory,
        'final_blocks': [b.to_dict() for b in blocks]
    }