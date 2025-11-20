"""
Test script for Autonomous Verification Pipeline
Demonstrates the full 9-stage autonomous pipeline
"""
import json
import sys
sys.path.insert(0, '.')

from core.autonomous_pipeline import AutonomousPipeline

def test_json_spec():
    """Test with JSON specification"""
    print("=" * 80)
    print("AUTONOMOUS PIPELINE TEST - JSON INPUT")
    print("=" * 80)
    
    spec = {
        "tasks": [
            {
                "name": "NavigationTask",
                "period_ms": 20,
                "execution_ms": 12,
                "deadline_ms": 15,
                "priority": 1
            },
            {
                "name": "SensorTask",
                "period_ms": 50,
                "execution_ms": 30,
                "deadline_ms": 40,
                "priority": 2
            },
            {
                "name": "LoggerTask",
                "period_ms": 100,
                "execution_ms": 20,
                "deadline_ms": 90,
                "priority": 3
            }
        ]
    }
    
    pipeline = AutonomousPipeline()
    result = pipeline.run_pipeline(json.dumps(spec), "json")
    
    print("\n" + "=" * 80)
    print("PIPELINE RESULTS")
    print("=" * 80)
    print(f"Success: {result['success']}")
    print(f"Converged: {result['converged']}")
    print(f"Iterations: {result['iterations']}")
    
    if result['success']:
        print(f"\n--- FINAL SPECIFICATION ---")
        for task in result['final_spec']['tasks']:
            print(f"  {task['name']}: P={task['period_ms']}ms, D={task['deadline_ms']}ms, C={task['execution_ms']}ms, Pri={task['priority']}")
        
        print(f"\n--- VERIFICATION RESULTS ---")
        vr = result['verification_results']
        print(f"All Passed: {vr['all_passed']}")
        print(f"Properties Checked: {len(vr['property_results'])}")
        
        print(f"\n--- VERIFIED HASKELL CODE (excerpt) ---")
        code_lines = result['verified_haskell_code'].split('\n')
        for line in code_lines[:20]:
            print(line)
        print("...")
        
        print(f"\n--- SDD DOCUMENT (excerpt) ---")
        sdd_lines = result['sdd_document'].split('\n')
        for line in sdd_lines[:30]:
            print(line)
        print("...")
        
        print(f"\n--- STAGE EXECUTION HISTORY ---")
        for iteration in result['stage_history']:
            print(f"\nIteration {iteration['iteration']}:")
            for stage in iteration['stages']:
                print(f"  Stage {stage['stage']}: {stage['name']}")
    else:
        print(f"\nError: {result.get('error')}")
        print("\n--- STAGE HISTORY ---")
        for iteration in result['stage_history']:
            print(f"\nIteration {iteration['iteration']}:")
            for stage in iteration['stages']:
                print(f"  Stage {stage['stage']}: {stage['name']}")
                if 'error' in stage['result']:
                    print(f"    ERROR: {stage['result']['error']}")

def test_ini_spec():
    """Test with INI specification"""
    print("\n\n" + "=" * 80)
    print("AUTONOMOUS PIPELINE TEST - INI INPUT")
    print("=" * 80)
    
    ini_spec = """[Task_Control]
PERIOD_MS = 10
EXECUTION_MS = 6
DEADLINE_MS = 8
PRIORITY = 1

[Task_Navigation]
PERIOD_MS = 20
EXECUTION_MS = 12
DEADLINE_MS = 15
PRIORITY = 2
"""
    
    pipeline = AutonomousPipeline()
    result = pipeline.run_pipeline(ini_spec, "ini")
    
    print(f"\nSuccess: {result['success']}")
    print(f"Converged: {result['converged']}")
    print(f"Iterations: {result['iterations']}")
    
    if result['success']:
        print(f"\nFinal Task Count: {len(result['final_spec']['tasks'])}")
        print(f"Properties Verified: {len(result['properties'])}")
        print(f"\nHaskell Code Generated: {len(result['verified_haskell_code'])} characters")
        print(f"SDD Document Generated: {len(result['sdd_document'])} characters")

def test_unschedulable_auto_repair():
    """Test auto-repair on unschedulable system"""
    print("\n\n" + "=" * 80)
    print("AUTO-REPAIR TEST - INTENTIONALLY UNSCHEDULABLE SYSTEM")
    print("=" * 80)
    
    # Create system that will fail schedulability
    spec = {
        "tasks": [
            {
                "name": "Task1",
                "period_ms": 10,
                "execution_ms": 9,  # 90% utilization
                "deadline_ms": 10,
                "priority": 1
            },
            {
                "name": "Task2",
                "period_ms": 20,
                "execution_ms": 15,  # 75% utilization
                "deadline_ms": 20,
                "priority": 2
            }
        ]
    }
    
    print("\nOriginal Specification (Over 100% utilization):")
    total_u = sum(t['execution_ms'] / t['period_ms'] for t in spec['tasks'])
    print(f"  Total Utilization: {total_u * 100:.1f}%")
    
    pipeline = AutonomousPipeline()
    result = pipeline.run_pipeline(json.dumps(spec), "json")
    
    print(f"\nPipeline Result:")
    print(f"  Success: {result['success']}")
    print(f"  Iterations: {result['iterations']}")
    
    if result['success']:
        print("\nRepaired Specification:")
        for task in result['final_spec']['tasks']:
            u = task['execution_ms'] / task['period_ms']
            print(f"  {task['name']}: P={task['period_ms']}ms, C={task['execution_ms']}ms, U={u*100:.1f}%")
        
        new_u = sum(t['execution_ms'] / t['period_ms'] for t in result['final_spec']['tasks'])
        print(f"\n  New Total Utilization: {new_u * 100:.1f}%")
        print(f"  Auto-Repair SUCCESS! ✅")

if __name__ == "__main__":
    print("\n" + "🤖 " * 20)
    print("AUTONOMOUS FORMAL VERIFICATION AGENT")
    print("Deterministic 9-Stage Pipeline: Spec → Verified Code")
    print("🤖 " * 20 + "\n")
    
    test_json_spec()
    test_ini_spec()
    test_unschedulable_auto_repair()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
