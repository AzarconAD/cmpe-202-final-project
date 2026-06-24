from typing import List, Dict, Any, Optional

from backend.models.process import MemoryRequest, MemoryBlock
from backend.utils.helpers import (
    initialize_memory, allocate_block, free_block,
    build_memory_result, find_first_fit, find_next_fit,
    find_best_fit, find_worst_fit
)

# ============= FIRST FIT =============
def first_fit(block_sizes: List[int], requests: List[Dict], time: Optional[int] = None) -> Dict[str, Any]:
    """
    First Fit: Allocate the first block that is large enough.

    Algorithm:
    1. Always start scanning from the BEGINNING of memory (block index 0),
       regardless of where the previous allocation happened.
    2. Find the first free block whose size is >= the request size.
    3. Allocate into that block if found; otherwise the request waits.

    The `time` parameter is optional and is only used to report memory
    utilization at a specific simulation timestamp (see
    calculate_utilization_at_time) - it does not affect the allocation
    decision itself.
    """
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []

    for req in memory_requests:
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }

        block = find_first_fit(blocks, req.size)
        if block is not None:
            allocate_block(block, req, blocks)
            step['block_id'] = block.id
        else:
            step['action'] = 'waiting'

        step_history.append(step)

    result = build_memory_result('First Fit', blocks, memory_requests)
    result['steps'] = step_history
    if time is not None:
        result['utilization_at_time'] = calculate_utilization_at_time(blocks, time)
    return result


# ============= NEXT FIT =============
def next_fit(block_sizes: List[int], requests: List[Dict], time: Optional[int] = None) -> Dict[str, Any]:
    """
    Next Fit: Like First Fit, but resumes scanning from where the LAST
    allocation left off instead of restarting from block index 0 every time.

    Algorithm:
    1. Keep a rotating pointer at the block index where the previous
       allocation succeeded (starts at 0).
    2. Scan forward from that pointer, wrapping around to the start of the
       block list if the end is reached, looking for the first free block
       that fits.
    3. Allocate into that block if found, and move the pointer to sit right
       after it for the next request; otherwise the request waits and the
       pointer does not move.
    """
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []
    pointer = 0

    for req in memory_requests:
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }

        block, pointer = find_next_fit(blocks, req.size, pointer)
        if block is not None:
            allocate_block(block, req, blocks)
            step['block_id'] = block.id
        else:
            step['action'] = 'waiting'

        step_history.append(step)

    result = build_memory_result('Next Fit', blocks, memory_requests)
    result['steps'] = step_history
    if time is not None:
        result['utilization_at_time'] = calculate_utilization_at_time(blocks, time)
    return result


# ============= BEST FIT =============
def best_fit(block_sizes: List[int], requests: List[Dict], time: Optional[int] = None) -> Dict[str, Any]:
    """
    Best Fit: Allocate the smallest free block that is large enough.

    Algorithm:
    1. Find every free block that fits the request (size >= request size).
    2. Among those, choose the block with the SMALLEST size, so the least
       space is wasted on this single allocation.
    3. Allocate into that block if found; otherwise the request waits.
    """
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []

    for req in memory_requests:
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }

        block = find_best_fit(blocks, req.size)
        if block is not None:
            allocate_block(block, req, blocks)
            step['block_id'] = block.id
        else:
            step['action'] = 'waiting'

        step_history.append(step)

    result = build_memory_result('Best Fit', blocks, memory_requests)
    result['steps'] = step_history
    if time is not None:
        result['utilization_at_time'] = calculate_utilization_at_time(blocks, time)
    return result


# ============= WORST FIT =============
def worst_fit(block_sizes: List[int], requests: List[Dict], time: Optional[int] = None) -> Dict[str, Any]:
    """
    Worst Fit: Allocate the largest free block that is large enough.

    Algorithm:
    1. Find every free block that fits the request (size >= request size).
    2. Among those, choose the block with the LARGEST size, so the leftover
       remainder stays as big - and as reusable - as possible.
    3. Allocate into that block if found; otherwise the request waits.
    """
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []

    for req in memory_requests:
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }

        block = find_worst_fit(blocks, req.size)
        if block is not None:
            allocate_block(block, req, blocks)
            step['block_id'] = block.id
        else:
            step['action'] = 'waiting'

        step_history.append(step)

    result = build_memory_result('Worst Fit', blocks, memory_requests)
    result['steps'] = step_history
    if time is not None:
        result['utilization_at_time'] = calculate_utilization_at_time(blocks, time)
    return result


