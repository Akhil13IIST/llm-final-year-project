"""
Routes for Autonomous Verification Pipeline
POST /autonomous_verify - Run full 9-stage autonomous pipeline
"""
from flask import Blueprint, request, jsonify
import traceback
import json

from core.autonomous_pipeline import AutonomousPipeline
import config

autonomous_bp = Blueprint('autonomous', __name__)

# Initialize pipeline
pipeline = None

def init_autonomous_routes(verifyta_path=None, use_llm=True):
    """Initialize autonomous pipeline with UPPAAL path and LLM option"""
    global pipeline
    pipeline = AutonomousPipeline(
        verifyta_path=verifyta_path or config.UPPAAL_PATH,
        use_llm=use_llm
    )

@autonomous_bp.route('/autonomous_verify', methods=['POST'])
def autonomous_verify():
    """
    Autonomous verification endpoint
    
    Accepts JSON or INI specification
    Returns complete pipeline results with verified code
    
    Example JSON input:
    {
        "specification": "...",  // JSON string or INI text
        "format": "json",  // or "ini"
        "use_llm": true  // Optional: enable LLM property generation
    }
    """
    try:
        data = request.json
        spec_input = data.get('specification') or data.get('spec')
        input_format = data.get('format', 'json')
        use_llm = data.get('use_llm', True)  # Default: use LLM if available
        
        # Reinitialize pipeline with LLM setting if different
        global pipeline
        if pipeline is None or (hasattr(pipeline, 'use_llm') and pipeline.use_llm != use_llm):
            pipeline = AutonomousPipeline(
                verifyta_path=config.UPPAAL_PATH,
                use_llm=use_llm
            )
        
        # Handle different input formats
        if isinstance(spec_input, dict):
            spec_input = json.dumps(spec_input)
        elif isinstance(spec_input, str):
            pass
        else:
            return jsonify({
                'error': 'Invalid specification format',
                'expected': 'JSON object or string'
            }), 400
        
        # Run autonomous pipeline
        result = pipeline.run_pipeline(spec_input, input_format)
        
        if result['success']:
            return jsonify({
                'success': True,
                'converged': result['converged'],
                'iterations': result['iterations'],
                'verified_code': {
                    'haskell': result['verified_haskell_code'],
                    'uppaal_xml': result['uppaal_xml']
                },
                'final_specification': result['final_spec'],
                'properties': result['properties'],
                'verification_results': result['verification_results'],
                'sdd': result['sdd_document'],
                'stage_history': result['stage_history']
            })
        else:
            return jsonify({
                'success': False,
                'converged': False,
                'iterations': result['iterations'],
                'error': result.get('error', 'Pipeline failed to converge'),
                'stage_history': result['stage_history']
            }), 500
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@autonomous_bp.route('/autonomous_verify/example', methods=['GET'])
def get_example_spec():
    """Return example specifications for testing"""
    examples = {
        'json_simple': {
            'format': 'json',
            'spec': {
                'tasks': [
                    {
                        'name': 'NavigationTask',
                        'period_ms': 20,
                        'execution_ms': 12,
                        'deadline_ms': 15,
                        'priority': 1
                    },
                    {
                        'name': 'SensorTask',
                        'period_ms': 50,
                        'execution_ms': 30,
                        'deadline_ms': 40,
                        'priority': 2
                    }
                ]
            }
        },
        'json_complex': {
            'format': 'json',
            'spec': {
                'tasks': [
                    {
                        'name': 'HighPriorityControl',
                        'period_ms': 10,
                        'execution_ms': 6,
                        'deadline_ms': 8,
                        'priority': 1
                    },
                    {
                        'name': 'NavigationTask',
                        'period_ms': 20,
                        'execution_ms': 12,
                        'deadline_ms': 15,
                        'priority': 2
                    },
                    {
                        'name': 'SensorTask',
                        'period_ms': 50,
                        'execution_ms': 30,
                        'deadline_ms': 40,
                        'priority': 3
                    },
                    {
                        'name': 'LoggerTask',
                        'period_ms': 100,
                        'execution_ms': 20,
                        'deadline_ms': 90,
                        'priority': 4
                    }
                ]
            }
        },
        'ini_example': {
            'format': 'ini',
            'spec': '''[Task_Navigation]
PERIOD_MS = 20
EXECUTION_MS = 12
DEADLINE_MS = 15
PRIORITY = 1

[Task_Sensor]
PERIOD_MS = 50
EXECUTION_MS = 30
DEADLINE_MS = 40
PRIORITY = 2

[Task_Logger]
PERIOD_MS = 100
EXECUTION_MS = 20
DEADLINE_MS = 90
PRIORITY = 3
'''
        }
    }
    
    return jsonify(examples)

@autonomous_bp.route('/autonomous_verify/status', methods=['GET'])
def pipeline_status():
    """Get pipeline configuration and status"""
    return jsonify({
        'pipeline': 'autonomous',
        'stages': 9,
        'features': [
            'Input Validation',
            'RMS Priority Fixing',
            'Schedulability Analysis',
            'TCTL Property Generation',
            'UPPAAL Model Generation',
            'Verifyta Verification',
            'Auto-Repair',
            'Haskell Code Generation',
            'SDD Documentation'
        ],
        'max_iterations': pipeline.max_repair_iterations if pipeline else 10,
        'verifyta_available': pipeline.verifyta_path is not None if pipeline else False
    })
