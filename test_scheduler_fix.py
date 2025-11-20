"""Test script to verify the scheduler fix"""
import sys
sys.path.insert(0, '.')

from modules.verification_engine import WebAdaUppaalVerifier

# Test with the traffic light code
ada_code = """with Ada.Real_Time; use Ada.Real_Time;
with Ada.Text_IO; use Ada.Text_IO;

procedure Traffic_Light_Scheduler is

task Red_Light;
task body Red_Light is
Period : constant Time_Span := Milliseconds(100);
Deadline : constant Time_Span := Milliseconds(90);
Execution_Time : constant Time_Span := Milliseconds(30);
Next_Release : Time := Clock;
begin
loop
delay until Next_Release;
Put_Line("Red Light: Processing");
delay Execution_Time;
Next_Release := Next_Release + Period;
end loop;
end Red_Light;

task Yellow_Light;
task body Yellow_Light is
Period : constant Time_Span := Milliseconds(50);
Deadline : constant Time_Span := Milliseconds(45);
Execution_Time : constant Time_Span := Milliseconds(15);
Next_Release : Time := Clock;
begin
loop
delay until Next_Release;
Put_Line("Yellow Light: Processing");
delay Execution_Time;
Next_Release := Next_Release + Period;
end loop;
end Yellow_Light;

task Green_Light;
task body Green_Light is
Period : constant Time_Span := Milliseconds(300);
Deadline : constant Time_Span := Milliseconds(270);
Execution_Time : constant Time_Span := Milliseconds(90);
Next_Release : Time := Clock;
begin
loop
delay until Next_Release;
Put_Line("Green Light: Processing");
delay Execution_Time;
Next_Release := Next_Release + Period;
end loop;
end Green_Light;

begin
Put_Line("Traffic Light Scheduler Starting");
delay until Time_Last;
end Traffic_Light_Scheduler;
"""

print("="*60)
print("Testing Scheduler Fix")
print("="*60)

verifier = WebAdaUppaalVerifier()

# Extract task info
print("\n[1] Extracting task information...")
task_info = verifier.extract_from_code(ada_code, language='ada')
print(f"✓ Found {task_info['task_count']} tasks")
for task in task_info['tasks']:
    print(f"  - {task['task_name']}: P={task['period']}ms, D={task['deadline']}ms, Pri={task['priority']}")

# Generate UPPAAL model
print("\n[2] Generating UPPAAL model with FIXED scheduler...")
xml, properties = verifier.generate_uppaal_xml(task_info, source_code=ada_code)

# Check if the fix is present
if "!task_scheduled[0] &amp;&amp; !task_scheduled[1]" in xml:
    print("✓ SCHEDULER FIX DETECTED: Priority checks added!")
    print("  - Green_Light will only dispatch if Red and Yellow are NOT waiting")
else:
    print("✗ WARNING: Fix not applied correctly")

# Verify
print("\n[3] Running UPPAAL verification...")
result = verifier.verify_uppaal(
    xml, 
    "Traffic_Light_FIXED", 
    task_info=task_info,
    source_code=ada_code,
    language='ada',
    properties_list=properties
)

print(f"\n{'='*60}")
print(f"VERIFICATION RESULTS")
print(f"{'='*60}")
print(f"Properties Verified: {result['properties_verified']}")
print(f"Properties Failed: {result['properties_failed']}")
print(f"Execution Time: {result['execution_time']}s")
print(f"Success: {result['success']}")

if result['success']:
    print("\n🎉 ALL PROPERTIES PASSED! Scheduler fix works!")
else:
    print(f"\n❌ {result['properties_failed']} properties still failing")
    print("\nFailed properties:")
    for prop, details in result.get('property_results', {}).items():
        if not details.get('satisfied'):
            print(f"  - {prop}")

print(f"\nResults saved to: {result['verification_folder']}")
print("="*60)
