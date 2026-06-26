import heapq
import copy
from collections import deque
from typing import List, Dict, Any

from backend.models.process import Process
from backend.utils.helpers import calculate_metrics, build_result

# Helper: make a fresh copy of the process list so previous runs don't change anything.
def _fresh(processes: List[Dict]) -> List[Dict]:
    return copy.deepcopy(processes)


# ============= FCFS =============
def fcfs(processes: List[Dict]) -> Dict[str, Any]:
    # Create Process objects from the input dicts.
    procs = [Process(**p) for p in _fresh(processes)]
    # Sort by arrival time (first come, first served).
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0

    for p in procs:
        # If CPU is idle, jump to the next arrival.
        if current_time < p.arrival:
            current_time = p.arrival
        p.start_time = current_time
        p.finish_time = current_time + p.burst
        # Record this block in the Gantt chart.
        gantt.append({'pid': p.pid, 'start': p.start_time, 'end': p.finish_time})
        current_time = p.finish_time

    calculate_metrics(procs)
    return build_result('FCFS', gantt, procs)


# ============= SJF (Non-Preemptive) =============
def sjf(processes: List[Dict]) -> Dict[str, Any]:
    procs = [Process(**p) for p in _fresh(processes)]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    completed = 0
    ready_queue = []          # min‑heap by burst time
    n = len(procs)
    visited = [False] * n

    while completed < n:
        # Add all processes that have arrived to the ready queue.
        for i, p in enumerate(procs):
            if p.arrival <= current_time and not visited[i]:
                heapq.heappush(ready_queue, (p.burst, i, p))
                visited[i] = True

        if ready_queue:
            # Pick the process with the shortest burst (heap gives smallest burst first).
            _, i, p = heapq.heappop(ready_queue)
            if current_time < p.arrival:
                current_time = p.arrival
            p.start_time = current_time
            p.finish_time = current_time + p.burst
            gantt.append({'pid': p.pid, 'start': p.start_time, 'end': p.finish_time})
            current_time = p.finish_time
            completed += 1
        else:
            # No process ready – advance time.
            current_time += 1

    calculate_metrics(procs)
    return build_result('SJF (Non-Preemptive)', gantt, procs)


# ============= SJF (Preemptive) =============
def sjf_preemptive(processes: List[Dict]) -> Dict[str, Any]:
    procs = [Process(**p) for p in _fresh(processes)]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    completed = 0
    n = len(procs)
    ready_queue = []          # heap by remaining burst
    i = 0
    last_pid = None           # track the last process that ran, to merge Gantt blocks.

    while completed < n:
        # Add newly arrived processes to the ready queue.
        while i < n and procs[i].arrival <= current_time:
            p = procs[i]
            p.remaining = p.burst
            heapq.heappush(ready_queue, (p.remaining, p.arrival, p.pid, p))
            i += 1

        if ready_queue:
            remaining, arrival, pid, p = heapq.heappop(ready_queue)
            if p.start_time is None:
                p.start_time = current_time

            # If a different process is now running, end the previous Gantt block.
            if last_pid != pid:
                if last_pid is not None:
                    gantt[-1]['end'] = current_time
                gantt.append({'pid': pid, 'start': current_time, 'end': current_time + 1})
                last_pid = pid

            # Run this process for 1 ms.
            p.remaining -= 1
            current_time += 1
            gantt[-1]['end'] = current_time

            if p.remaining == 0:
                p.finish_time = current_time
                completed += 1
                last_pid = None
            else:
                # Put it back in the queue with the new remaining time.
                heapq.heappush(ready_queue, (p.remaining, p.arrival, p.pid, p))
        else:
            # No process ready – CPU idle.
            current_time += 1

    calculate_metrics(procs)
    return build_result('SJF Preemptive (SRTF)', gantt, procs)


# ============= Priority Scheduling (Non-Preemptive) =============
def priority(processes: List[Dict], aging_interval: int = 5) -> Dict[str, Any]:
    procs = [Process(**p) for p in _fresh(processes)]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    completed = 0
    n = len(procs)
    ready_queue = []          # heap by priority (lower number = higher priority)
    visited = [False] * n
    last_aging_time = 0
    last_pid = None

    while completed < n:
        # Add arrived processes to the ready queue.
        for i, p in enumerate(procs):
            if p.arrival <= current_time and not visited[i]:
                if p.priority is None:
                    p.priority = 0
                heapq.heappush(ready_queue, (p.priority, p.arrival, i, p))
                visited[i] = True

        # Apply aging every `aging_interval` ms.
        if current_time - last_aging_time >= aging_interval:
            new_ready_queue = []
            for priority, arrival, pid, p in ready_queue:
                if pid != last_pid:
                    p.priority = max(0, p.priority - 1)   # lower number = higher priority
                heapq.heappush(new_ready_queue, (p.priority, p.arrival, p.pid, p))
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
    return build_result('Priority (Non-Preemptive) with Aging', gantt, procs)


