from flask import Flask, render_template, request, jsonify
import os

# Import the algorithm runners from the backend modules.
from backend.algorithms.cpu_scheduling import run_algorithm
from backend.algorithms.memory_management import run_memory_algorithm
from backend.utils.helpers import simulate_memory_scheduling
from backend.algorithms.page_replacement import run_page_algorithm
from backend.algorithms.disk_scheduling import run_disk_algorithm

# ------------------------------------------------------------------
# Flask App Configuration
# ------------------------------------------------------------------
app = Flask(
    __name__,
    template_folder="frontend/templates",   # HTML templates live here
    static_folder="frontend/static"         # CSS, JS, images live here
)

# ------------------------------------------------------------------
# Main Pages (GET routes)
# ------------------------------------------------------------------

@app.route("/")
def home():
    """Render the dashboard / home page."""
    return render_template("index.html")

@app.route("/cpu")
def cpu():
    """Render the CPU scheduling simulator page."""
    return render_template("cpu.html")

@app.route("/memory")
def memory():
    """Render the memory management simulator page."""
    return render_template("memory.html")

@app.route("/page-replacement")
def page_replacement():
    """Render the page replacement simulator page."""
    return render_template("page.html")

@app.route("/disk")
def disk():
    """Render the disk scheduling simulator page."""
    return render_template("disk.html")

# ------------------------------------------------------------------
# Simulation Endpoints (POST routes)
# ------------------------------------------------------------------

@app.route("/simulate/cpu", methods=["POST"])
def simulate_cpu():
    """
    Receive a CPU scheduling simulation request.
    Expects JSON: { algorithm, processes, quantum }.
    Runs the requested algorithm and returns the result as JSON.
    """
    data = request.get_json() or {}
    algorithm = data.get("algorithm", "fcfs")
    processes = data.get("processes", [])
    quantum = data.get("quantum", 4)

    try:
        quantum_val = int(quantum) if quantum is not None else 4

        # Round Robin and MLQ need the quantum value; others don't.
        if algorithm == "round_robin":
            result = run_algorithm(algorithm, processes, quantum=quantum_val)
        elif algorithm == "mlq":
            result = run_algorithm(algorithm, processes, quantum_system=quantum_val)
        else:
            result = run_algorithm(algorithm, processes)

        return jsonify(result)

    except Exception as e:
        # Return a 400 error with the exception message.
        return jsonify({"error": str(e)}), 400


@app.route("/simulate/memory", methods=["POST"])
def simulate_memory():
    """
    Run a static (MFT) memory allocation simulation.
    Expects JSON: { algorithm, block_sizes, requests, compaction }.
    """
    data = request.get_json() or {}
    algorithm = data.get("algorithm", "first_fit")
    block_sizes = data.get("block_sizes", [])
    requests_list = data.get("requests", [])
    compaction = data.get("compaction", False)

    try:
        # Validate and clean block sizes: keep only positive integers.
        safe_blocks = []
        for b in block_sizes:
            if isinstance(b, bool):
                continue
            try:
                b_int = int(b)
                if b_int > 0:
                    safe_blocks.append(b_int)
            except (TypeError, ValueError):
                continue

        # Run the selected memory allocation algorithm.
        result = run_memory_algorithm(
            algorithm, safe_blocks, requests_list, compaction=bool(compaction)
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/simulate/memory_scheduling", methods=["POST"])
def simulate_memory_scheduling_route():
    """
    Run a dynamic (MVT) memory + admission scheduling simulation.
    Expects JSON: { processes, total_memory, algorithm, compaction, cpu_algorithm, cpu_quantum }.
    The processes list contains { pid, arrival, burst, memory, (priority) }.
    """
    data = request.get_json() or {}
    processes = data.get("processes", [])
    total_memory = data.get("total_memory", 60)
    algorithm = data.get("algorithm", "first_fit")
    compaction = data.get("compaction", False)
    cpu_algorithm = data.get("cpu_algorithm", "fcfs")
    cpu_quantum = data.get("cpu_quantum", 4)

    try:
        total_memory = int(total_memory)

        # Build a safe list of process dictionaries.
        safe_processes = []
        for p in processes:
            try:
                entry = {
                    'pid': str(p['pid']),
                    'arrival': int(p['arrival']),
                    'burst': max(1, int(p['burst'])),
                    'memory': max(1, int(p['memory'])),
                }
                # Include priority only if it was sent.
                if 'priority' in p:
                    entry['priority'] = int(p['priority']) if p['priority'] else 0
                safe_processes.append(entry)
            except (KeyError, TypeError, ValueError):
                # Skip malformed process entries.
                continue

        # Ensure quantum is an integer.
        cpu_quantum = int(cpu_quantum) if cpu_quantum else 4

        # Call the core simulation function from helpers.
        result = simulate_memory_scheduling(
            safe_processes,
            total_memory,
            algorithm,
            bool(compaction),
            cpu_algorithm=cpu_algorithm,
            cpu_quantum=cpu_quantum
        )
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/simulate/page", methods=["POST"])
def simulate_page():
    """
    Run a page replacement simulation.
    Expects JSON: { algorithm, reference_string, frames }.
    Transforms the backend result into the format expected by the frontend.
    """
    data = request.get_json() or {}
    algorithm = data.get("algorithm", "fifo")
    reference_string = data.get("reference_string", [])
    frames_count = data.get("frames", 3)

    try:
        frames_count = int(frames_count)
        safe_reference = [int(x) for x in reference_string if str(x).strip() != ""]

        # Run the page replacement algorithm.
        result = run_page_algorithm(algorithm, safe_reference, frames_count)

        # The backend uses keys 'pg', 'frm', 'status', 'replaced_page'.
        # The frontend expects 'page', 'frames', 'hit', 'evicted'.
        result["steps"] = [
            {
                "page": s["pg"],
                "frames": s["frm"],
                "hit": s["status"] == "Hit",
                "evicted": s["replaced_page"],
            }
            for s in result["steps"]
        ]

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/simulate/disk", methods=["POST"])
def simulate_disk():
    """
    Run a disk scheduling simulation.
    Expects JSON: { algorithm, request_queue, initial_head, disk_size, direction }.
    """
    data = request.get_json() or {}
    algorithm = data.get("algorithm", "fcfs")
    request_queue = data.get("request_queue", [])
    direction = data.get("direction", "left")
    initial_head = data.get("initial_head", 50)
    disk_size = data.get("disk_size", 200)

    try:
        initial_head = int(initial_head)
        disk_size = int(disk_size)

        # Validate disk size and head position.
        if disk_size <= 0:
            raise ValueError("Disk size must be positive.")
        if initial_head < 0 or initial_head >= disk_size:
            raise ValueError(f"Head position must be between 0 and {disk_size - 1}.")

        # Parse and clean the request queue.
        safe_queue = [int(q) for q in request_queue if str(q).strip() != ""]
        if not safe_queue:
            raise ValueError("Request queue cannot be empty.")

        # Call the disk scheduling algorithm.
        result_dict = run_disk_algorithm(
            algorithm, safe_queue, initial_head, disk_size, direction
        )

        # The frontend expects 'total_seek_time' and 'seek_sequence' aliases.
        return jsonify({
            "order": result_dict.get("order", []),
            "move": result_dict.get("move", 0),
            "avg": result_dict.get("avg", 0.0),
            "steps": result_dict.get("steps", []),
            "total_seek_time": result_dict.get("move", 0),
            "seek_sequence": result_dict.get("order", []),
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# ------------------------------------------------------------------
# Run the Flask development server
# ------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)