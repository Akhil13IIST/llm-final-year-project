"""Async verification and dashboard routes."""
from flask import request, jsonify, Blueprint
from datetime import datetime
import time
import queue
import threading
from collections import deque

async_bp = Blueprint('async', __name__)

# Shared state
verification_queue = queue.Queue()
verification_results = {}
verification_history = deque(maxlen=50)
active_verifications = {}
verifier = None

def init_async_routes(app_verifier):
    """Initialize routes with verifier instance."""
    global verifier
    verifier = app_verifier
    # Start background worker
    worker_thread = threading.Thread(target=verification_worker, daemon=True)
    worker_thread.start()

def verification_worker():
    """Background worker for processing verification requests."""
    while True:
        try:
            job = verification_queue.get(timeout=1)
            job_id = job['id']
            
            print(f"[WORKER] Starting verification job {job_id}...")
            active_verifications[job_id] = {
                'status': 'running',
                'started_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'task_name': job.get('task_name', 'Unknown'),
                'language': job.get('language', 'ada')
            }
            
            # Run verification
            result = verifier.verify_uppaal_async(
                job['xml_content'],
                job['task_name'],
                job_id,
                job.get('task_info'),
                job.get('source_code'),
                job.get('language', 'ada')
            )
            result.setdefault('completed_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            result['job_id'] = job_id
            result['task_name'] = job.get('task_name', 'Unknown')
            
            # Store result
            verification_results[job_id] = result
            verification_history.append({
                'job_id': job_id,
                'task_name': job['task_name'],
                'success': result.get('success', False),
                'timestamp': result.get('completed_at'),
                'execution_time': result.get('execution_time', 0),
                'properties_verified': result.get('properties_verified', 0),
                'properties_failed': result.get('properties_failed', 0)
            })
            
            # Remove from active
            if job_id in active_verifications:
                del active_verifications[job_id]
            
            verification_queue.task_done()
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[WORKER ERROR] {e}")
            if 'job_id' in locals():
                active_verifications.pop(job_id, None)

def snapshot_queue_details():
    """Collect a lightweight view of queued jobs without mutating the queue."""
    queued_jobs = []
    with verification_queue.mutex:
        queued_jobs = list(verification_queue.queue)
    return [
        {
            'job_id': job.get('id', 'unknown'),
            'task_name': job.get('task_name', 'PendingTask'),
            'language': job.get('language', 'ada')
        }
        for job in queued_jobs
    ]

@async_bp.route('/verify_async', methods=['POST'])
def verify_async():
    """Submit verification job to queue."""
    try:
        data = request.json
        ada_code = data.get('ada_code', '')
        language = data.get('language', 'ada')
        
        if not ada_code.strip():
            return jsonify({'error': 'No code provided'}), 400
        
        # Extract and generate XML
        task_info = verifier.extract_from_code(ada_code, language)
        xml_content, properties_list = verifier.generate_uppaal_xml(task_info)
        
        # Generate job ID
        job_id = f"job_{int(time.time() * 1000)}"
        
        # Determine task name
        if isinstance(task_info, dict) and task_info.get('multi_task'):
            task_names = [t['task_name'] for t in task_info['tasks']]
            file_task_name = "_".join(task_names[:3])
        else:
            file_task_name = task_info['task_name']
        
        # Submit to queue
        verification_queue.put({
            'id': job_id,
            'xml_content': xml_content,
            'task_name': file_task_name,
            'task_info': task_info,
            'source_code': ada_code,
            'language': language
        })
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'message': 'Verification job submitted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@async_bp.route('/verify_status/<job_id>', methods=['GET'])
def verify_status(job_id):
    """Check verification job status."""
    if job_id in verification_results:
        return jsonify({
            'status': 'completed',
            'result': verification_results[job_id]
        })
    elif job_id in active_verifications:
        return jsonify({
            'status': active_verifications[job_id]['status'],
            'info': active_verifications[job_id]
        })
    else:
        return jsonify({
            'status': 'not_found',
            'message': 'Job ID not found'
        }), 404

@async_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Verification dashboard endpoint."""
    active_details = [
        {
            'job_id': job_id,
            **info
        }
        for job_id, info in active_verifications.items()
    ]
    queued_details = snapshot_queue_details()
    return jsonify({
        'active_jobs': len([j for j in active_verifications.values() if j.get('status') == 'running']),
        'queued_jobs': len(queued_details),
        'completed_jobs': len(verification_results),
        'recent_history': list(verification_history)[-10:],
        'success_rate': calculate_success_rate(),
        'avg_execution_time': calculate_avg_time(),
        'active_jobs_detail': active_details,
        'queued_jobs_detail': queued_details
    })

@async_bp.route('/metrics', methods=['GET'])
def metrics():
    """Comprehensive benchmark metrics endpoint."""
    history_list = list(verification_history)
    
    first_pass = [h for h in history_list if '_repair' not in h.get('task_name', '')]
    repair_attempts = [h for h in history_list if '_repair' in h.get('task_name', '')]
    
    def calc_rate(items):
        if not items:
            return 0.0
        successes = sum(1 for h in items if h.get('success'))
        return round((successes / len(items)) * 100, 1)
    
    def calc_avg_time(items):
        if not items:
            return 0.0
        times = [h.get('execution_time', 0) for h in items]
        return round(sum(times) / len(times), 2)
    
    return jsonify({
        'total_verifications': len(history_list),
        'first_pass_success_rate': calc_rate(first_pass),
        'repair_convergence_rate': calc_rate(repair_attempts),
        'avg_execution_time': calc_avg_time(history_list),
        'recent_history': history_list[-20:]
    })

def calculate_success_rate():
    """Calculate overall success rate."""
    if not verification_history:
        return 0.0
    successes = sum(1 for h in verification_history if h.get('success'))
    return round((successes / len(verification_history)) * 100, 1)

def calculate_avg_time():
    """Calculate average execution time."""
    if not verification_history:
        return 0.0
    times = [h.get('execution_time', 0) for h in verification_history]
    return round(sum(times) / len(times), 2)
