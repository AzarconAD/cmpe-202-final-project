from typing import List, Dict, Any
from models.process import Process

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