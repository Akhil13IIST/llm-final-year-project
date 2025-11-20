"""
Full Integration Test for Autonomous Verification Pipeline
Tests complete workflow: Spec → Real UPPAAL → Verified Code
"""

import json
from core.autonomous_pipeline import AutonomousPipeline

def test_real_uppaal_integration():
    """
    Test the complete autonomous pipeline with real UPPAAL verifyta
    """
    print("\n" + "="*80)
    print("FULL INTEGRATION TEST - REAL UPPAAL VERIFYTA")
    print("="*80)
    
    # Create a simple, schedulable system
    spec = {
        "system_name": "SimpleSchedulableSystem",
        "tasks": [
            {
                "name": "HighPriorityTask",
                "period_ms": 10,
                "deadline_ms": 10,
                "execution_time_ms": 3,
                "priority": 1
            },
            {
                "name": "LowPriorityTask",
                "period_ms": 20,
                "deadline_ms": 20,
                "execution_time_ms": 5,
                "priority": 2
            }
        ]
    }
    
    print(f"\n📋 INPUT SPECIFICATION:")
    print(json.dumps(spec, indent=2))
    
    # Calculate utilization
    utilization = sum(t["execution_time_ms"] / t["period_ms"] for t in spec["tasks"])
    print(f"\n📊 System Utilization: {utilization*100:.1f}%")
    
    # Create pipeline
    pipeline = AutonomousPipeline()
    
    print(f"\n🔧 Using UPPAAL verifyta at: {pipeline.verifyta_path}")
    
    # Run pipeline
    print(f"\n🚀 Executing 9-stage autonomous pipeline...")
    result = pipeline.run_pipeline(spec)
    
    # Display results
    print("\n" + "="*80)
    print("PIPELINE EXECUTION RESULTS")
    print("="*80)
    
    print(f"\n✅ Success: {result['success']}")
    print(f"🔄 Converged: {result['converged']}")
    print(f"🔢 Iterations: {result['iterations']}")
    
    if result["success"]:
        print(f"\n🎯 FORMAL VERIFICATION:")
        vr = result.get('verification_result', {})
        print(f"  Properties Verified: {vr.get('properties_verified', 'N/A')}")
        print(f"  All Properties Passed: {vr.get('all_passed', 'N/A')}")
        
        if "execution_time" in vr:
            print(f"  Verifyta Execution Time: {vr['execution_time']:.2f}s")
        
        print(f"\n📜 VERIFIED CODE GENERATION:")
        haskell_code = result.get("haskell_code", "")
        print(f"  Haskell Code Length: {len(haskell_code)} characters")
        print(f"  First 500 chars:")
        print("  " + "-"*76)
        for line in haskell_code[:500].split('\n'):
            print(f"  {line}")
        print("  " + "-"*76)
        
        print(f"\n📄 SYSTEM DESIGN DOCUMENT:")
        sdd = result.get("sdd_document", "")
        print(f"  SDD Length: {len(sdd)} characters")
        print(f"  First 400 chars:")
        print("  " + "-"*76)
        for line in sdd[:400].split('\n'):
            print(f"  {line}")
        print("  " + "-"*76)
        
        # Display stage execution
        print(f"\n🔍 STAGE EXECUTION TRACE:")
        for iteration, stages in enumerate(result.get("stage_execution", []), 1):
            print(f"\n  Iteration {iteration}:")
            for stage in stages:
                print(f"    ✓ {stage}")
        
        # Display final spec
        print(f"\n✅ FINAL VERIFIED SPECIFICATION:")
        final_spec = result["final_spec"]
        for task in final_spec["tasks"]:
            util = (task["execution_time_ms"] / task["period_ms"]) * 100
            print(f"  {task['name']}: P={task['period_ms']}ms, D={task['deadline_ms']}ms, "
                  f"C={task['execution_time_ms']}ms, U={util:.1f}%")
        
        total_util = sum(t["execution_time_ms"] / t["period_ms"] for t in final_spec["tasks"]) * 100
        print(f"  Total Utilization: {total_util:.1f}%")
        
    else:
        print(f"\n❌ Pipeline failed:")
        print(f"  Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    return result["success"]


def test_unschedulable_repair():
    """
    Test auto-repair on an initially unschedulable system
    """
    print("\n" + "="*80)
    print("AUTO-REPAIR TEST - REAL UPPAAL WITH FIXES")
    print("="*80)
    
    # Create an unschedulable system (>100% utilization)
    spec = {
        "system_name": "UnschedulableSystem",
        "tasks": [
            {
                "name": "HeavyTask1",
                "period_ms": 10,
                "deadline_ms": 10,
                "execution_time_ms": 8,  # 80% utilization
                "priority": 1
            },
            {
                "name": "HeavyTask2",
                "period_ms": 15,
                "deadline_ms": 15,
                "execution_time_ms": 10,  # 67% utilization
                "priority": 2
            }
        ]
    }
    
    initial_util = sum(t["execution_time_ms"] / t["period_ms"] for t in spec["tasks"]) * 100
    print(f"\n📊 Initial Utilization: {initial_util:.1f}% (UNSCHEDULABLE)")
    
    # Run pipeline with auto-repair
    pipeline = AutonomousPipeline()
    result = pipeline.run_pipeline(spec)
    
    if result["success"]:
        final_util = sum(t["execution_time_ms"] / t["period_ms"] for t in result["final_spec"]["tasks"]) * 100
        print(f"\n✅ Auto-Repair Success!")
        print(f"📊 Final Utilization: {final_util:.1f}%")
        print(f"🔄 Iterations Required: {result['iterations']}")
        
        print(f"\n🔧 REPAIRS APPLIED:")
        for i, (orig, fixed) in enumerate(zip(spec["tasks"], result["final_spec"]["tasks"])):
            if orig["period_ms"] != fixed["period_ms"]:
                print(f"  {fixed['name']}: Period {orig['period_ms']}ms → {fixed['period_ms']}ms")
        
        return True
    else:
        print(f"\n❌ Auto-repair failed: {result.get('error', 'Unknown')}")
        return False


if __name__ == "__main__":
    print("\n" + "🤖"*40)
    print("AUTONOMOUS FORMAL VERIFICATION AGENT - FULL INTEGRATION TEST")
    print("Testing Real UPPAAL Verifyta Integration")
    print("🤖"*40)
    
    # Test 1: Normal verification
    test1_passed = test_real_uppaal_integration()
    
    # Test 2: Auto-repair
    test2_passed = test_unschedulable_repair()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUITE SUMMARY")
    print("="*80)
    print(f"Test 1 (Real UPPAAL Integration): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Auto-Repair with UPPAAL): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("="*80)
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! System is production-ready.")
    else:
        print("\n⚠️  Some tests failed. Review logs above.")
