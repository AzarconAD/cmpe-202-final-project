from typing import List, Dict, Any, Optional

from models.process import MemoryRequest
from utils.helpers import initialize_memory, allocate_block, build_memory_result

# ============= FIRST FIT =============
def first_fit(block_sizes: List[int], requests: List[Dict]) -> Dict[str, Any]:
    """
    First Fit: Allocate the first block that is large enough
    
    Algorithm:
    1. Start from beginning of memory
    2. Find first free block that fits the request
    3. Allocate if found
    """
    # Initialize
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []  # Track allocation steps for visualization
    
    for req in memory_requests:
        allocated = False
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }
        
        # First Fit: scan from beginning
        for block in blocks:
            if block.is_free and block.size >= req.size:
                allocate_block(block, req, blocks)
                allocated = True
                step['block_id'] = block.id
                break
        
        if not allocated:
            step['action'] = 'waiting'
            # Keep track of requests that couldn't be allocated
        
        step_history.append(step)
    
    result = build_memory_result('First Fit', blocks, memory_requests)
    result['steps'] = step_history
    return result

# ============= BEST FIT =============
def best_fit(block_sizes: List[int], requests: List[Dict]) -> Dict[str, Any]:
    """
    Best Fit: Allocate the smallest block that is large enough
    
    Algorithm:
    1. Find all free blocks that fit the request
    2. Choose the block with the smallest size (minimum waste)
    3. Allocate if found
    """
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []
    
    for req in memory_requests:
        allocated = False
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }
        
        # Best Fit: find the smallest block that fits
        best_block = None
        best_fit_size = float('inf')
        
        for block in blocks:
            if block.is_free and block.size >= req.size:
                # Check if this block is a better fit (smaller)
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

# ============= BEST AVAILABLE FIT =============
def best_available_fit(block_sizes, requests, min_fragment_size: int = 2):
    """
    Best Available Fit: Variation of Best Fit that considers fragmentation
    
    This algorithm:
    1. Like Best Fit, finds the smallest block that fits
    2. BUT: If the remaining space after allocation is too small,
       it may choose a larger block to reduce fragmentation
    3. Uses a threshold to decide (e.g., don't create blocks smaller than 2KB)
    """
    blocks = initialize_memory(block_sizes)
    memory_requests = [MemoryRequest(**r) for r in requests]
    step_history = []
    MIN_FRAGMENT_SIZE = min_fragment_size  # Minimum useful block size (avoid tiny fragments)
    
    for req in memory_requests:
        allocated = False
        step = {
            'request': req.process_id,
            'size': req.size,
            'action': 'allocated',
            'block_id': None
        }
        
        # Find all blocks that fit
        fitting_blocks = []
        for block in blocks:
            if block.is_free and block.size >= req.size:
                remaining = block.size - req.size
                fitting_blocks.append({
                    'block': block,
                    'remaining': remaining
                })
        
        if fitting_blocks:
            # Sort by remaining space (Best Fit)
            fitting_blocks.sort(key=lambda x: x['remaining'])
            
            # Best Available: consider fragmentation
            chosen = fitting_blocks[0]  # Best Fit first
            
            # But if remaining space is too small, try next best
            if chosen['remaining'] < min_fragment_size and len(fitting_blocks) > 1:
                # Find a block with enough remaining space to be useful
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

# ============= Algorithm Router =============
MEMORY_ALGORITHMS = {
    'first_fit': first_fit,
    'best_fit': best_fit,
    'best_available_fit': best_available_fit,
}

def run_memory_algorithm(algorithm: str, block_sizes: List[int], requests: List[Dict]) -> Dict[str, Any]:
    """Public entry point for Flask API"""
    if algorithm not in MEMORY_ALGORITHMS:
        raise ValueError(f"Unknown memory algorithm: {algorithm}")
    return MEMORY_ALGORITHMS[algorithm](block_sizes, requests)