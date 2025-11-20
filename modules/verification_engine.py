"""
LLM-Enhanced UPPAAL Verification Engine
Main verification logic with LLM integration
"""

import subprocess
import re
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
import json
import traceback
import time

# Import core modules
from core.llm_property_generator import LLMPropertyGenerator
from core.schedulability_analyzer import SchedulabilityAnalyzer
from core.priority_validator import PriorityValidator
from core.counterexample_analyzer import CounterexampleAnalyzer
from core.uppaal_generator import UppaalGenerator
from core.uppaal_verifier import UppaalVerifier
from core.property_repair import PropertyRepairEngine

# Global configuration (will be set by app.py)
STRICT_PRIORITY_MODE = False
ALLOW_UNSCHEDULABLE = False
MAX_LLM_REPAIR_ATTEMPTS = 3
USE_LLM_PROPERTY_GENERATION = True
LLM_FEEDBACK_ENABLED = True
USE_SHARED_SCHEDULER = True
USE_PRIORITY_VALIDATION = True
ALLOW_LLM_MULTITASK_PROPERTIES = True
SHOW_RAW_UPPAAL_OUTPUT = True
ENABLE_BUNDLE_EXPORT = True

# Initialize LLM property generator
llm_property_gen = LLMPropertyGenerator(enable_rag=False)

