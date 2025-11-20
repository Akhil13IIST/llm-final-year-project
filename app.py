"""
LLM-Enhanced UPPAAL Verification Web Application
Main entry point - modular architecture
"""
from flask import Flask
from collections import deque
import queue
import os

import config
import modules.verification_engine as verification_engine
from core.schedulability_analyzer import SchedulabilityAnalyzer

# Import route blueprints
from routes.view_routes import views_bp
from routes.verification_routes import verification_bp, init_verification_routes
from routes.generation_routes import generation_bp, init_generation_routes
from routes.async_routes import async_bp, init_async_routes
from routes.autonomous_routes import autonomous_bp, init_autonomous_routes

# Initialize Flask app
app = Flask(__name__)

# Configure session
app.secret_key = os.urandom(24)  # Random secret key for sessions
app.config['SESSION_TYPE'] = 'filesystem'

# Sync configuration with verification engine
verification_engine.STRICT_PRIORITY_MODE = config.STRICT_PRIORITY_MODE
verification_engine.ALLOW_UNSCHEDULABLE = config.ALLOW_UNSCHEDULABLE
verification_engine.MAX_LLM_REPAIR_ATTEMPTS = config.MAX_LLM_REPAIR_ATTEMPTS
verification_engine.USE_LLM_PROPERTY_GENERATION = config.USE_LLM_PROPERTY_GENERATION
verification_engine.LLM_FEEDBACK_ENABLED = config.LLM_FEEDBACK_ENABLED
verification_engine.USE_SHARED_SCHEDULER = config.USE_SHARED_SCHEDULER
verification_engine.USE_PRIORITY_VALIDATION = config.USE_PRIORITY_VALIDATION
verification_engine.ALLOW_LLM_MULTITASK_PROPERTIES = config.ALLOW_LLM_MULTITASK_PROPERTIES
verification_engine.SHOW_RAW_UPPAAL_OUTPUT = config.SHOW_RAW_UPPAAL_OUTPUT
verification_engine.ENABLE_BUNDLE_EXPORT = config.ENABLE_BUNDLE_EXPORT

# Initialize verifier and LLM property generator with config
verifier = verification_engine.LLMEnhancedVerifier(
    uppaal_path=config.UPPAAL_PATH,
    ollama_url=config.OLLAMA_BASE_URL
)
llm_property_gen = verification_engine.llm_property_gen
sched_analyzer_global = SchedulabilityAnalyzer(allow_unschedulable=config.ALLOW_UNSCHEDULABLE)

# Initialize route modules with shared instances
init_verification_routes(verifier, llm_property_gen)
init_generation_routes(verifier)
init_async_routes(verifier)
init_autonomous_routes(config.UPPAAL_PATH, use_llm=config.USE_LLM_PROPERTY_GENERATION)

# Register blueprints
app.register_blueprint(views_bp)
app.register_blueprint(verification_bp)
app.register_blueprint(generation_bp)
app.register_blueprint(async_bp)
app.register_blueprint(autonomous_bp)

if __name__ == '__main__':
    print("=" * 60)
    print("LLM-Enhanced UPPAAL Verification Server")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  - LLM Property Generation: {config.USE_LLM_PROPERTY_GENERATION}")
    print(f"  - Shared Scheduler: {config.USE_SHARED_SCHEDULER}")
    print(f"  - Priority Validation: {config.USE_PRIORITY_VALIDATION}")
    print(f"  - Max Repair Attempts: {config.MAX_LLM_REPAIR_ATTEMPTS}")
    print(f"  - Strict Priority Mode: {config.STRICT_PRIORITY_MODE}")
    print(f"  - Allow Unschedulable: {config.ALLOW_UNSCHEDULABLE}")
    print("=" * 60)
    print("Server running at: http://127.0.0.1:5000")
    print("API Endpoints:")
    print("  - GET  /              - Main UI")
    print("  - GET  /editor        - Task Editor")
    print("  - POST /verify        - Verify code")
    print("  - POST /generate_ada  - Generate code from NL")
    print("  - GET  /dashboard     - Metrics dashboard")
    print("  - POST /autonomous_verify - Autonomous 9-stage pipeline")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
