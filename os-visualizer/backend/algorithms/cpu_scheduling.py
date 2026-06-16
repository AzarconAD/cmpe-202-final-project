import heapq
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

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

# ============= FCFS =============
def fcfs(processes: List[Dict]) -> Dict[str, Any]:
    procs = [Process(**p) for p in processes]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    
    for p in procs:
        if current_time < p.arrival:
            current_time = p.arrival
        p.start_time = current_time
        p.finish_time = current_time + p.burst
        gantt.append({'pid': p.pid, 'start': p.start_time, 'end': p.finish_time})
        current_time = p.finish_time
    
    calculate_metrics(procs)
    return build_result('FCFS', gantt, procs)

# ============= SJF (Non-Preemptive) =============
def sjf(processes: List[Dict]) -> Dict[str, Any]:
    procs = [Process(**p) for p in processes]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    completed = 0
    ready_queue = []
    n = len(procs)
    visited = [False] * n
    
    while completed < n:
        # Add arrived processes to ready queue
        for i, p in enumerate(procs):
            if p.arrival <= current_time and not visited[i]:
                heapq.heappush(ready_queue, (p.burst, i, p))
                visited[i] = True
        
        if ready_queue:
            _, i, p = heapq.heappop(ready_queue)
            if current_time < p.arrival:
                current_time = p.arrival
            p.start_time = current_time
            p.finish_time = current_time + p.burst
            gantt.append({'pid': p.pid, 'start': p.start_time, 'end': p.finish_time})
            current_time = p.finish_time
            completed += 1
        else:
            current_time += 1
    
    calculate_metrics(procs)
    return build_result('SJF', gantt, procs)

# ============= SJF (Preemptive - SRTF) =============
def sjf_preemptive(processes: List[Dict]) -> Dict[str, Any]:
    procs = [Process(**p) for p in processes]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    completed = 0
    n = len(procs)
    ready_queue = []  # (remaining_burst, arrival, pid, process)
    i = 0
    last_pid = None
    
    while completed < n:
        # Add newly arrived processes
        while i < n and procs[i].arrival <= current_time:
            p = procs[i]
            p.remaining = p.burst
            heapq.heappush(ready_queue, (p.remaining, p.arrival, p.pid, p))
            i += 1
        
        if ready_queue:
            remaining, arrival, pid, p = heapq.heappop(ready_queue)
            if p.start_time is None:
                p.start_time = current_time
            
            # If different process, start new gantt entry
            if last_pid != pid:
                if last_pid is not None:
                    gantt[-1]['end'] = current_time
                gantt.append({'pid': pid, 'start': current_time, 'end': current_time + 1})
                last_pid = pid
            
            p.remaining -= 1
            current_time += 1
            
            # Update gantt end time
            gantt[-1]['end'] = current_time
            
            # If process finished
            if p.remaining == 0:
                p.finish_time = current_time
                completed += 1
                last_pid = None
            else:
                # Re-queue with remaining time
                heapq.heappush(ready_queue, (p.remaining, p.arrival, p.pid, p))
        else:
            current_time += 1
    
    calculate_metrics(procs)
    return build_result('SJF Preemptive (SRTF)', gantt, procs)

# ============= Priority Scheduling (Non-Preemptive) =============
def priority(processes: List[Dict], aging_interval: int = 5) -> Dict[str, Any]: # with aging to prevent starvation
    procs = [Process(**p) for p in processes]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    completed = 0
    n = len(procs)
    ready_queue = []
    visited = [False] * n
    last_aging_time = 0
    
    while completed < n:
        # Add arrived processes to ready queue
        for i, p in enumerate(procs):
            if p.arrival <= current_time and not visited[i]:
                heapq.heappush(ready_queue, (p.priority, p.arrival, i, p))
                visited[i] = True
        
        # Apply aging every 'aging_interval' ms
        if current_time - last_aging_time >= aging_interval:
            new_ready_queue = []
            # Boost priority of all waiting processes
            for priority, arrival, i, p in ready_queue:
                p.priority = max(0, p.priority - 1)  # Higher priority (lower number)
                heapq.heappush(new_ready_queue, (p.priority, p.arrival, i, p))
            ready_queue = new_ready_queue
            last_aging_time = current_time
        
        if ready_queue:
            _, _, i, p = heapq.heappop(ready_queue)
            if current_time < p.arrival:
                current_time = p.arrival
            p.start_time = current_time
            p.finish_time = current_time + p.burst
            gantt.append({'pid': p.pid, 'start': p.start_time, 'end': p.finish_time})
            current_time = p.finish_time
            completed += 1
        else:
            current_time += 1
    
    calculate_metrics(procs)
    return build_result('Priority (Non-Preemptive)', gantt, procs)