class LLMEnhancedVerifier:
    """Main verification engine with LLM integration"""
    
    def __init__(self, uppaal_path=r"C:\uppaal-5.0.0\bin-Windows\verifyta.exe",
                 ollama_url="http://localhost:11434"):
        self.uppaal_path = uppaal_path
        self.ollama_url = ollama_url
        self.results_folder = "verification_results"
        os.makedirs(self.results_folder, exist_ok=True)
        
        # Initialize sub-modules
        self.sched_analyzer = SchedulabilityAnalyzer(allow_unschedulable=ALLOW_UNSCHEDULABLE)
        self.priority_validator = PriorityValidator()
        self.ce_analyzer = CounterexampleAnalyzer()
        self.uppaal_generator = UppaalGenerator()
        self.uppaal_verifier = UppaalVerifier(uppaal_path)
        self.repair_engine = PropertyRepairEngine()
        
        # Check LLM availability
        self.llm_available = self._check_llm_available()
        
    def _check_llm_available(self):
        """Check if Ollama LLM is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def extract_from_code(self, code, language='ada'):
        """
        Extract task information from Ada or Python code
        
        Returns:
            dict with task_name, period, deadline, execution_time, priority
        """
        if language.lower() == 'python':
            return self._extract_from_python(code)
        else:
            return self._extract_from_ada(code)
    
    def _extract_from_ada(self, ada_code):
        """Extract task info from Ada code, supporting multi-task files."""
        task_blocks = list(re.finditer(
            r'task\s+body\s+(?P<name>\w+).*?end\s+\1\s*;',
            ada_code,
            re.IGNORECASE | re.DOTALL
        ))
        
        if len(task_blocks) > 1:
            tasks = []
            for idx, block in enumerate(task_blocks):
                snippet = block.group(0)
                task_info = self._extract_single_ada_task(
                    snippet,
                    default_priority=idx + 1
                )
                tasks.append(task_info)
            return {
                'multi_task': True,
                'task_count': len(tasks),
                'tasks': tasks
            }
        
        return self._extract_single_ada_task(ada_code)

    def _extract_single_ada_task(self, ada_code, default_priority=1):
        """Extract a single task definition from Ada code."""
        task_info = {
            'task_name': 'Task',
            'period': None,
            'deadline': None,
            'execution_time': None,
            'priority': default_priority,
            'multi_task': False
        }
        
        # Extract task name
        task_match = re.search(r'task\s+body\s+(\w+)', ada_code, re.IGNORECASE)
        if task_match:
            task_info['task_name'] = task_match.group(1)
        
        # Extract period
        period_match = re.search(r'Period\s*(?:=>|:).*?Milliseconds\s*\(\s*(\d+)\s*\)', ada_code, re.IGNORECASE)
        if period_match:
            task_info['period'] = int(period_match.group(1))
        
        # Extract deadline
        deadline_match = re.search(r'Deadline\s*(?:=>|:).*?Milliseconds\s*\(\s*(\d+)\s*\)', ada_code, re.IGNORECASE)
        if deadline_match:
            task_info['deadline'] = int(deadline_match.group(1))
        else:
            task_info['deadline'] = task_info['period']  # D = T if not specified
        
        # Extract execution time
        exec_match = re.search(r'(?:Execution_Time|WCET)\s*(?:=>|:).*?Milliseconds\s*\(\s*(\d+)\s*\)', ada_code, re.IGNORECASE)
        if exec_match:
            task_info['execution_time'] = int(exec_match.group(1))
        
        # Extract priority
        priority_match = re.search(r'pragma\s+Priority\s*\(\s*(\d+)\s*\)', ada_code, re.IGNORECASE)
        if not priority_match:
             # Try aspect syntax
             priority_match = re.search(r'Priority\s*=>\s*(\d+)', ada_code, re.IGNORECASE)
        
        if priority_match:
            task_info['priority'] = int(priority_match.group(1))
        
        return task_info
    
    def _extract_from_python(self, python_code):
        """Extract task info from Python code"""
        task_info = {
            'task_name': 'Task',
            'period': None,
            'deadline': None,
            'execution_time': None,
            'priority': 1,
            'multi_task': False
        }
        
        # Extract class name
        class_match = re.search(r'class\s+(\w+)', python_code)
        if class_match:
            task_info['task_name'] = class_match.group(1)
        
        # Extract PERIOD
        period_match = re.search(r'PERIOD\s*=\s*(\d+)', python_code, re.IGNORECASE)
        if period_match:
            task_info['period'] = int(period_match.group(1))
        
        # Extract DEADLINE
        deadline_match = re.search(r'DEADLINE\s*=\s*(\d+)', python_code, re.IGNORECASE)
        if deadline_match:
            task_info['deadline'] = int(deadline_match.group(1))
        else:
            task_info['deadline'] = task_info['period']
        
        # Extract EXECUTION_TIME or WCET
        exec_match = re.search(r'EXECUTION_TIME\s*=\s*(\d+)', python_code, re.IGNORECASE)
        if not exec_match:
            exec_match = re.search(r'WCET\s*=\s*(\d+)', python_code, re.IGNORECASE)
        if exec_match:
            task_info['execution_time'] = int(exec_match.group(1))
        
        # Extract PRIORITY
        priority_match = re.search(r'PRIORITY\s*=\s*(\d+)', python_code, re.IGNORECASE)
        if priority_match:
            task_info['priority'] = int(priority_match.group(1))
        
        return task_info
    
    def generate_uppaal_xml(self, task_info, source_code=None):
        """Generate UPPAAL XML model from task info (single or multi-task)."""
        return self.uppaal_generator.generate_xml(task_info, source_code)
    
    def verify_uppaal(self, xml_content, task_name, task_info=None, source_code=None, language='ada', properties_list=None):
        """
        Run UPPAAL verification
        
        Args:
            xml_content: UPPAAL XML model
            task_name: Name of the task
            task_info: Task information dict (optional)
            source_code: Original source code (optional)
            language: Programming language (ada/python)
            properties_list: List of properties to verify (optional)
        
        Returns:
            dict with verification results
        """
        # Save XML to temp file
        xml_filename = f"{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        xml_path = os.path.join(self.results_folder, xml_filename)
        
        # Use UppaalVerifier
        # Note: properties_list is optional here, but UppaalVerifier expects it for parsing results.
        # If not provided, we might miss detailed property results, but raw output will be there.
        props = properties_list if properties_list else []
        
        result = self.uppaal_verifier.verify(xml_content, props, timeout=300, xml_path=xml_path)
        
        # Adapt result to expected format
        return {
            'success': result['all_passed'],
            'properties_verified': result.get('properties_verified', 0),
            'properties_failed': result.get('properties_failed', 0),
            'uppaal_output': result.get('raw_output', ''),
            'execution_time': result.get('execution_time', 0),
            'xml_path': result.get('xml_path', xml_path),
            'completed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'verification_folder': self.results_folder,
            'error': result.get('error')
        }
    
    def verify_uppaal_async(self, xml_content, task_name, job_id, task_info=None, source_code=None, language='ada', properties_list=None):
        """Async version of verify_uppaal"""
        return self.verify_uppaal(xml_content, task_name, task_info, source_code, language, properties_list)
    
    def generate_ada_from_nl(self, requirement):
        """Generate Ada code from natural language using LLM"""
        if not self.llm_available:
            return "-- LLM not available\n-- Please start Ollama"
        
        prompt = f"""Generate Ada real-time task code from this requirement:

{requirement}

Generate ONLY the Ada code with:
- task declaration with pragma Priority
- task body with Period, Deadline, Execution_Time constants using Milliseconds()
- Basic loop structure with 'delay until Next_Release'

Output ONLY the code, no explanations."""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                code = response.json().get('response', '')
                return self._sanitize_llm_output(code, 'ada')
            else:
                return f"-- Error: {response.status_code}"
                
        except Exception as e:
            return f"-- Error: {str(e)}"
    
    def generate_python_from_nl(self, requirement):
        """Generate Python code from natural language using LLM"""
        if not self.llm_available:
            return "# LLM not available\n# Please start Ollama"
        
        prompt = f"""Generate Python real-time task class from this requirement:

{requirement}

Generate ONLY the Python code with:
- class definition
- PERIOD, DEADLINE, EXECUTION_TIME, PRIORITY as class variables
- run() method

Output ONLY the code, no explanations."""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                code = response.json().get('response', '')
                return self._sanitize_llm_output(code, 'python')
            else:
                return f"# Error: {response.status_code}"
                
        except Exception as e:
            return f"# Error: {str(e)}"

    def _sanitize_llm_output(self, llm_output, language='ada'):
        """Remove markdown formatting and explanatory text from LLM output"""
        # Remove markdown code blocks
        llm_output = re.sub(r'```(?:ada|python)?\n', '', llm_output)
        llm_output = re.sub(r'```\s*$', '', llm_output)
        
        # Remove common explanatory patterns at the end
        explanation_patterns = [
            r'\n\s*This code.*$',
            r'\n\s*Note:.*$',
            r'\n\s*To use.*$',
            r'\n\s*I hope.*$',
            r'\n\s*The above.*$'
        ]
        
        for pattern in explanation_patterns:
            llm_output = re.sub(pattern, '', llm_output, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        
        return llm_output.strip()
    
    def regenerate_with_feedback(self, original_code, error_msg, nl_requirement, language='ada'):
        """Regenerate code based on error feedback"""
        if not self.llm_available:
            return original_code, "LLM not available"
        
        prompt = f"""The following {language.upper()} code has an error:

{original_code}

Error: {error_msg}

Original requirement: {nl_requirement}

Please fix the code. Output ONLY the corrected code, no explanations."""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                code = response.json().get('response', '')
                return self._sanitize_llm_output(code, language), None
            else:
                return original_code, f"Error: {response.status_code}"
                
        except Exception as e:
            return original_code, str(e)
    
    def repair_counterexample(self, original_code, counterexample, task_info, language='ada'):
        """
        Repair code based on counterexample
        
        Args:
            original_code: The code that failed verification
            counterexample: The UPPAAL counterexample/error output
            task_info: Task information dict (used as context)
            language: Programming language (ada/python)
            
        Returns:
            tuple: (repaired_code, error_message)
        """
        # Create a descriptive requirement from task_info
        nl_requirement = f"Real-time task with period={task_info.get('period', 'unknown')}, deadline={task_info.get('deadline', 'unknown')}, execution_time={task_info.get('execution_time', 'unknown')}"
        return self.regenerate_with_feedback(original_code, f"Verification failed: {counterexample}", nl_requirement, language)


# Backwards compatibility alias for older modules/tests
WebAdaUppaalVerifier = LLMEnhancedVerifier
