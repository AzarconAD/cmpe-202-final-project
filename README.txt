================================================================================
 OS VISUALIZER - Operating System Algorithm Simulator
 Final Project - Operating Systems
================================================================================

WHAT THIS PROJECT IS
--------------------------------------------------------------------------------
A web app that lets you visually run and compare classic Operating System
algorithms across four topics:

  1. CPU Scheduling      (FCFS, SJF, SRTF, Priority, RR, MLQ, MLFQ)
  2. Memory Management   (First Fit, Best Fit, Worst Fit, Best Available Fit)
  3. Page Replacement    (FIFO, Optimal, LRU, LRU Approximation, LFU)
  4. Disk Scheduling     (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK)

You type in your own input (processes, memory blocks, a reference string, a
disk request queue), pick an algorithm, and the page shows you the resulting
Gantt chart / memory map / frame trace / head-movement trace, plus the
relevant performance metrics (waiting time, hit ratio, total head movement,
etc).

--------------------------------------------------------------------------------
HOW THE PROJECT IS STRUCTURED
--------------------------------------------------------------------------------

os-visualizer/
|
|-- app.py                          <- Flask app: defines every URL route
|
|-- backend/
|   |-- algorithms/
|   |   |-- cpu_scheduling.py       <- All CPU scheduling algorithms
|   |   |-- memory_management.py    <- All memory allocation algorithms
|   |   |-- page_replacement.py     <- All page replacement algorithms
|   |   |-- disk_scheduling.py      <- All disk scheduling algorithms
|   |
|   |-- models/
|   |   |-- process.py              <- Data shapes (Process, MemoryBlock, etc)
|   |                                  + the abstract base classes that
|   |                                  page/disk algorithms inherit from
|   |
|   |-- utils/
|       |-- helpers.py              <- Shared logic: metrics, JSON building,
|       |                              memory split/free/coalesce
|       |-- validators.py           <- Input-checking functions (catches bad
|                                      types/values before they reach an
|                                      algorithm)
|
|-- frontend/
    |-- templates/
    |   |-- base.html               <- Shared page shell (navbar + CSS link)
    |   |-- index.html              <- Dashboard / landing page
    |   |-- cpu.html                <- CPU scheduling page (form + chart)
    |   |-- memory.html             <- Memory management page
    |   |-- page.html               <- Page replacement page
    |   |-- disk.html               <- Disk scheduling page
    |
    |-- static/
        |-- css/style.css           <- All page styling

--------------------------------------------------------------------------------
HOW A SIMULATION ACTUALLY RUNS, STEP BY STEP
--------------------------------------------------------------------------------

Every one of the 4 modules follows the exact same round trip:

  1. You open a page (e.g. /cpu) -> Flask renders the matching .html template.
  2. You fill in the form and click "Run" / "Compute".
  3. The page's JavaScript collects your inputs into a JSON object and sends
     it with fetch() to a matching /simulate/... endpoint (e.g. /simulate/cpu).
  4. app.py receives that POST request, pulls out the fields it needs, and
     calls the matching algorithm function in backend/algorithms/.
  5. The algorithm runs the full simulation in one shot (not animated step by
     step on the backend) and returns a single JSON-shaped dictionary
     containing: the algorithm name, a step-by-step trace, and the summary
     metrics.
  6. Flask sends that JSON back to the browser.
  7. The page's JavaScript reads the JSON and builds the visualization:
     Gantt bars, colored memory blocks, a frame matrix table, or a
     disk-head movement trace.

Nothing is stored in a database - every run is stateless. Send a request,
get a JSON result back, render it. Refreshing the page resets everything.

--------------------------------------------------------------------------------
MODULE 1: CPU SCHEDULING  (backend/algorithms/cpu_scheduling.py)
--------------------------------------------------------------------------------
WHAT IT DOES:
  Takes a list of processes (pid, arrival time, burst time, and priority/
  queue if needed) and decides the order they run on the CPU.

