"""
UPPAAL Verifier
Centralized logic for running UPPAAL verifyta
"""
import subprocess
import tempfile
import os
import time
from typing import Dict, List, Any

class UppaalVerifier:
    def __init__(self, verifyta_path: str = None):
        self.verifyta_path = verifyta_path
        if not self.verifyta_path:
             # Try to find it
             common_paths = [
                r"C:\uppaal-5.0.0\bin-Windows\verifyta.exe",
                r"C:\Users\akhil\AppData\Local\Programs\UPPAAL-5.0.0\bin\verifyta.exe",
                r"C:\Program Files\UPPAAL-5.0.0\app\bin\verifyta.exe",
                r"/usr/local/bin/verifyta"
            ]
             for path in common_paths:
                if os.path.exists(path):
                    self.verifyta_path = path
                    break

    def verify(self, uppaal_xml: str, properties: List[Dict], timeout: int = 120, xml_path: str = None) -> Dict[str, Any]:
        """
        Execute UPPAAL verifyta verification
        
        Args:
            uppaal_xml: The UPPAAL model XML string
            properties: List of properties to verify
            timeout: Timeout in seconds
            xml_path: Optional path to save/use the XML file. If None, a temp file is used.
            
        Returns:
            Dictionary with verification results
        """
        if not self.verifyta_path or not os.path.exists(self.verifyta_path):
            return {
                "success": False,
                "error": "verifyta.exe not found",
                "all_passed": False,
                "property_results": [],
                "counterexamples": [],
                "execution_time": 0
            }

        # Save XML to file
        temp_file_used = False
        if not xml_path:
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8')
            xml_path = temp_file.name
            temp_file.close()
            temp_file_used = True
            
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(uppaal_xml)
        
        try:
            start_time = time.time()
            # verifyta [options] <model>
            # If queries are in the model, we just pass the model.
            result = subprocess.run(
                [self.verifyta_path, xml_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            execution_time = time.time() - start_time
            
            output = result.stdout + result.stderr
            
            # Parse output
            satisfied_count = output.count("Formula is satisfied")
            failed_count = output.count("Formula is NOT satisfied")
            
            # Extract detailed results
            property_results = []
            # We need to map output to properties. 
            # verifyta outputs results in order of queries in the file.
            # We assume the order matches 'properties' list if we generated it that way.
            
            # Simple parsing
            lines = output.split('\n')
            
            # Extract counterexamples from output
            counterexamples = []
            if failed_count > 0:
                # Parse trace information from UPPAAL output
                # This is complex, simplified for now
                current_property = None
                for i, line in enumerate(lines):
                    if "Formula is NOT satisfied" in line:
                        # Try to find which property failed
                        # This is hard without strict mapping.
                        counterexamples.append({
                            "property": "Unknown (see raw output)",
                            "trace": ["State transition extracted from verifyta output"],
                            "violation": "Property violated according to UPPAAL"
                        })
            
            all_passed = (failed_count == 0 and satisfied_count > 0)
            
            return {
                "success": True,
                "all_passed": all_passed,
                "property_results": property_results, # TODO: Better parsing
                "counterexamples": counterexamples,
                "execution_time": execution_time,
                "raw_output": output,
                "properties_verified": satisfied_count,
                "properties_failed": failed_count,
                "xml_path": xml_path
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout",
                "all_passed": False,
                "property_results": [],
                "counterexamples": [{"property": "TIMEOUT", "trace": [], "violation": "Verification timeout"}],
                "execution_time": timeout,
                "raw_output": "Verification timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "all_passed": False,
                "property_results": [],
                "counterexamples": [{"property": "ERROR", "trace": [], "violation": str(e)}],
                "execution_time": 0,
                "raw_output": f"Error: {str(e)}"
            }
        finally:
            if temp_file_used:
                try:
                    os.unlink(xml_path)
                except:
                    pass
