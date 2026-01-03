"""
Simple Flask API server for Job Aggregator UI.
Run locally to serve the dashboard and API endpoints.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import Config
from src.database.connection import DatabaseConnection
from src.database.operations import JobOperations

app = Flask(__name__, static_folder='../ui')
CORS(app)

# Global database connection
db_conn = None
job_ops = None


def get_db():
    """Get or initialize database connection."""
    global db_conn, job_ops
    
    if job_ops is None:
        try:
            config = Config()
            db_conn = DatabaseConnection(config.mongodb_uri, config.mongodb_database)
            db = db_conn.connect()
            job_ops = JobOperations(db)
        except Exception as e:
            print(f"Database connection failed: {e}")
            return None
    
    return job_ops


@app.route('/')
def index():
    """Serve the main UI."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)


@app.route('/api/jobs')
def get_jobs():
    """Get jobs from database."""
    ops = get_db()
    
    if ops is None:
        # Fallback to JSON file
        json_path = Path(app.static_folder) / 'jobs_data.json'
        if json_path.exists():
            with open(json_path) as f:
                return jsonify(json.load(f))
        return jsonify({'jobs': [], 'stats': {}, 'error': 'Database not available'})
    
    hours = request.args.get('hours', 24, type=int)
    
    try:
        jobs = ops.get_all_jobs_for_ui(hours=hours)
        stats = ops.get_stats()
        
        return jsonify({
            'jobs': jobs,
            'stats': stats,
            'generated_at': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'jobs': [], 'stats': {}, 'error': str(e)})


@app.route('/api/stats')
def get_stats():
    """Get database statistics."""
    ops = get_db()
    
    if ops is None:
        return jsonify({'error': 'Database not available'})
    
    try:
        stats = ops.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    ops = get_db()
    
    return jsonify({
        'status': 'healthy' if ops else 'degraded',
        'database': 'connected' if ops else 'disconnected',
        'timestamp': datetime.utcnow().isoformat()
    })


def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask development server."""
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║           JOB AGGREGATOR - LOCAL UI SERVER                ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║   Dashboard: http://{host}:{port}                         ║
║   API:       http://{host}:{port}/api/jobs                ║
║                                                           ║
║   Press Ctrl+C to stop the server                         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)




