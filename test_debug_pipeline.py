"""
Debug test to see what's happening in the pipeline
"""

import json
from core.autonomous_pipeline import AutonomousPipeline

# Simple schedulable system
spec = {
    "system_name": "DebugTest",
    "tasks": [
        {
            "name": "TaskA",
            "period_ms": 10,
            "deadline_ms": 10,
            "execution_time_ms": 3,
            "priority": 1
        }
    ]
}

print("Testing single task system:")
print(json.dumps(spec, indent=2))

pipeline = AutonomousPipeline()
print(f"\nUPPAAL path: {pipeline.verifyta_path}")

result = pipeline.run_pipeline(spec)

print("\n" + "="*80)
print("RESULT:")
print("="*80)
print(f"Success: {result['success']}")
print(f"Converged: {result['converged']}")
print(f"Iterations: {result['iterations']}")

if 'error' in result:
    print(f"\nError: {result['error']}")

# Show stage execution
print("\n" + "="*80)
print("STAGE EXECUTION:")
print("="*80)
for i, stages in enumerate(result.get('stage_execution', []), 1):
    print(f"\nIteration {i}:")
    for stage in stages:
        print(f"  {stage}")

# Show verification details if available
if 'verification_result' in result:
    print("\n" + "="*80)
    print("VERIFICATION DETAILS:")
    print("="*80)
    vr = result['verification_result']
    print(f"All passed: {vr.get('all_passed', 'N/A')}")
    if 'raw_output' in vr:
        print(f"\nRaw UPPAAL output:")
        print(vr['raw_output'][:500])
