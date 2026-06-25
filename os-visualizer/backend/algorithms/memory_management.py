from typing import List, Dict, Any, Optional, Tuple
from backend.models.process import MemoryRequest, MemoryBlock
from backend.utils.helpers import (
    initialize_memory,
    allocate_block,
    compact_memory,
    build_memory_result
)

# ============= FIRST FIT =============
def first_fit(block_sizes: List[int], requests: List[Dict], compaction: bool = False) -> Dict[str, Any]:
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []

    for req in memory_requests:
        if compaction:
            blocks = compact_memory(blocks)

        allocated = False 
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }

        for block in blocks:
            if not block.is_allocated and block.size >= req.size:
                allocate_block(block, req, blocks)
                allocated = True
                step['block_id'] = block.id
                break

        if not allocated:
            step['action'] = 'waiting'

        step_history.append(step)

    result = build_memory_result('First Fit', blocks, memory_requests)
    result['steps'] = step_history
    return result

# ============= NEXT FIT =============
def next_fit(block_sizes: List[int], requests: List[Dict], compaction: bool = False) -> Dict[str, Any]:
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []
    pointer = 0

    for req in memory_requests:
        if compaction:
            blocks = compact_memory(blocks)

        allocated = False
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }

        n = len(blocks)
        if n > 0:
            for offset in range(n):
                idx = (pointer + offset) % n
                block = blocks[idx]
                if not block.is_allocated and block.size >= req.size:
                    allocate_block(block, req, blocks)
                    allocated = True
                    step['block_id'] = block.id
                    pointer = (idx + 1) % len(blocks)
                    break

        if not allocated:
            step['action'] = 'waiting'

        step_history.append(step)

    result = build_memory_result('Next Fit', blocks, memory_requests)
    result['steps'] = step_history
    return result

# ============= BEST FIT =============
def best_fit(block_sizes: List[int], requests: List[Dict], compaction: bool = False) -> Dict[str, Any]:
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []

    for req in memory_requests:
        if compaction:
            blocks = compact_memory(blocks)

        allocated = False
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }

        best_block = None
        best_fit_size = float('inf')
        for block in blocks:
            if not block.is_allocated and block.size >= req.size:
                if block.size < best_fit_size:
                    best_fit_size = block.size
                    best_block = block

        if best_block is not None:
            allocate_block(best_block, req, blocks)
            allocated = True
            step['block_id'] = best_block.id

        if not allocated:
            step['action'] = 'waiting'

        step_history.append(step)

    result = build_memory_result('Best Fit', blocks, memory_requests)
    result['steps'] = step_history
    return result

# ============= WORST FIT =============
def worst_fit(block_sizes: List[int], requests: List[Dict], compaction: bool = False) -> Dict[str, Any]:
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []

    for req in memory_requests:
        if compaction:
            blocks = compact_memory(blocks)

        allocated = False
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }

        worst_block = None
        worst_fit_size = -1
        for block in blocks:
            if not block.is_allocated and block.size >= req.size:
                if block.size > worst_fit_size:
                    worst_fit_size = block.size
                    worst_block = block

        if worst_block is not None:
            allocate_block(worst_block, req, blocks)
            allocated = True
            step['block_id'] = worst_block.id

        if not allocated:
            step['action'] = 'waiting'

        step_history.append(step)

    result = build_memory_result('Worst Fit', blocks, memory_requests)
    result['steps'] = step_history
    return result

# ============= BEST AVAILABLE FIT =============
def best_available_fit(block_sizes: List[int], requests: List[Dict], min_fragment_size: int = 2, compaction: bool = False) -> Dict[str, Any]:
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []
    MIN_FRAGMENT_SIZE = min_fragment_size

    for req in memory_requests:
        if compaction:
            blocks = compact_memory(blocks)

        allocated = False
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

            if chosen['remaining'] < min_fragment_size and len(fitting_blocks) > 1:
                for candidate in fitting_blocks[1:]:
                    if candidate['remaining'] >= min_fragment_size:
                        chosen = candidate
                        break

            allocate_block(chosen['block'], req, blocks)
            allocated = True
            step['block_id'] = chosen['block'].id
            step['remaining'] = chosen['remaining']

        if not allocated:
            step['action'] = 'waiting'

        step_history.append(step)

    result = build_memory_result('Best Available Fit', blocks, memory_requests)
    result['steps'] = step_history
    return result

# ============= ALGORITHM ROUTER =============
MEMORY_ALGORITHMS = {
    'first_fit': first_fit,
    'next_fit': next_fit,
    'best_fit': best_fit,
    'worst_fit': worst_fit,
    'best_available_fit': best_available_fit,
}

def run_memory_algorithm(algorithm: str, block_sizes: List[int], requests: List[Dict], compaction: bool = False) -> Dict[str, Any]:
    if algorithm not in MEMORY_ALGORITHMS:
        raise ValueError(f"Unknown memory algorithm: {algorithm}")
    return MEMORY_ALGORITHMS[algorithm](block_sizes, requests, compaction=compaction)