# ============= Priority Scheduling (Preemptive) =============
def priority_preemptive(processes: List[Dict], aging_interval: int = 5) -> Dict[str, Any]:
    procs = [Process(**p) for p in _fresh(processes)]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    completed = 0
    n = len(procs)
    ready_queue = []          # heap by priority (lower = higher)
    i = 0
    last_pid = None
    last_aging_time = 0

    while completed < n:
        # Add newly arrived processes to the ready queue.
        while i < n and procs[i].arrival <= current_time:
            p = procs[i]
            p.remaining = p.burst
            if p.priority is None:
                p.priority = 0
            heapq.heappush(ready_queue, (p.priority, p.arrival, p.pid, p))
            i += 1

        # Apply aging to waiting processes (excluding the one that is currently running).
        if current_time - last_aging_time >= aging_interval:
            new_ready_queue = []
            for priority, arrival, pid, p in ready_queue:
                if pid != last_pid:   # don't age the running process
                    p.priority = max(0, p.priority - 1)
                heapq.heappush(new_ready_queue, (p.priority, p.arrival, p.pid, p))
            ready_queue = new_ready_queue
            last_aging_time = current_time

        if ready_queue:
            priority_val, arrival, pid, p = heapq.heappop(ready_queue)
            if p.start_time is None:
                p.start_time = current_time

            # Switch Gantt block if a different process takes over.
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
                heapq.heappush(ready_queue, (p.priority, p.arrival, p.pid, p))
        else:
            current_time += 1

    calculate_metrics(procs)
    return build_result('Priority Preemptive with Aging', gantt, procs)


# ============= Round Robin =============
def round_robin(processes: List[Dict], quantum: int) -> Dict[str, Any]:
    procs = [Process(**p) for p in _fresh(processes)]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    ready_queue = deque()
    n = len(procs)
    i = 0
    completed = 0

    for p in procs:
        p.remaining = p.burst

    while completed < n:
        # Add newly arrived processes to the ready queue.
        while i < n and procs[i].arrival <= current_time:
            ready_queue.append(procs[i])
            i += 1

        if ready_queue:
            p = ready_queue.popleft()

            if p.start_time is None:
                p.start_time = current_time

            # Run for at most the quantum.
            exec_time = min(quantum, p.remaining)
            p.remaining -= exec_time

            gantt.append({'pid': p.pid, 'start': current_time, 'end': current_time + exec_time})
            current_time += exec_time

            # Add any new arrivals that came during this time slice.
            while i < n and procs[i].arrival <= current_time:
                ready_queue.append(procs[i])
                i += 1

            if p.remaining > 0:
                # Still has time left – put it at the back of the queue.
                ready_queue.append(p)
            else:
                p.finish_time = current_time
                completed += 1
        else:
            # No process ready – CPU idle.
            current_time += 1

    calculate_metrics(procs)
    return build_result('Round Robin', gantt, procs)