# ============= Priority Scheduling (Preemptive) =============
def priority_preemptive(processes: List[Dict], aging_interval: int = 5) -> Dict[str, Any]: # with aging to prevent starvation
    procs = [Process(**p) for p in processes]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    completed = 0
    n = len(procs)
    ready_queue = []
    i = 0
    last_pid = None
    last_aging_time = 0
    
    while completed < n:
        # Add newly arrived processes
        while i < n and procs[i].arrival <= current_time:
            p = procs[i]
            p.remaining = p.burst
            heapq.heappush(ready_queue, (p.priority, p.arrival, p.pid, p))
            i += 1
        
        # Apply aging every 'aging_interval' ms
        if current_time - last_aging_time >= aging_interval:
            new_ready_queue = []
            for priority, arrival, pid, p in ready_queue:
                p.priority = max(0, p.priority - 1)  # Boost priority
                heapq.heappush(new_ready_queue, (p.priority, p.arrival, p.pid, p))
            ready_queue = new_ready_queue
            last_aging_time = current_time
        
        if ready_queue:
            priority_val, arrival, pid, p = heapq.heappop(ready_queue)
            if p.start_time is None:
                p.start_time = current_time
            
            if last_pid != pid:
                if last_pid is not None:
                    gantt[-1]['end'] = current_time
                gantt.append({'pid': pid, 'start': current_time, 'end': current_time + 1})
                last_pid = pid
            
            p.remaining -= 1
            current_time += 1
            gantt[-1]['end'] = current_time
            
            if p.remaining == 0:
                p.finish_time = current_time
                completed += 1
                last_pid = None
            else:
                # Re-queue with remaining
                heapq.heappush(ready_queue, (p.priority, p.arrival, p.pid, p))
        else:
            current_time += 1
    
    calculate_metrics(procs)
    return build_result('Priority Preemptive', gantt, procs)

# ============= Round Robin =============
def round_robin(processes: List[Dict], quantum: int) -> Dict[str, Any]:
    procs = [Process(**p) for p in processes]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    ready_queue = deque()
    n = len(procs)
    i = 0
    completed = 0
    
    # Initialize remaining times
    for p in procs:
        p.remaining = p.burst
    
    while completed < n:
        # Add newly arrived processes
        while i < n and procs[i].arrival <= current_time:
            ready_queue.append(procs[i])
            i += 1
        
        if ready_queue:
            p = ready_queue.popleft()
            
            # If process hasn't started or was preempted
            if p.start_time is None:
                p.start_time = current_time
            
            # Execute for quantum or until completion
            exec_time = min(quantum, p.remaining)
            p.remaining -= exec_time
            
            gantt.append({'pid': p.pid, 'start': current_time, 'end': current_time + exec_time})
            current_time += exec_time
            
            # Add new arrivals during execution
            while i < n and procs[i].arrival <= current_time:
                ready_queue.append(procs[i])
                i += 1
            
            if p.remaining > 0:
                ready_queue.append(p)
            else:
                p.finish_time = current_time
                completed += 1
        else:
            current_time += 1
    
    calculate_metrics(procs)
    return build_result('Round Robin', gantt, procs)