# ============= BEST AVAILABLE FIT =============
def best_available_fit(block_sizes: List[int], requests: List[Dict], min_fragment_size: int = 2, time: Optional[int] = None) -> Dict[str, Any]:
    """
    Best Available Fit: a variation of Best Fit that also considers
    fragmentation, instead of always chasing the absolute tightest fit.

    Algorithm:
    1. Like Best Fit, find every free block that fits, sorted by remaining
       leftover space after the allocation (smallest leftover first).
    2. If the tightest fit would leave a leftover smaller than
       `min_fragment_size` (a sliver too small to ever be useful again),
       skip it and use the next-best fitting block instead, as long as
       that block's leftover meets the minimum.
    3. Allocate into the chosen block if found; otherwise the request waits.
    """
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []
    MIN_FRAGMENT_SIZE = min_fragment_size

    for req in memory_requests:
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }

        fitting_blocks = []
        for block in blocks:
            if not block.is_allocated and block.size >= req.size:
                remaining = block.size - req.size
                fitting_blocks.append({'block': block, 'remaining': remaining})

        if fitting_blocks:
            fitting_blocks.sort(key=lambda x: x['remaining'])

            chosen = fitting_blocks[0]
            if chosen['remaining'] < MIN_FRAGMENT_SIZE and len(fitting_blocks) > 1:
                for candidate in fitting_blocks[1:]:
                    if candidate['remaining'] >= MIN_FRAGMENT_SIZE:
                        chosen = candidate
                        break

            allocate_block(chosen['block'], req, blocks)
            step['block_id'] = chosen['block'].id
            step['remaining'] = chosen['remaining']
        else:
            step['action'] = 'waiting'

        step_history.append(step)

    result = build_memory_result('Best Available Fit', blocks, memory_requests)
    result['steps'] = step_history
    if time is not None:
        result['utilization_at_time'] = calculate_utilization_at_time(blocks, time)
    return result


# ============= MEMORY UTILITIES =============
def compact_memory(blocks: List) -> List:
    """
    Compaction: physically slide every allocated block down to the start
    of memory (removing the gaps between them), then merge all the freed
    space into a single contiguous free block at the end.

    This eliminates external fragmentation entirely - useful for showing
    what an OS would do if it paused everything to defragment memory.
    """
    allocated_blocks = [b for b in blocks if b.is_allocated]
    total_size = sum(b.size for b in blocks)

    compacted: List = []
    cursor = 0
    for b in allocated_blocks:
        b.start = cursor
        b.end = cursor + b.size
        cursor += b.size
        compacted.append(b)

    used_total = cursor
    leftover = total_size - used_total
    if leftover > 0:
        next_id = max((b.id for b in blocks), default=-1) + 1
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


def release_process(blocks: List, process_id: str) -> List:
    """
    Release every block currently allocated to `process_id`, freeing that
    memory and coalescing it with any adjacent free blocks.
    """
    matching_blocks = [b for b in blocks if b.is_allocated and b.process_id == process_id]
    for b in matching_blocks:
        free_block(b, blocks)
    return blocks


def calculate_utilization_at_time(blocks: List, time: int) -> Dict[str, Any]:
    """
    Calculate memory utilization at a specific simulation timestamp.
    """
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


def _find_block(blocks: List, size: int, algorithm: str, next_fit_pointer: int = 0):
    """
    Internal helper: pick the right fit function based on the algorithm string.
    Returns (block_or_None, new_pointer) so next_fit pointer can be tracked.
    """
    if algorithm == 'first_fit':
        return find_first_fit(blocks, size), next_fit_pointer
    elif algorithm == 'next_fit':
        return find_next_fit(blocks, size, next_fit_pointer)
    elif algorithm == 'best_fit':
        return find_best_fit(blocks, size), next_fit_pointer
    elif algorithm == 'worst_fit':
        return find_worst_fit(blocks, size), next_fit_pointer
    else:
        return find_first_fit(blocks, size), next_fit_pointer


