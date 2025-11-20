"""
Configuration for LLM-Enhanced UPPAAL Verification System
"""
import os

# ===== LLM Configuration =====
# Ollama LLM settings
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "llama3.1:latest"  # Changed from qwen2.5-coder to llama3.1
LLM_TIMEOUT = 120  # seconds
LLM_MAX_RETRIES = 3

# LLM Feature Flags
USE_LLM_PROPERTY_GENERATION = True  # Generate properties using LLM
LLM_FEEDBACK_ENABLED = True  # Provide LLM explanations for failures
ALLOW_LLM_MULTITASK_PROPERTIES = True  # Allow multi-task properties from LLM

# ===== Verification Configuration =====
# UPPAAL paths
UPPAAL_PATH = r"C:\Program Files\UPPAAL-5.0.0\app\bin\verifyta.exe"
UPPAAL_TIMEOUT = 300  # seconds

# Verification behavior
ALLOW_UNSCHEDULABLE = False  # Allow verification even if not schedulable
MAX_LLM_REPAIR_ATTEMPTS = 3  # Maximum LLM code repair iterations
SHOW_RAW_UPPAAL_OUTPUT = True  # Show raw UPPAAL output in results

# ===== Scheduling Configuration =====
# Priority and scheduling settings
STRICT_PRIORITY_MODE = False  # Enforce Rate Monotonic priority ordering
USE_PRIORITY_VALIDATION = True  # Validate and auto-fix priorities
USE_SHARED_SCHEDULER = True  # Use shared CPU scheduler in model

# ===== Output Configuration =====
# Result storage
RESULTS_DIR = "verification_results"
ENABLE_BUNDLE_EXPORT = True  # Allow downloading verification bundles

# Create results directory if it doesn't exist
os.makedirs(RESULTS_DIR, exist_ok=True)

# ===== Debug Configuration =====
DEBUG_MODE = True
VERBOSE_LOGGING = True
