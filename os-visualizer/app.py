from flask import Flask, render_template, request, jsonify
import os
from backend.algorithms.cpu_scheduling import run_algorithm
from backend.algorithms.memory_management import run_memory_algorithm
from backend.utils.helpers import simulate_memory_scheduling
from backend.algorithms.page_replacement import run_page_algorithm
from backend.algorithms.disk_scheduling import run_disk_algorithm

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/cpu")
def cpu():
    return render_template("cpu.html")

@app.route("/simulate/cpu", methods=["POST"])
def simulate_cpu():
    data = request.get_json() or {}
    algorithm = data.get("algorithm", "fcfs")
    processes = data.get("processes", [])
    quantum = data.get("quantum", 4)

    try:
        quantum_val = int(quantum) if quantum is not None else 4

        if algorithm == "round_robin":
            result = run_algorithm(algorithm, processes, quantum=quantum_val)
        elif algorithm == "mlq":
            result = run_algorithm(algorithm, processes, quantum_system=quantum_val)
        else:
            result = run_algorithm(algorithm, processes)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/memory")
def memory():
    return render_template("memory.html")

@app.route("/simulate/memory", methods=["POST"])
def simulate_memory():
    data = request.get_json() or {}
    algorithm = data.get("algorithm", "first_fit")
    block_sizes = data.get("block_sizes", [])
    requests_list = data.get("requests", [])
    compaction = data.get("compaction", False)

    try:
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
        result = run_memory_algorithm(algorithm, safe_blocks, requests_list, compaction=bool(compaction))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/simulate/memory_scheduling", methods=["POST"])
def simulate_memory_scheduling_route():
    data = request.get_json() or {}
    processes = data.get("processes", [])
    total_memory = data.get("total_memory", 60)
    algorithm = data.get("algorithm", "first_fit")
    compaction = data.get("compaction", False)
    cpu_algorithm = data.get("cpu_algorithm", "fcfs")
    cpu_quantum = data.get("cpu_quantum", 4)

    try:
        total_memory = int(total_memory)
        safe_processes = []
        for p in processes:
            try:
                entry = {
                    'pid': str(p['pid']),
                    'arrival': int(p['arrival']),
                    'burst': max(1, int(p['burst'])),
                    'memory': max(1, int(p['memory'])),
                }
                if 'priority' in p:
                    try:
                        entry['priority'] = int(p['priority'])
                    except Exception:
                        entry['priority'] = 0
                safe_processes.append(entry)
            except (KeyError, TypeError, ValueError):
                continue

        try:
            cpu_quantum = int(cpu_quantum)
        except Exception:
            cpu_quantum = 4

        result = simulate_memory_scheduling(
            safe_processes, total_memory, algorithm, bool(compaction), cpu_algorithm=cpu_algorithm, cpu_quantum=cpu_quantum
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/page-replacement")
def page_replacement():
    return render_template("page.html")

@app.route("/simulate/page", methods=["POST"])
def simulate_page():
    data = request.get_json() or {}

    algorithm = data.get("algorithm", "fifo")
    reference_string = data.get("reference_string", [])

    try:
        frames_count = int(data.get("frames", 3))
        safe_reference = [int(x) for x in reference_string]

        result = run_page_algorithm(algorithm, safe_reference, frames_count)

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

@app.route("/disk")
def disk():
    return render_template("disk.html")

@app.route("/simulate/disk", methods=["POST"])
def simulate_disk():
    data = request.get_json() or {}
    algorithm = data.get("algorithm", "fcfs")
    request_queue = data.get("request_queue", [])
    direction = data.get("direction", "left")

    try:
        initial_head = int(data.get("initial_head", 50))
        disk_size = int(data.get("disk_size", 200))

        # Validate input
        if disk_size <= 0:
            raise ValueError("Disk size must be positive.")
        if initial_head < 0 or initial_head >= disk_size:
            raise ValueError(f"Head position must be between 0 and {disk_size - 1}.")

        safe_queue = [int(q) for q in request_queue if str(q).strip() != ""]
        if not safe_queue:
            raise ValueError("Request queue cannot be empty.")

        result_dict = run_disk_algorithm(algorithm, safe_queue, initial_head, disk_size, direction)

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

if __name__ == "__main__":
    app.run(debug=True, port=5000)