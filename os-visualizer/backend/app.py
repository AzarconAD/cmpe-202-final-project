from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from algorithms.cpu_scheduling import run_algorithm

app = Flask(__name__, 
            template_folder='/frontend/templates',
            static_folder='/frontend/static')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cpu/schedule', methods=['POST'])
def cpu_schedule():
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'algorithm' not in data or 'processes' not in data:
            return jsonify({'error': 'Missing algorithm or processes'}), 400
        
        algorithm = data['algorithm']
        processes = data['processes']
        
        # Extract optional parameters
        quantum = data.get('quantum', 4)
        aging_interval = data.get('aging_interval', 5)
        time_quantums = data.get('time_quantums', [4, 8, 16])
        quantum_system = data.get('quantum_system', 4)
        
        # Run the algorithm
        result = run_algorithm(
            algorithm=algorithm,
            processes=processes,
            quantum=quantum,
            aging_interval=aging_interval,
            time_quantums=time_quantums,
            quantum_system=quantum_system
        )
        
        return jsonify(result)
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/algorithms', methods=['GET'])
def list_algorithms():
    """Return list of available algorithms"""
    return jsonify({
        'algorithms': [
            'fcfs',
            'sjf',
            'sjf_preemptive',
            'priority',
            'priority_preemptive',
            'round_robin',
            'mlq',
            'mlfq'
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)