# ============= MLQ (Multi-Level Queue) =============
def mlq(processes: List[Dict], quantum_system: int = 4) -> Dict[str, Any]:
    """
    Processes have 'queue' field: 0=System (RR), 1=User (FCFS)
    System queue has higher priority
    """
    procs = [Process(**p) for p in processes]
    
    # Separate by queue
    system_queue = [p for p in procs if p.queue == 'system']
    user_queue   = [p for p in procs if p.queue == 'user']
    
    system_queue.sort(key=lambda x: x.arrival)
    user_queue.sort(key=lambda x: x.arrival)
    
    gantt = []
    current_time = 0
    system_idx = 0
    user_idx = 0
    system_ready = deque()
    user_ready = deque()
    n = len(procs)
    completed = 0
    
    # Initialize remaining
    for p in procs:
        p.remaining = p.burst
    
    while completed < n:
        # Add arrived system processes
        while system_idx < len(system_queue) and system_queue[system_idx].arrival <= current_time:
            system_ready.append(system_queue[system_idx])
            system_idx += 1
        
        # Add arrived user processes
        while user_idx < len(user_queue) and user_queue[user_idx].arrival <= current_time:
            user_ready.append(user_queue[user_idx])
            user_idx += 1
        
        # System queue gets priority (RR)
        if system_ready:
            p = system_ready.popleft()
            if p.start_time is None:
                p.start_time = current_time
            
            exec_time = min(quantum_system, p.remaining)
            p.remaining -= exec_time
            gantt.append({'pid': p.pid, 'start': current_time, 'end': current_time + exec_time})
            current_time += exec_time
            
            # Check for new arrivals
            while system_idx < len(system_queue) and system_queue[system_idx].arrival <= current_time:
                system_ready.append(system_queue[system_idx])
                system_idx += 1
            
            if p.remaining > 0:
                system_ready.append(p)
            else:
                p.finish_time = current_time
                completed += 1
        
        # User queue (FCFS)
        elif user_ready:
            p = user_ready.popleft()
            if p.start_time is None:
                p.start_time = current_time
            
            # Non-preemptive for user queue
            exec_time = p.remaining
            p.remaining = 0
            gantt.append({'pid': p.pid, 'start': current_time, 'end': current_time + exec_time})
            current_time += exec_time
            p.finish_time = current_time
            completed += 1
            
            # Add newly arrived system processes (preempt user)
            while system_idx < len(system_queue) and system_queue[system_idx].arrival <= current_time:
                system_ready.append(system_queue[system_idx])
                system_idx += 1
        else:
            current_time += 1
    
    calculate_metrics(procs)
    return build_result('MLQ', gantt, procs)