HOW THE CODE WORKS:
  - Each algorithm (fcfs, sjf, sjf_preemptive, priority, priority_preemptive,
    round_robin, mlq, mlfq) is its own function that:
      1. Wraps the raw input dicts into Process objects (models/process.py).
      2. Runs a time-stepped simulation loop, advancing a `current_time`
         clock and deciding which process gets the CPU next according to
         that algorithm's rule (shortest burst first, best priority first,
         time-slice rotation, etc).
      3. Appends each CPU burst to a `gantt` list as it happens.
      4. Once every process has finished, calls calculate_metrics() to work
         out each process's waiting time and turnaround time.
      5. Returns everything through build_result(), which standardizes the
         output shape (gantt, processes, avg_waiting, avg_turnaround) so the
         frontend chart code doesn't need to care which algorithm ran.
  - The non-preemptive algorithms run a process to completion once it starts.
  - The preemptive algorithms (SRTF, Priority Preemptive, RR, MLQ, MLFQ) use
    a queue/heap and can interrupt a running process every time tick if a
    better-priority/shorter process becomes available.
  - The ALGORITHMS dictionary at the bottom is a simple router: given a
    string like "round_robin", it calls the matching function.

HOW IT CONNECTS TO THE FRONTEND:
  cpu.html lets you add process rows and pick an algorithm from a dropdown.
  On submit, it POSTs to /simulate/cpu. app.py only forwards the extra
  `quantum` argument to algorithms that actually need it (Round Robin, MLQ)
  to avoid errors. The JSON response's `gantt` array is drawn as colored
  blocks sized proportionally to each burst's duration.

--------------------------------------------------------------------------------
MODULE 2: MEMORY MANAGEMENT  (backend/algorithms/memory_management.py)
--------------------------------------------------------------------------------
WHAT IT DOES:
  Takes a list of memory block sizes (simulating fixed physical memory) and
  a queue of process requests (process id + size needed), then decides
  which memory block each process gets allocated into.

HOW THE CODE WORKS:
  - initialize_memory() (in utils/helpers.py) builds the starting list of
    MemoryBlock objects from your block sizes, all marked free.
  - Each algorithm (first_fit, best_fit, worst_fit, best_available_fit) loops
    through the requests one at a time and searches the free blocks using a
    different rule:
      first_fit          -> picks the first free block big enough
      best_fit           -> picks the smallest free block big enough
                             (minimizes wasted space per allocation)
      worst_fit          -> picks the largest free block big enough
                             (keeps remaining holes large and reusable)
      best_available_fit -> like best_fit, but avoids leaving a leftover
                             sliver smaller than a minimum useful size
  - allocate_block() (in utils/helpers.py) does the actual placement: if the
    chosen block is bigger than the request, it SPLITS the block - the
    process gets a block of exactly the size it asked for, and the leftover
    space becomes a brand new free block right after it. This is what lets
    the simulation show realistic fragmentation over time instead of
    wasting memory silently.
  - free_block() / coalesce_free_blocks() exist so that if a process's
    memory is released, adjacent free blocks automatically merge back
    together into one larger usable block.
  - Every algorithm function returns its result through
    build_memory_result(), which reports total/used/free memory, percentage
    utilization, and a step-by-step trace of each allocation decision.

HOW IT CONNECTS TO THE FRONTEND:
  memory.html lets you add block sizes and a request queue, then POSTs to
  /simulate/memory. The response's `blocks` array is drawn as a horizontal
  strip of colored segments (one per memory block), sized proportionally,
  labeled with whichever process occupies them or "Free" if unallocated.

--------------------------------------------------------------------------------
MODULE 3: PAGE REPLACEMENT  (backend/algorithms/page_replacement.py)
--------------------------------------------------------------------------------
WHAT IT DOES:
  Takes a "reference string" (a sequence of page numbers a program asks for,
  e.g. [7,0,1,2,0,3,...]) and a fixed number of physical memory frames, then
  simulates which page gets evicted every time a new page doesn't fit.

HOW THE CODE WORKS:
  - All five algorithms (FIFO, Optimal, LRU, LRU Approximation/Second-Chance,
    LFU) share the same base class, PageReplacementAlgorithm, defined in
    models/process.py. That base class validates the input and provides two
    shared helper methods: _step() (records one reference-string step) and
    _res() (builds the final summary).
  - Each algorithm keeps its own frame array (frm) representing what's
    currently loaded, and walks through the reference string one page at a
    time:
      - If the page is already in a frame -> it's a HIT.
      - If not -> it's a FAULT. If there's a free frame slot, fill it.
        Otherwise, evict a page chosen by that algorithm's specific rule:
          FIFO       -> evict whichever page has been loaded the longest
          Optimal    -> evict whichever loaded page won't be needed again
                        for the longest time (the theoretical best case,
                        requires looking ahead in the reference string)
          LRU        -> evict whichever loaded page was used longest ago
          LRU Approx -> "clock"/second-chance algorithm: cycles through
                        frames giving each a second chance via a 1-bit flag
                        before evicting it
          LFU        -> evict whichever loaded page has been used the
                        fewest times
  - Every step is recorded with the page requested, the full frame state at
    that moment (frame positions are kept stable, not compacted, so the
    visualization shows real movement between frames rather than pages
    randomly jumping slots), whether it was a hit or fault, and which page
    (if any) got evicted.
  - At the end, hit count, fault count, and hit/fault ratios are calculated.

