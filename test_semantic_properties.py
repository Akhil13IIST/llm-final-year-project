"""
Test script to demonstrate semantic property generation from source code
Run this in a separate terminal window (not with the Flask server running)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Prevent Flask app from running
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

from core.llm_property_generator import LLMPropertyGenerator

# Sample traffic controller Ada code
traffic_code = """
-- Traffic Light Controller with Fault Handling
procedure Vehicle_Green is
   green_light : Boolean := True;
   red_light : Boolean := False;
begin
   -- Turn vehicle light green
   Set_Light(Green);
   delay until Period;
end Vehicle_Green;

procedure Opposing_Red is
   red_light : Boolean := True;
begin
   -- Ensure opposing traffic is red when vehicle is green
   Set_Light(Red);
   delay until Period;
end Opposing_Red;

procedure Pedestrian_Signal is
   walk_signal : Boolean := False;
begin
   -- Control pedestrian crossing signal
   if Safe_To_Cross then
      walk_signal := True;
   end if;
end Pedestrian_Signal;

procedure Fault_Checker is
   fault_detected : Boolean := False;
begin
   -- Monitor for system faults
   if Error_Condition then
      fault_detected := True;
      Enter_Safe_Mode;
   end if;
end Fault_Checker;
"""

def main():
    # Multi-task info
    task_info = {
        'multi_task': True,
        'task_count': 4,
        'tasks': [
            {'task_name': 'Vehicle_Green', 'period': 100, 'deadline': 80, 'priority': 1},
            {'task_name': 'Opposing_Red', 'period': 100, 'deadline': 80, 'priority': 2},
            {'task_name': 'Pedestrian_Signal', 'period': 200, 'deadline': 150, 'priority': 3},
            {'task_name': 'Fault_Checker', 'period': 50, 'deadline': 40, 'priority': 4}
        ]
    }

    # Test semantic analysis
    print("="*80)
    print("TESTING SEMANTIC CODE ANALYSIS")
    print("="*80)

    prop_gen = LLMPropertyGenerator()

    # Test the _analyze_code_semantics method
    analysis = prop_gen._analyze_code_semantics(traffic_code, task_info)

    print("\n[CODE ANALYSIS RESULTS]")
    print(analysis)

    print("\n" + "="*80)
    print("SEMANTIC ANALYSIS COMPLETE")
    print("="*80)
    print("\nThis analysis will be included in the LLM prompt to generate")
    print("domain-specific properties like:")
    print("  - A[] (Vehicle_Green_inst.Executing imply Opposing_Red_inst.Idle)")
    print("  - A[] (Fault_Checker_inst.fault_detected imply Safe_Mode)")
    print("  - E<> Pedestrian_Signal_inst.walk_signal")
    print("\nInstead of just generic timing properties!")

if __name__ == '__main__':
    main()