# ============= MLFQ (Multi-Level Feedback Queue) =============
def mlfq(processes: List[Dict], time_quantums: List[int] = [4, 8, 16]) -> Dict[str, Any]:
    """
    3 queues: Q0=RR(4ms), Q1=RR(8ms), Q2=FCFS
    Priority boost every 10ms (to prevent starvation)
    """
    procs = [Process(**p) for p in processes]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    n = len(procs)
    completed = 0
    arrived_idx = 0
    
    # Queues: Q0 (highest priority), Q1, Q2 (lowest)
    queues = [deque(), deque(), deque()]
    process_queue_level = {}  # Track which queue each process is in
    remaining_time = {}  # Remaining burst time
    last_executed_time = {}  # For priority boost
    last_boost_time = 0
    
    # Initialize
    for p in procs:
        p.remaining = p.burst
        remaining_time[p.pid] = p.burst
        process_queue_level[p.pid] = 0
        last_executed_time[p.pid] = 0
    
    # Add initial arrived processes to Q0
    while arrived_idx < n and procs[arrived_idx].arrival <= current_time:
        queues[0].append(procs[arrived_idx])
        arrived_idx += 1
    
    while completed < n:
        # Priority boost every 10ms
        if current_time > 0 and current_time - last_boost_time >= 10:
            last_boost_time = current_time 
            # Move all processes to Q0
            for q in [1, 2]:
                while queues[q]:
                    p = queues[q].popleft()
                    process_queue_level[p.pid] = 0
                    queues[0].append(p)
        
        # Check if any queue has processes
        selected_queue = -1
        for q in range(3):
            if queues[q]:
                selected_queue = q
                break
        
        if selected_queue != -1:
            p = queues[selected_queue].popleft()
            
            if p.start_time is None:
                p.start_time = current_time
            
            # Determine execution time
            if selected_queue < 2:  # RR queues
                quantum = time_quantums[selected_queue]
                exec_time = min(quantum, remaining_time[p.pid])
            else:  # FCFS queue
                exec_time = remaining_time[p.pid]
            
            remaining_time[p.pid] -= exec_time
            p.remaining -= exec_time
            gantt.append({'pid': p.pid, 'start': current_time, 'end': current_time + exec_time})
            current_time += exec_time
            last_executed_time[p.pid] = current_time
            
            # Add newly arrived processes
            while arrived_idx < n and procs[arrived_idx].arrival <= current_time:
                queues[0].append(procs[arrived_idx])
                arrived_idx += 1
            
            if remaining_time[p.pid] > 0:
                # Demote to lower queue
                if selected_queue < 2:
                    process_queue_level[p.pid] = selected_queue + 1
                    queues[selected_queue + 1].append(p)
                else:
                    # Stay in Q2 (FCFS)
                    queues[2].append(p)
            else:
                # Process completed
                p.finish_time = current_time
                completed += 1
        else:
            # No processes ready, advance time
            current_time += 1
            # Check if any process arrived during idle
            while arrived_idx < n and procs[arrived_idx].arrival <= current_time:
                queues[0].append(procs[arrived_idx])
                arrived_idx += 1
    
    calculate_metrics(procs)
    return build_result('MLFQ', gantt, procs)

# ============= Main function for API usage =============
def build_result(algorithm: str, gantt, procs) -> Dict[str, Any]:
    return {
        'algorithm': algorithm,
        'gantt': format_gantt(gantt),
        'processes': [p.to_dict() for p in procs],
        'avg_waiting': sum(p.waiting_time for p in procs) / len(procs),
        'avg_turnaround': sum(p.turnaround_time for p in procs) / len(procs),
    }

ALGORITHMS = {
    'fcfs': fcfs,
    'sjf': sjf,
    'sjf_preemptive': sjf_preemptive,
    'priority': priority,
    'priority_preemptive': priority_preemptive,
    'round_robin': lambda p, **kw: round_robin(p, kw.get('quantum', 4)),
    'mlq': lambda p, **kw: mlq(p, kw.get('quantum_system', 4)),
    'mlfq': lambda p, **kw: mlfq(p, kw.get('time_quantums', [4, 8, 16])),
}

def run_algorithm(algorithm: str, processes: List[Dict], **kwargs):
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    return ALGORITHMS[algorithm](processes, **kwargs)

# ============= Example usage =============
if __name__ == '__main__':
    # Test data
    test_processes = [
        {'pid': 'P1', 'arrival': 0, 'burst': 8, 'priority': 2},
        {'pid': 'P2', 'arrival': 1, 'burst': 4, 'priority': 1},
        {'pid': 'P3', 'arrival': 2, 'burst': 9, 'priority': 3},
        {'pid': 'P4', 'arrival': 3, 'burst': 5, 'priority': 2},
    ]
    
    print("=== FCFS ===")
    result = fcfs(test_processes)
    print(f"Gantt: {result['gantt']}")
    print(f"Avg Waiting: {result['avg_waiting']:.2f}")
    
    print("\n=== SJF ===")
    result = sjf(test_processes)
    print(f"Gantt: {result['gantt']}")
    print(f"Avg Waiting: {result['avg_waiting']:.2f}")
    
    print("\n=== Round Robin (Quantum=4) ===")
    result = round_robin(test_processes, 4)
    print(f"Gantt: {result['gantt']}")
    print(f"Avg Waiting: {result['avg_waiting']:.2f}")