def simulate_memory_scheduling(processes: List[Dict],
                               total_memory: int,
                               algorithm: str = 'first_fit',
                               compaction: bool = False) -> Dict[str, Any]:
    """
    Simulate memory allocation over time with FCFS CPU scheduling.

    Processes: list of dicts with pid, arrival, burst, memory.
    total_memory: total physical memory size (KB).
    algorithm: 'first_fit' | 'next_fit' | 'best_fit' | 'worst_fit'.
    compaction: if True, compact when an allocation fails before giving up.

    Returns a timeline with memory map and utilization per second.

    Bug fixes applied:
    - Replaced the broken double allocate_block() call with _find_block()
      + allocate_block() using the correct (block, request, blocks) signature.
    - Compaction now runs only after a fit fails, not unconditionally every
      tick, so it doesn't waste cycles and gives a true "compaction helped" result.
    - Added a stall-guard: if ready_queue is non-empty but no allocation
      succeeded AND no process is running, we advance time to the next
      arrival to prevent an infinite loop.
    """
    blocks = [MemoryBlock(
        id=0, start=0, end=total_memory,
        size=total_memory, is_allocated=False, process_id=None
    )]

    procs = sorted(processes, key=lambda p: p['arrival'])
    ready_queue: List[Dict] = []
    in_memory: Dict[str, int] = {}   # pid -> remaining burst
    timeline: List[Dict] = []

    idx = 0
    n = len(procs)
    t = 0
    next_fit_pointer = 0  # only used by next_fit

    MAX_TICKS = sum(p['burst'] for p in procs) + sum(p['arrival'] for p in procs) + 10

    while (idx < n or ready_queue or in_memory) and t <= MAX_TICKS:
        # 1. Admit newly arrived processes to the ready queue
        while idx < n and procs[idx]['arrival'] <= t:
            ready_queue.append(procs[idx])
            idx += 1

        # 2. Try to allocate memory for each waiting process (FCFS order)
        allocated_this_tick: List[str] = []
        still_waiting: List[Dict] = []

        for proc in ready_queue:
            size = proc['memory']
            block, next_fit_pointer = _find_block(blocks, size, algorithm, next_fit_pointer)

            # BUG FIX: if no block fits and compaction is enabled, compact then retry once
            if block is None and compaction:
                compact_memory(blocks)
                block, next_fit_pointer = _find_block(blocks, size, algorithm, next_fit_pointer)

            if block is not None:
                req = MemoryRequest(process_id=proc['pid'], size=size)
                allocate_block(block, req, blocks)
                in_memory[proc['pid']] = proc['burst']
                allocated_this_tick.append(proc['pid'])
            else:
                still_waiting.append(proc)

        ready_queue = still_waiting

        # 3. Execute one time unit for all processes currently in memory
        finished_this_tick: List[str] = []
        for pid in list(in_memory.keys()):
            in_memory[pid] -= 1
            if in_memory[pid] <= 0:
                release_process(blocks, pid)
                del in_memory[pid]
                finished_this_tick.append(pid)

        # 4. Record snapshot
        total = sum(b.size for b in blocks)
        used = sum(b.size for b in blocks if b.is_allocated)
        util = (used / total * 100) if total else 0.0

        timeline.append({
            'time': t,
            'blocks': [b.to_dict() for b in blocks],
            'utilization': round(util, 2),
            'allocated': allocated_this_tick,
            'finished': finished_this_tick,
            'running': list(in_memory.keys()),
            'waiting': [p['pid'] for p in ready_queue],
        })

        t += 1

        # BUG FIX: stall guard — if nothing is running and nothing was
        # allocated, skip time ahead to next arrival to avoid infinite loop
        if not in_memory and not allocated_this_tick and ready_queue and idx < n:
            t = procs[idx]['arrival']
        elif not in_memory and not allocated_this_tick and ready_queue and idx >= n:
            # Processes are stuck with no hope of allocation — break out
            break

    return {
        'algorithm': algorithm,
        'compaction': compaction,
        'timeline': timeline,
        'total_memory': total_memory,
        'final_blocks': [b.to_dict() for b in blocks],
    }


# ============= Algorithm Router =============
MEMORY_ALGORITHMS = {
    'first_fit': first_fit,
    'next_fit': next_fit,
    'best_fit': best_fit,
    'worst_fit': worst_fit,
    'best_available_fit': best_available_fit,
}


def run_memory_algorithm(algorithm: str, block_sizes: List[int], requests: List[Dict], time: Optional[int] = None) -> Dict[str, Any]:
    """Public entry point for Flask API (block-mode)."""
    if algorithm not in MEMORY_ALGORITHMS:
        raise ValueError(f"Unknown memory algorithm: {algorithm}")
    return MEMORY_ALGORITHMS[algorithm](block_sizes, requests, time=time)