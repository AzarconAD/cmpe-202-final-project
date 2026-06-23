from flask import Flask, render_template, request, jsonify
import os
from backend.algorithms.cpu_scheduling import run_algorithm  # Interacts with your simulation routing module
from backend.algorithms.memory_management import run_memory_algorithm
from backend.algorithms.page_replacement import run_page_algorithm  # Import the page replacement module
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
        # Cast quantum safely in case it is sent as a string from the frontend
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

    try:
        # Protect block size lists mapping
        safe_blocks = [int(b) for b in block_sizes if str(b).isdigit() or isinstance(b, int)]
        result = run_memory_algorithm(algorithm, safe_blocks, requests_list)
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
        # Ensure values in reference string are treated as integers
        safe_reference = [int(x) for x in reference_string]
        
        result = run_page_algorithm(algorithm, safe_reference, frames_count)
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
    direction = data.get("direction", "right")

    try:
        initial_head = int(data.get("initial_head", 50))
        disk_size = int(data.get("disk_size", 200))
        
        # Cleanly stringify and filter queue inputs to protect against type cast failures
        safe_queue = [int(q) for q in request_queue if str(q).strip().lstrip('-').isdigit()]

        # Compute results from your operational layer
        raw_result = run_disk_algorithm(algorithm, safe_queue, initial_head, disk_size, direction)
        
        # Standardize properties to match exactly what your script fetches
        return jsonify({
            "total_seek_time": raw_result.get("move", raw_result.get("total_seek_time", 0)),
            "seek_sequence": raw_result.get("order", raw_result.get("seek_sequence", []))
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)