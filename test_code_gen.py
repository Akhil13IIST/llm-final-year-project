"""
Quick test to verify Haskell and UPPAAL XML generation
"""

import json
from core.autonomous_pipeline import AutonomousPipeline

spec = {
    "system_name": "CodeGenTest",
    "tasks": [
        {
            "name": "TestTask",
            "period_ms": 10,
            "deadline_ms": 10,
            "execution_time_ms": 3,
            "priority": 1
        }
    ]
}

print("Testing code generation...")
pipeline = AutonomousPipeline(use_llm=False)
result = pipeline.run_pipeline(spec)

print(f"\n✅ Success: {result['success']}")
print(f"🔄 Iterations: {result['iterations']}")

# Check Haskell code
if 'verified_haskell_code' in result:
    haskell_length = len(result['verified_haskell_code'])
    print(f"\n✅ Haskell Code: {haskell_length} characters")
    print("First 200 chars:")
    print(result['verified_haskell_code'][:200])
else:
    print("\n❌ No Haskell code found!")

# Check UPPAAL XML
if 'uppaal_xml' in result:
    xml_length = len(result['uppaal_xml'])
    print(f"\n✅ UPPAAL XML: {xml_length} characters")
    print("First 200 chars:")
    print(result['uppaal_xml'][:200])
else:
    print("\n❌ No UPPAAL XML found!")

# Check SDD
if 'sdd_document' in result:
    sdd_length = len(result['sdd_document'])
    print(f"\n✅ SDD Document: {sdd_length} characters")
else:
    print("\n❌ No SDD document found!")

print("\n" + "="*80)
print("RESULT KEYS:", list(result.keys()))