HOW IT CONNECTS TO THE FRONTEND:
  page.html lets you build a reference string by appending page numbers
  (0-9) and choose the number of frames, then POSTs to /simulate/page.
  app.py translates the backend's internal field names (pg, frm, status,
  replaced_page) into the names the page's JavaScript expects (page, frames,
  hit, evicted) before sending the response back. The result is rendered as
  a colored pill for each step (blue = hit, red = fault) and a full frame
  table showing exactly what's sitting in each frame at every step.

--------------------------------------------------------------------------------
MODULE 4: DISK SCHEDULING  (backend/algorithms/disk_scheduling.py)
--------------------------------------------------------------------------------
WHAT IT DOES:
  Takes a queue of disk track requests, a starting head position, the total
  disk size, and a direction, then decides the order the disk arm visits
  those tracks and how far it has to physically move overall.

HOW THE CODE WORKS:
  - All six algorithms (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK) share a base
    class, DiskSchedulingAlgorithm, also in models/process.py, which
    validates the head/size/direction inputs up front (e.g. rejecting a
    head position outside the disk's range).
  - Each algorithm decides the visiting order differently:
      FCFS    -> visits requests in the exact order they were given
      SSTF    -> always jumps to whichever remaining request is physically
                 closest to the current head position
      SCAN    -> sweeps in one direction to the end of the disk, then
                 reverses and sweeps back, picking up requests along the way
      C-SCAN  -> sweeps in one direction only; once it hits the end, it
                 jumps straight back to the opposite end and continues the
                 same direction (so all sweeps are one-way)
      LOOK    -> like SCAN, but doesn't bother going all the way to the
                 disk's edge - it reverses as soon as there are no more
                 requests ahead of it
      C-LOOK  -> like C-SCAN, but doesn't travel to the edge either - it
                 jumps back to the lowest pending request instead of track 0
  - Every algorithm records each individual head movement as a DiskStep
    (from track, to track, distance moved, and the running cumulative total)
    via the shared _step() helper.
  - The final result (built via _res()) reports the full visiting order, the
    total head movement, and the average movement per request.

HOW IT CONNECTS TO THE FRONTEND:
  disk.html POSTs your request queue, head position, disk size, and
  direction to /simulate/disk, and the response's `steps` array is drawn as
  a head-movement trace showing exactly how far the disk arm travels at
  each stage of the simulation.

--------------------------------------------------------------------------------
SHARED SUPPORT FILES
--------------------------------------------------------------------------------
backend/models/process.py
  Defines every data shape used across the project: Process, MemoryBlock,
  MemoryRequest, PageStep/PageResult, DiskStep/DiskResult, plus the two
  abstract base classes (PageReplacementAlgorithm, DiskSchedulingAlgorithm)
  that the page and disk algorithms inherit shared step-building logic from.

backend/utils/helpers.py
  Holds logic that's reused across multiple algorithms: calculating waiting/
  turnaround time, merging consecutive Gantt entries, standardizing JSON
  output shape, and all the memory block operations (initialize, allocate
  with splitting, free, coalesce).

backend/utils/validators.py
  Small standalone input-checking functions (valid_int, valid_reference,
  valid_request_queue, valid_direction) used by the page/disk base classes
  to reject bad input early with a clear error message, instead of letting
  garbage data quietly corrupt a simulation.

--------------------------------------------------------------------------------
HOW TO RUN IT LOCALLY
--------------------------------------------------------------------------------
  1. Install dependencies:
       pip install flask flask-cors

  2. From the project root, run:
       python app.py

  3. Open a browser to:
       http://127.0.0.1:5000/

  4. Use the dashboard to navigate to any of the four simulators.

================================================================================