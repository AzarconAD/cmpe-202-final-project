from flask import Flask, render_template, request, jsonify
import os
from backend.algorithms.cpu_scheduling import run_algorithm  # Interacts with your simulation routing module
from backend.algorithms.memory_management import run_memory_algorithm

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
        if algorithm == "round_robin":
            result = run_algorithm(algorithm, processes, quantum=quantum)
        elif algorithm == "mlq":
            result = run_algorithm(algorithm, processes, quantum_system=quantum)
        elif algorithm == "mlfq":
            result = run_algorithm(algorithm, processes)
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
        result = run_memory_algorithm(algorithm, block_sizes, requests_list)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
if __name__ == "__main__":
    app.run(debug=True, port=5000)