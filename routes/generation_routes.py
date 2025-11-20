"""
Generation Routes - Code generation from natural language
"""
from flask import Blueprint, request, jsonify
import traceback

generation_bp = Blueprint('generation', __name__)

# Global verifier instance (set by init function)
verifier = None

def init_generation_routes(verifier_instance):
    """Initialize generation routes with verifier instance"""
    global verifier
    verifier = verifier_instance

@generation_bp.route('/generate_ada', methods=['POST'])
def generate_ada():
    """Generate Ada code from natural language requirement"""
    try:
        data = request.json
        requirement = data.get('requirement', '')
        
        if not requirement:
            return jsonify({'error': 'No requirement provided'}), 400
        
        # Use verifier's LLM to generate Ada code
        ada_code = verifier.generate_ada_from_nl(requirement)
        
        return jsonify({
            'success': True,
            'ada_code': ada_code
        })
        
    except Exception as e:
        print(f"Error in generate_ada: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@generation_bp.route('/generate_python', methods=['POST'])
def generate_python():
    """Generate Python code from natural language requirement"""
    try:
        data = request.json
        requirement = data.get('requirement', '')
        
        if not requirement:
            return jsonify({'error': 'No requirement provided'}), 400
        
        # Use verifier's LLM to generate Python code
        python_code = verifier.generate_python_from_nl(requirement)
        
        return jsonify({
            'success': True,
            'python_code': python_code
        })
        
    except Exception as e:
        print(f"Error in generate_python: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
