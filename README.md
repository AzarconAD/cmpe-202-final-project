# OS Visualizer — Operating System Algorithm Simulator

> Final Project — CMPE 202 Operating Systems 

> BSCPE 2-2

> Azarcon, Adam Daniel P.

> Canoy, James Starwin T.

> Clemente, Benidict C.

> Mangalindan, Justin Rain C.

A web app that lets you visually run and compare classic Operating System algorithms — see exactly how a CPU scheduler, memory allocator, page replacement policy, or disk scheduler makes its decisions, step by step.

---

## Table of Contents

1. [What This Project Does](#-what-this-project-does)
2. [Project Structure](#-project-structure)
3. [How a Simulation Runs](#-how-a-simulation-runs-step-by-step)
4. [Module 1 — CPU Scheduling](#-module-1--cpu-scheduling)
5. [Module 2 — Memory Management](#-module-2--memory-management)
6. [Module 3 — Page Replacement](#-module-3--page-replacement)
7. [Module 4 — Disk Scheduling](#-module-4--disk-scheduling)
8. [Shared Support Files](#-shared-support-files)
9. [Running It Locally](#-running-it-locally)

---

## What This Project Does

| Module | Algorithms Included |
|---|---|
| **CPU Scheduling** | FCFS, SJF, SRTF, Priority (Non-Preemptive & Preemptive), Round Robin, MLQ, MLFQ |
| **Memory Management** | First Fit, Best Fit, Worst Fit, Best Available Fit |
| **Page Replacement** | FIFO, Optimal, LRU, LRU Approximation, LFU |
| **Disk Scheduling** | FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK |

You type in your own input (processes, memory blocks, a reference string, a disk request queue), pick an algorithm, and the page shows you the resulting **Gantt chart**, **memory map**, **frame trace**, or **head-movement trace** — plus the relevant performance metrics (waiting time, hit ratio, total head movement, etc).

Every run is **stateless** — nothing is saved to a database. Send a request, get a result back, render it. Refreshing the page resets everything.

---

## 📁 Project Structure

```
os-visualizer/
│
├── app.py                          ← Flask app: defines every URL route
│
├── backend/
│   ├── algorithms/
│   │   ├── cpu_scheduling.py       ← All CPU scheduling algorithms
│   │   ├── memory_management.py    ← All memory allocation algorithms
│   │   ├── page_replacement.py     ← All page replacement algorithms
│   │   └── disk_scheduling.py      ← All disk scheduling algorithms
│   │
│   ├── models/
│   │   └── process.py              ← Data shapes (Process, MemoryBlock, etc.)
│   │                                  + abstract base classes for page/disk algos
│   │
│   └── utils/
│       ├── helpers.py              ← Shared logic: metrics, JSON building,
│       │                              memory split/free/coalesce
│       └── validators.py           ← Input-checking functions
│
└── frontend/
    ├── templates/
    │   ├── base.html               ← Shared page shell (navbar + CSS link)
    │   ├── index.html              ← Dashboard / landing page
    │   ├── cpu.html                ← CPU scheduling page
    │   ├── memory.html             ← Memory management page
    │   ├── page.html                ← Page replacement page
    │   └── disk.html               ← Disk scheduling page
    │
    └── static/
        └── css/style.css           ← All page styling
```

---

## How a Simulation Runs, Step by Step

Every one of the 4 modules follows the **exact same round trip**:

```
 1. Open a page (e.g. /cpu)
        ↓
 2. Flask renders the matching .html template
        ↓
 3. You fill in the form, click "Run"
        ↓
 4. JavaScript collects your inputs into JSON, sends via fetch()
    to a matching /simulate/... endpoint
        ↓
 5. app.py receives the POST, calls the matching algorithm
    function in backend/algorithms/
        ↓
 6. The algorithm runs the FULL simulation in one shot,
    returns one JSON object: { algorithm name, step trace, metrics }
        ↓
 7. JavaScript reads the JSON and builds the chart / map / table
```

> **Note:** The backend computes the entire simulation in a single function call — it doesn't animate step-by-step live. The "animation" you see is the frontend replaying the already-computed trace.

---

## 🟦 Module 1 — CPU Scheduling

📄 `backend/algorithms/cpu_scheduling.py`

**What it does:** Takes a list of processes (pid, arrival time, burst time, and priority/queue if needed) and decides the order they run on the CPU.

**How the code works:**

| Step | What happens |
|---|---|
| 1 | Raw input dicts are wrapped into `Process` objects (`models/process.py`) |
| 2 | A time-stepped loop advances `current_time`, deciding which process runs next according to that algorithm's rule |
| 3 | Each CPU burst gets appended to a `gantt` list as it happens |
| 4 | Once everyone's finished, `calculate_metrics()` computes waiting & turnaround time |
| 5 | `build_result()` standardizes the output shape so the frontend doesn't care which algorithm ran |

- **Non-preemptive** algorithms (FCFS, SJF, Priority) run a process to completion once started.
- **Preemptive** algorithms (SRTF, Priority Preemptive, RR, MLQ, MLFQ) use a queue/heap and can interrupt a running process every tick if something better arrives.
- The `ALGORITHMS` dictionary at the bottom routes a string like `"round_robin"` to its matching function.

**Frontend connection:** `cpu.html` POSTs to `/simulate/cpu`. `app.py` only forwards the `quantum` argument to algorithms that actually need it (Round Robin, MLQ), to avoid errors. The `gantt` array is drawn as colored blocks sized proportionally to burst duration.

---

## 🟩 Module 2 — Memory Management

📄 `backend/algorithms/memory_management.py`

**What it does:** Takes a list of memory block sizes and a queue of process requests, then decides which block each process gets allocated into.

**How the code works:**

| Algorithm | Rule |
|---|---|
| **First Fit** | Picks the first free block big enough |
| **Best Fit** | Picks the smallest free block big enough (minimizes wasted space) |
| **Worst Fit** | Picks the largest free block big enough (keeps remaining holes reusable) |
| **Best Available Fit** | Like Best Fit, but avoids leaving a leftover sliver smaller than a usable minimum |

- `initialize_memory()` builds the starting list of `MemoryBlock` objects, all marked free.
- `allocate_block()` does the actual placement — if the chosen block is bigger than the request, it **splits** the block: the process gets exactly what it asked for, and the leftover becomes a new free block. This is what lets the simulation show real fragmentation instead of silently wasting space.
- `free_block()` / `coalesce_free_blocks()` merge adjacent free blocks back together when memory is released.
- `build_memory_result()` reports total/used/free memory, utilization %, and a step-by-step allocation trace.

**Frontend connection:** `memory.html` POSTs to `/simulate/memory`. The `blocks` array is drawn as a horizontal strip of colored segments, sized proportionally, labeled with the occupying process or "Free."

---

## 🟨 Module 3 — Page Replacement

📄 `backend/algorithms/page_replacement.py`

**What it does:** Takes a *reference string* (a sequence of page numbers requested, e.g. `[7,0,1,2,0,3,...]`) and a fixed number of physical frames, then simulates which page gets evicted whenever a new page doesn't fit.

**How the code works:**

All five algorithms share one base class, `PageReplacementAlgorithm` (in `models/process.py`), which validates input and provides two shared helpers: `_step()` (records one reference-string step) and `_res()` (builds the final summary).

| Algorithm | Eviction rule |
|---|---|
| **FIFO** | Evict whichever page has been loaded the longest |
| **Optimal** | Evict whichever page won't be needed again for the longest time (requires looking ahead — theoretical best case) |
| **LRU** | Evict whichever page was used longest ago |
| **LRU Approximation** | "Clock"/second-chance: cycles through frames, giving each a second chance via a 1-bit flag before evicting |
| **LFU** | Evict whichever page has been used the fewest times |

Each step records: the page requested, the **full frame state** at that moment (positions stay stable, not compacted — so the table shows real movement between frames, not pages randomly jumping slots), hit/fault status, and which page (if any) got evicted.

**Frontend connection:** `page.html` lets you build a reference string (page numbers 0–9) and choose the frame count, then POSTs to `/simulate/page`. `app.py` translates the backend's internal field names (`pg`, `frm`, `status`, `replaced_page`) into what the JavaScript expects (`page`, `frames`, `hit`, `evicted`). Results render as colored pills (🔵 hit / 🔴 fault) plus a full frame table.

---

## 🟧 Module 4 — Disk Scheduling

📄 `backend/algorithms/disk_scheduling.py`

**What it does:** Takes a queue of disk track requests, a starting head position, the disk size, and a direction, then decides the visiting order and total head movement.

**How the code works:**

All six algorithms share one base class, `DiskSchedulingAlgorithm` (in `models/process.py`), which validates head/size/direction up front.

| Algorithm | Visiting rule |
|---|---|
| **FCFS** | Visits requests in the exact order given |
| **SSTF** | Always jumps to whichever remaining request is physically closest |
| **SCAN** | Sweeps one direction to the disk's end, reverses, sweeps back |
| **C-SCAN** | Sweeps one direction only; jumps straight back to the opposite end and continues the same direction |
| **LOOK** | Like SCAN, but reverses as soon as there are no more requests ahead — doesn't travel to the edge |
| **C-LOOK** | Like C-SCAN, but jumps back to the lowest pending request instead of all the way to track 0 |

Each head movement is recorded as a `DiskStep` (from track, to track, distance, running cumulative total) via the shared `_step()` helper. The final result reports the full visiting order, total head movement, and average movement per request.

**Frontend connection:** `disk.html` POSTs your request queue, head position, disk size, and direction to `/simulate/disk`. The `steps` array is drawn as a head-movement trace.

---

## 🛠️ Shared Support Files

| File | Purpose |
|---|---|
| `backend/models/process.py` | Every data shape used project-wide: `Process`, `MemoryBlock`, `MemoryRequest`, `PageStep`/`PageResult`, `DiskStep`/`DiskResult`, plus the two abstract base classes that page/disk algorithms inherit shared logic from |
| `backend/utils/helpers.py` | Reused logic across algorithms: waiting/turnaround time, merging Gantt entries, standardizing JSON output, and all memory block operations (initialize, allocate-with-split, free, coalesce) |
| `backend/utils/validators.py` | Small input-checking functions (`valid_int`, `valid_reference`, `valid_request_queue`, `valid_direction`) used by the page/disk base classes to reject bad input early with a clear error, instead of letting garbage data quietly corrupt a simulation |

---

## 🚀 Running It Locally

```bash
# 1. Install dependencies
pip install flask

# 2. From the project root, run the app
python app.py

# 3. Open your browser to:
http://127.0.0.1:5000/
```

Then use the dashboard to navigate to any of the four simulators. 🎉

---

<p align="center"><i>Built for our Operating Systems final project.</i></p>