# ============= MLQ (Multi-Level Queue) =============
def mlq(processes: List[Dict], quantum_system: int = 4) -> Dict[str, Any]:
    procs = [Process(**p) for p in _fresh(processes)]

    # Separate system and user processes based on the 'queue' field.
    system_queue = [p for p in procs if p.queue == 'system']
    user_queue = [p for p in procs if p.queue == 'user']

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

    for p in procs:
        p.remaining = p.burst

    while completed < n:
        # Add arrived system processes to the system ready queue.
        while system_idx < len(system_queue) and system_queue[system_idx].arrival <= current_time:
            system_ready.append(system_queue[system_idx])
            system_idx += 1

        # Add arrived user processes to the user ready queue.
        while user_idx < len(user_queue) and user_queue[user_idx].arrival <= current_time:
            user_ready.append(user_queue[user_idx])
            user_idx += 1

        # System queue has absolute priority.
        if system_ready:
            p = system_ready.popleft()
            if p.start_time is None:
                p.start_time = current_time

            # System processes use Round Robin with quantum_system.
            exec_time = min(quantum_system, p.remaining)
            p.remaining -= exec_time
            gantt.append({'pid': p.pid, 'start': current_time, 'end': current_time + exec_time})
            current_time += exec_time

            # Add any new system arrivals that came during this slice.
            while system_idx < len(system_queue) and system_queue[system_idx].arrival <= current_time:
                system_ready.append(system_queue[system_idx])
                system_idx += 1

            if p.remaining > 0:
                system_ready.append(p)
            else:
                p.finish_time = current_time
                completed += 1

        # If no system process, run a user process (FCFS, non‑preemptive).
        elif user_ready:
            p = user_ready.popleft()
            if p.start_time is None:
                p.start_time = current_time

            # User processes run to completion.
            exec_time = p.remaining
            p.remaining = 0
            gantt.append({'pid': p.pid, 'start': current_time, 'end': current_time + exec_time})
            current_time += exec_time
            p.finish_time = current_time
            completed += 1

            # New system arrivals may appear during the user process – we'll handle them
            # at the top of the next loop, but we can check now to keep the queue fresh.
            while system_idx < len(system_queue) and system_queue[system_idx].arrival <= current_time:
                system_ready.append(system_queue[system_idx])
                system_idx += 1
        else:
            # No process ready – idle.
            current_time += 1

    calculate_metrics(procs)
    return build_result('MLQ (System: RR, User: FCFS)', gantt, procs)


# ============= MLFQ (Multi-Level Feedback Queue) =============
def mlfq(processes: List[Dict], time_quantums: List[int] = [4, 8, 16]) -> Dict[str, Any]:
    procs = [Process(**p) for p in _fresh(processes)]
    procs.sort(key=lambda x: x.arrival)
    gantt = []
    current_time = 0
    n = len(procs)
    completed = 0
    arrived_idx = 0

    # Three queues: Q0 (highest priority, RR 4ms), Q1 (RR 8ms), Q2 (FCFS)
    queues = [deque(), deque(), deque()]
    remaining_time = {}      # tracks remaining burst per process
    last_boost_time = 0

    for p in procs:
        p.remaining = p.burst
        remaining_time[p.pid] = p.burst

    # Put initial arrivals into Q0.
    while arrived_idx < n and procs[arrived_idx].arrival <= current_time:
        queues[0].append(procs[arrived_idx])
        arrived_idx += 1

    while completed < n:
        # Priority boost: every 10ms, move all processes back to Q0.
        if current_time > 0 and current_time - last_boost_time >= 10:
            last_boost_time = current_time
            for q in [1, 2]:
                while queues[q]:
                    p = queues[q].popleft()
                    queues[0].append(p)

        # Pick the highest‑priority non‑empty queue.
        selected_queue = -1
        for q in range(3):
            if queues[q]:
                selected_queue = q
                break

        if selected_queue != -1:
            p = queues[selected_queue].popleft()

            if p.start_time is None:
                p.start_time = current_time

            # Determine how long to run this process.
            if selected_queue < 2:   # RR queues
                quantum = time_quantums[selected_queue]
                exec_time = min(quantum, remaining_time[p.pid])
            else:                    # Q2 is FCFS – run to completion
                exec_time = remaining_time[p.pid]

            remaining_time[p.pid] -= exec_time
            p.remaining -= exec_time
            gantt.append({'pid': p.pid, 'start': current_time, 'end': current_time + exec_time})
            current_time += exec_time

            # Add any new arrivals that came during this slice.
            while arrived_idx < n and procs[arrived_idx].arrival <= current_time:
                queues[0].append(procs[arrived_idx])
                arrived_idx += 1

            if remaining_time[p.pid] > 0:
                # Process still has time left – demote it to the next lower queue.
                if selected_queue < 2:
                    queues[selected_queue + 1].append(p)
                else:
                    # Already in Q2 – stay in Q2.
                    queues[2].append(p)
            else:
                p.finish_time = current_time
                completed += 1
        else:
            # No process ready – advance time.
            current_time += 1
            # Check if any process arrived during idle time.
            while arrived_idx < n and procs[arrived_idx].arrival <= current_time:
                queues[0].append(procs[arrived_idx])
                arrived_idx += 1

    calculate_metrics(procs)
    return build_result('MLFQ (Q0:RR4ms, Q1:RR8ms, Q2:FCFS)', gantt, procs)


# ============= Algorithm Router =============
# A dictionary that maps algorithm names to the corresponding function.
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
    # Look up the algorithm and call it with the provided arguments.
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    return ALGORITHMS[algorithm](processes, **kwargs)