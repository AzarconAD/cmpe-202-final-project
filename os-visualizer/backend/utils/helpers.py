from typing import Any, Dict, List, Optional, Tuple
from backend.models.process import Process, MemoryBlock, MemoryRequest

# ============================================================
# CPU Scheduling Helpers
# ============================================================
def calculate_metrics(processes: List[Process]):
    """
    After a CPU scheduling simulation, compute turnaround time and waiting time
    for each process.
    """
    for p in processes:
        p.turnaround_time = p.finish_time - p.arrival
        p.waiting_time = p.turnaround_time - p.burst


def format_gantt(gantt: List[Dict]) -> List[Dict]:
    """
    Merge consecutive Gantt chart entries that belong to the same process.
    Example: [P1:0-2, P1:2-5] → [P1:0-5]
    """
    merged = []
    for entry in gantt:
        if merged and merged[-1]['pid'] == entry['pid']:
            merged[-1]['end'] = entry['end']
        else:
            merged.append(entry)
    return merged


def build_result(algorithm: str, gantt, procs) -> Dict[str, Any]:
    """Package the CPU scheduling result into a standard dictionary."""
    return {
        'algorithm': algorithm,
        'gantt': format_gantt(gantt),
        'processes': [p.to_dict() for p in procs],
        'avg_waiting': sum(p.waiting_time for p in procs) / len(procs),
        'avg_turnaround': sum(p.turnaround_time for p in procs) / len(procs),
    }


# ============================================================
# Memory Management Helpers
# ============================================================
def build_memory_result(algorithm: str, blocks: List[MemoryBlock],
                        requests: List[MemoryRequest]) -> Dict[str, Any]:
    """Package the memory allocation result into a standard dictionary."""
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
    """Create a list of free MemoryBlock objects from the given partition sizes."""
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


def allocate_block(block: MemoryBlock, request: MemoryRequest,
                   blocks: List[MemoryBlock]):
    """
    Allocate a memory block to a request. If the block is larger than needed,
    split off the remainder as a new free block.
    """
    if block.size > request.size:
        # Create a new free block for the leftover space.
        next_id = max((b.id for b in blocks), default=-1) + 1
        remainder = MemoryBlock(
            id=next_id,
            start=block.start + request.size,
            end=block.end,
            size=block.size - request.size,
            is_allocated=False,
            process_id=None
        )
        # Shrink the original block to the requested size.
        block.end = block.start + request.size
        block.size = request.size
        # Insert the remainder right after the allocated block.
        blocks.insert(blocks.index(block) + 1, remainder)
    # Mark the block as allocated.
    block.is_allocated = True
    block.process_id = request.process_id
    request.allocated_block = block.id
    return block


def free_block(block: MemoryBlock, blocks: List[MemoryBlock]):
    """Free an allocated block and merge adjacent free blocks."""
    block.is_allocated = False
    block.process_id = None
    coalesce_free_blocks(blocks)


def coalesce_free_blocks(blocks: List[MemoryBlock]):
    """Merge adjacent free blocks into one larger block."""
    blocks.sort(key=lambda b: b.start)   # sort by starting address
    i = 0
    while i < len(blocks) - 1:
        current = blocks[i]
        nxt = blocks[i + 1]
        # If both are free and adjacent, merge them.
        if not current.is_allocated and not nxt.is_allocated and current.end == nxt.start:
            current.end = nxt.end
            current.size = current.end - current.start
            blocks.pop(i + 1)   # remove the merged block
        else:
            i += 1


# ============================================================
# Allocation Algorithm Helpers (used in MVT simulation)
# ============================================================
def find_first_fit(blocks, size):
    """Return the first free block that is large enough."""
    for b in blocks:
        if not b.is_allocated and b.size >= size:
            return b
    return None


def find_next_fit(blocks, size, pointer):
    """
    Return the first free block that fits, starting the search from `pointer`
    (and wrapping around). Also returns the new pointer position.
    """
    n = len(blocks)
    for i in range(n):
        idx = (pointer + i) % n
        b = blocks[idx]
        if not b.is_allocated and b.size >= size:
            return b, (idx + 1) % n
    return None, pointer


def find_best_fit(blocks, size):
    """Return the free block with the smallest size that still fits."""
    best = None
    best_size = float('inf')
    for b in blocks:
        if not b.is_allocated and b.size >= size and b.size < best_size:
            best = b
            best_size = b.size
    return best


def find_worst_fit(blocks, size):
    """Return the free block with the largest size (leaves biggest leftover)."""
    worst = None
    worst_size = -1
    for b in blocks:
        if not b.is_allocated and b.size >= size and b.size > worst_size:
            worst = b
            worst_size = b.size
    return worst


def allocate_with_algorithm(blocks: List[MemoryBlock], size: int,
                            algorithm: str, pointer: int = 0) -> Tuple[Optional[MemoryBlock], int]:
    """
    Dispatch to the correct allocation finder based on the algorithm name.
    Returns the chosen block (or None) and the updated pointer (for Next Fit).
    """
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


