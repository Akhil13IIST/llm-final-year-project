"""
Test LLM Integration in Autonomous Pipeline
"""

import json
from core.autonomous_pipeline import AutonomousPipeline

def test_llm_property_generation():
    """Test that LLM generates properties correctly"""
    print("\n" + "="*80)
    print("LLM INTEGRATION TEST")
    print("="*80)
    
    # Simple test spec
    spec = {
        "system_name": "LLMTest",
        "tasks": [
            {
                "name": "SensorTask",
                "period_ms": 20,
                "deadline_ms": 20,
                "execution_time_ms": 8,
                "priority": 1
            }
        ]
    }
    
    print("\n📋 Test Specification:")
    print(json.dumps(spec, indent=2))
    
    # Test with LLM enabled
    print("\n" + "-"*80)
    print("TEST 1: With LLM Enabled")
    print("-"*80)
    
    pipeline_llm = AutonomousPipeline(use_llm=True)
    print(f"LLM Available: {pipeline_llm.use_llm}")
    print(f"LLM Property Generator: {pipeline_llm.llm_property_gen is not None}")
    
    if pipeline_llm.use_llm:
        result_llm = pipeline_llm.run_pipeline(spec)
        
        print(f"\n✅ Success: {result_llm['success']}")
        print(f"🔄 Iterations: {result_llm['iterations']}")
        
        if 'properties' in result_llm:
            print(f"\n📜 Properties Generated: {len(result_llm['properties'])}")
            for i, prop in enumerate(result_llm['properties'][:5], 1):
                llm_tag = " [LLM]" if prop.get('llm_generated') else " [Template]"
                print(f"  {i}. {prop['formula']}{llm_tag}")
    else:
        print("⚠️  LLM not available, skipping LLM test")
    
    # Test with LLM disabled
    print("\n" + "-"*80)
    print("TEST 2: With LLM Disabled (Deterministic Templates)")
    print("-"*80)
    
    pipeline_no_llm = AutonomousPipeline(use_llm=False)
    print(f"LLM Available: {pipeline_no_llm.use_llm}")
    
    result_no_llm = pipeline_no_llm.run_pipeline(spec)
    
    print(f"\n✅ Success: {result_no_llm['success']}")
    print(f"🔄 Iterations: {result_no_llm['iterations']}")
    
    if 'properties' in result_no_llm:
        print(f"\n📜 Properties Generated: {len(result_no_llm['properties'])}")
        for i, prop in enumerate(result_no_llm['properties'][:5], 1):
            print(f"  {i}. {prop['formula']}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    return result_llm if pipeline_llm.use_llm else result_no_llm


def test_multi_task_llm():
    """Test LLM with multi-task system"""
    print("\n" + "="*80)
    print("MULTI-TASK LLM TEST")
    print("="*80)
    
    spec = {
        "system_name": "MultiTaskLLM",
        "tasks": [
            {
                "name": "HighPriority",
                "period_ms": 10,
                "deadline_ms": 10,
                "execution_time_ms": 3,
                "priority": 1
            },
            {
                "name": "LowPriority",
                "period_ms": 20,
                "deadline_ms": 20,
                "execution_time_ms": 5,
                "priority": 2
            }
        ]
    }
    
    print("\n📋 Multi-Task Specification:")
    print(json.dumps(spec, indent=2))
    
    pipeline = AutonomousPipeline(use_llm=True)
    
    if not pipeline.use_llm:
        print("\n⚠️  LLM not available, using deterministic templates")
    
    result = pipeline.run_pipeline(spec)
    
    print(f"\n✅ Success: {result['success']}")
    print(f"🔄 Iterations: {result['iterations']}")
    
    if 'properties' in result:
        print(f"\n📜 Properties Generated: {len(result['properties'])}")
        
        # Categorize properties
        categories = {}
        for prop in result['properties']:
            cat = prop.get('category', 'UNKNOWN')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(prop)
        
        print("\n📊 Properties by Category:")
        for cat, props in categories.items():
            print(f"\n  {cat}: {len(props)} properties")
            for prop in props[:3]:
                llm_tag = " [LLM]" if prop.get('llm_generated') else " [Template]"
                print(f"    • {prop['formula']}{llm_tag}")
    
    print("\n" + "="*80)
    print("MULTI-TASK TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    print("\n" + "🤖"*40)
    print("AUTONOMOUS PIPELINE - LLM INTEGRATION TEST")
    print("🤖"*40)
    
    # Test 1: Single task with LLM
    test_llm_property_generation()
    
    # Test 2: Multi-task with LLM
    test_multi_task_llm()
    
    print("\n" + "="*80)
    print("ALL LLM INTEGRATION TESTS COMPLETE")
    print("="*80)