# ============================================================
# Compaction and Release (used in MVT simulation)
# ============================================================
def compact_memory(blocks: List[MemoryBlock]) -> List[MemoryBlock]:
    """
    Move all allocated blocks to the start of memory, merging all free space
    into one contiguous block at the end. This eliminates fragmentation.
    """
    allocated_blocks = [b for b in blocks if b.is_allocated]
    total_size = sum(b.size for b in blocks)
    next_id = max((b.id for b in blocks), default=-1) + 1
    compacted: List[MemoryBlock] = []
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
    """Free all memory blocks that belong to the given process."""
    matching = [b for b in blocks if b.is_allocated and b.process_id == process_id]
    for b in matching:
        free_block(b, blocks)
    return blocks


def calculate_utilization_at_time(blocks: List[MemoryBlock], time: int) -> Dict[str, Any]:
    """Calculate memory usage statistics at a given simulation time."""
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


# ============================================================
# MVT (Dynamic Memory) Main Simulation
# ============================================================
def simulate_memory_scheduling(processes: List[Dict], total_memory: int,
                               algorithm: str, compaction: bool = False,
                               cpu_algorithm: str = 'fcfs', cpu_quantum: int = 4) -> Dict[str, Any]:
    """
    Run a complete MVT simulation:
      - Processes arrive over time.
      - They wait in a ready queue.
      - The chosen scheduling algorithm (fcfs, sjf_preemptive, etc.)
        decides the order in which they are admitted to memory.
      - Each process occupies memory for its 'burst' time (holding time),
        then releases it.
      - Compaction may be triggered to defragment memory.
    Returns a timeline of snapshots.
    """
    # Start with one big free block.
    blocks = [MemoryBlock(id=0, start=0, end=total_memory, size=total_memory,
                          is_allocated=False, process_id=None)]
    procs = sorted(processes, key=lambda p: p['arrival'])
    ready_queue = []                 # processes waiting for memory
    in_memory = {}                   # pid -> remaining burst, priority, arrival
    timeline = []
    t = 0
    idx = 0
    n = len(procs)
    pointer = 0

    while idx < n or ready_queue or any(in_memory.values()):
        # 1. Admit newly arrived processes to the ready queue.
        while idx < n and procs[idx]['arrival'] <= t:
            ready_queue.append(procs[idx])
            idx += 1

        # 2. Decrement remaining burst for ALL processes in memory.
        finished = []
        for pid in list(in_memory.keys()):
            in_memory[pid]['remaining'] -= 1
            if in_memory[pid]['remaining'] == 0:
                finished.append(pid)

        # 3. Release finished processes (free their memory).
        finished_any = False
        for pid in finished:
            release_process(blocks, pid)
            del in_memory[pid]
            finished_any = True

        # 4. Compact if enabled and something was freed.
        compacted_this_tick = False
        if compaction and finished_any:
            compact_memory(blocks)
            pointer = 0
            compacted_this_tick = True

        # 5. Sort ready_queue according to the chosen CPU algorithm.
        if cpu_algorithm == 'fcfs':
            pass   # keep arrival order
        elif cpu_algorithm in ('sjf_preemptive', 'srtf'):
            ready_queue.sort(key=lambda p: p['burst'])
        elif cpu_algorithm == 'priority_preemptive':
            ready_queue.sort(key=lambda p: p.get('priority', 0))
        elif cpu_algorithm == 'round_robin':
            pass   # treat as FCFS for admission order

        # 6. Try to allocate memory for waiting processes (in the sorted order).
        allocated_this_tick = []
        new_ready = []
        for proc in ready_queue:
            size = proc['memory']
            block, new_pointer = allocate_with_algorithm(blocks, size, algorithm, pointer)
            # If compaction is on and allocation fails, compact and retry.
            if block is None and compaction:
                compact_memory(blocks)
                pointer = 0
                compacted_this_tick = True
                block, new_pointer = allocate_with_algorithm(blocks, size, algorithm, pointer)
            if block is not None:
                req = MemoryRequest(proc['pid'], size)
                allocate_block(block, req, blocks)
                in_memory[proc['pid']] = {
                    'remaining': proc['burst'],
                    'priority': proc.get('priority', 0),
                    'arrival': proc['arrival']
                }
                allocated_this_tick.append(proc['pid'])
                pointer = new_pointer
            else:
                new_ready.append(proc)
        ready_queue = new_ready

        # 7. Record a snapshot of the current memory state.
        total_mem = sum(b.size for b in blocks)
        used = sum(b.size for b in blocks if b.is_allocated)
        util = (used / total_mem * 100) if total_mem else 0.0

        timeline.append({
            'time': t,
            'blocks': [b.to_dict() for b in blocks],
            'utilization': round(util, 2),
            'allocated': allocated_this_tick,
            'finished': finished,
            'waiting': [p['pid'] for p in ready_queue],
            'running': list(in_memory.keys()),
            'compacted': compacted_this_tick,
        })
        t += 1

    return {
        'algorithm': algorithm,
        'cpu_algorithm': cpu_algorithm,
        'cpu_quantum': cpu_quantum,
        'compaction': compaction,
        'timeline': timeline,
        'total_memory': total_memory,
        'final_blocks': [b.to_dict() for b in blocks]
    }