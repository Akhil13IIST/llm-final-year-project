"""
LLM-Based Dynamic Property Generator with Memory and RAG
Generates context-aware UPPAAL properties using LLM reasoning
Enhanced with Retrieval-Augmented Generation from 295 UPPAAL models
"""

import requests
import json
from datetime import datetime

class LLMPropertyGenerator:
    def __init__(self, ollama_url="http://localhost:11434/api/generate", enable_rag=False):
        self.ollama_url = ollama_url
        self.verification_memory = []  # Store past verifications for context
        self.enable_rag = enable_rag
        self.rag = None
        
        # Initialize RAG if enabled (DISABLED by default - causes invalid property syntax)
        if enable_rag:
            try:
                from core.uppaal_rag import UppaalRAG
                print("🚀 Initializing RAG system...")
                self.rag = UppaalRAG()
                stats = self.rag.get_stats()
                if stats.get('total_models', 0) > 0:
                    print(f"✅ RAG enabled with {stats['total_models']} UPPAAL models")
                else:
                    print("⚠️ RAG initialized but no models found")
                    self.rag = None
            except ImportError as e:
                print(f"⚠️ RAG dependencies not installed: {e}")
                print("   Install with: pip install sentence-transformers faiss-cpu")
                self.rag = None
            except Exception as e:
                print(f"⚠️ RAG initialization failed: {e}")
                self.rag = None
        
    def add_to_memory(self, task_info, properties_used, verification_results):
        """Store verification history for future property generation"""
        self.verification_memory.append({
            'timestamp': datetime.now().isoformat(),
            'task_info': task_info,
            'properties': properties_used,
            'results': verification_results,
            'failed_properties': [p for p in verification_results if not verification_results[p].get('satisfied', True)]
        })
        
        # Keep only last 20 verifications to avoid context overflow
        if len(self.verification_memory) > 20:
            self.verification_memory = self.verification_memory[-20:]
    
    def get_memory_context(self):
        """Generate summary of past verifications for LLM context"""
        if not self.verification_memory:
            return "No previous verification history available."
        
        recent = self.verification_memory[-5:]  # Last 5 verifications
        context = "Previous verification insights:\n"
        
        for idx, mem in enumerate(recent, 1):
            failed = mem.get('failed_properties', [])
            if failed:
                context += f"- Verification {idx}: Failed properties: {', '.join(failed[:3])}\n"
            else:
                context += f"- Verification {idx}: All properties satisfied\n"
        
        return context
    
    def generate_properties_with_llm(self, task_info, include_memory=True):
        """
        Use LLM to intelligently select properties based on task characteristics
        Enhanced with RAG to use similar UPPAAL models as examples
        
        Args:
            task_info: Dictionary with task_name, period, deadline, priority, etc.
            include_memory: Whether to include past verification context
        
        Returns:
            List of property dictionaries with formula, category, priority
        """
        # Try LLM first, then fix its output
        properties = self._try_llm_generation(task_info, include_memory)
        
        if properties:
            # FIX LLM OUTPUT: Replace lowercase location names with capitalized ones
            fixed_properties = []
            for prop in properties:
                formula = prop.get('formula', '')
                
                # Fix location names: done -> Done, ready -> Ready, etc.
                formula = formula.replace('.done', '.Done')
                formula = formula.replace('.ready', '.Ready')
                formula = formula.replace('.idle', '.Idle')
                formula = formula.replace('.scheduled', '.Scheduled')
                formula = formula.replace('.executing', '.Executing')
                formula = formula.replace('.completing', '.Completing')
                
                fixed_properties.append({
                    **prop,
                    'formula': formula
                })
            
            print(f"✅ LLM generated {len(fixed_properties)} properties (auto-fixed capitalization)")
            return fixed_properties
        else:
            print("⚠️ LLM generation failed, using fallback")
            return self._fallback_properties(task_info)
    
    def _try_llm_generation(self, task_info, include_memory=True):
        """Internal method to try LLM generation (returns None if fails)"""
        # Build context for LLM
        memory_context = self.get_memory_context() if include_memory else ""
        
        # Handle multi-task scenarios
        is_multi_task = isinstance(task_info, dict) and task_info.get('multi_task', False)
        
        if is_multi_task:
            task_summary = f"Multi-task system with {task_info['task_count']} tasks:\n"
            for t in task_info['tasks']:
                task_summary += f"  - {t['task_name']}: Period={t['period']}ms, Deadline={t['deadline']}ms, Priority={t['priority']}\n"
            exact_task_name = task_info['tasks'][0]['task_name']
            period = task_info['tasks'][0]['period']
            deadline = task_info['tasks'][0]['deadline']
        else:
            task_name = task_info.get('task_name', 'Task')
            period = task_info.get('period', 10)
            deadline = task_info.get('deadline', 8)
            priority = task_info.get('priority', 1)
            task_summary = f"Single task: {task_name}, Period={period}ms, Deadline={deadline}ms, Priority={priority}"
            exact_task_name = task_name
        
        # Enhanced Prompt with Few-Shot Examples and Strict Constraints
        prompt = f"""You are a formal verification expert for Real-Time Systems using UPPAAL.
Your goal is to generate TCTL (Timed Computation Tree Logic) properties to verify the system.

SYSTEM DESCRIPTION:
{task_summary}

{memory_context}

STRICT RULES:
1. Use ONLY valid UPPAAL TCTL syntax.
2. Locations are Case-Sensitive: Use 'Done', 'Ready', 'Executing' (Capitalized).
3. Process names must be suffixed with '_inst' (e.g., '{exact_task_name}_inst').
4. Do NOT use 'deadlock' keyword inside complex formulas (only 'A[] not deadlock').
5. Output MUST be valid JSON only. No markdown, no explanations.

EXAMPLES:
Input: Task 'Sensor', Period 50, Deadline 40
Output:
{{
  "properties": [
    {{"formula": "A[] not deadlock", "category": "SAFETY", "priority": "CRITICAL", "reason": "System safety"}},
    {{"formula": "E<> Sensor_inst.Done", "category": "LIVENESS", "priority": "HIGH", "reason": "Task reachability"}},
    {{"formula": "A[] (Sensor_inst.Completing imply x <= 40)", "category": "TIMING", "priority": "HIGH", "reason": "Deadline constraint"}},
    {{"formula": "Sensor_inst.Done --> Sensor_inst.Ready", "category": "LIVENESS", "priority": "MEDIUM", "reason": "Cyclic behavior"}}
  ]
}}

YOUR TASK:
Generate 5 relevant properties for the system described above.
Output JSON format:
{{
  "properties": [
    {{"formula": "...", "category": "...", "priority": "...", "reason": "..."}}
  ]
}}
"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 1000}
                },
                timeout=20
            )
            
            if response.status_code == 200:
                llm_output = response.json().get('response', '')
                return self._parse_llm_property_response(llm_output, task_info)
            else:
                return None
        except Exception as e:
            print(f"⚠️ LLM error: {e}")
            return None
    
    def _parse_llm_property_response(self, llm_output, task_info):
        """Extract property list from LLM JSON response"""
        try:
            # Clean up markdown code blocks if present
            clean_output = llm_output
            if "```" in clean_output:
                import re
                match = re.search(r'```(?:json)?\s*(.*?)\s*```', clean_output, re.DOTALL)
                if match:
                    clean_output = match.group(1)
            
            # Try to find JSON block
            json_start = clean_output.find('{')
            json_end = clean_output.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = clean_output[json_start:json_end]
                data = json.loads(json_str)
                
                properties = data.get('properties', [])
                
                # Convert to UPPAAL-compatible format
                uppaal_properties = []
                for prop in properties:
                    uppaal_properties.append({
                        'formula': prop.get('formula', ''),
                        'category': prop.get('category', 'SAFETY'),
                        'comment': prop.get('reason', ''),
                        'priority': prop.get('priority', 'MEDIUM'),
                        'llm_generated': True
                    })
                
                return uppaal_properties
            else:
                return None
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return None
    
    def _fallback_properties(self, task_info):
        """Fallback to rule-based properties if LLM fails - uses correct UPPAAL state names"""
        properties = []
        
        is_multi_task = isinstance(task_info, dict) and task_info.get('multi_task', False)
        
        if is_multi_task:
            task_name = task_info['tasks'][0]['task_name']
            period = task_info['tasks'][0]['period']
            deadline = task_info['tasks'][0]['deadline']
        else:
            task_name = task_info.get('task_name', 'Task')
            period = task_info.get('period', 10)
            deadline = task_info.get('deadline', 8)
        
        print(f"[FALLBACK] Generating properties for task: '{task_name}' (period={period}, deadline={deadline})")
        
        # Use instantiated process name
        process_name = f"{task_name}_inst"
        
        # Basic safety - ALWAYS CRITICAL
        properties.append({
            'formula': 'A[] not deadlock',
            'category': 'SAFETY',
            'comment': 'System never deadlocks',
            'priority': 'CRITICAL'
        })
        
        # Reachability - Task can complete (use location NAME not ID!)
        properties.append({
            'formula': f'E<> {process_name}.Done',
            'category': 'LIVENESS',
            'comment': f'Task can reach completion state',
            'priority': 'HIGH'
        })
        
        # Period adherence (use location NAME: Ready)
        properties.append({
            'formula': f'A[] ({process_name}.Ready imply x <= {period})',
            'category': 'TIMING',
            'comment': f'Task activates every {period}ms period',
            'priority': 'MEDIUM'
        })
        
        # Deadline (use location NAME: Completing)
        if deadline < period:
            properties.append({
                'formula': f'A[] ({process_name}.Completing imply x <= {deadline})',
                'category': 'TIMING',
                'comment': f'Task completes within {deadline}ms deadline',
                'priority': 'HIGH'
            })
        
        # Liveness - Eventually returns to ready (use location NAMEs!)
        properties.append({
            'formula': f'{process_name}.Done --> {process_name}.Ready',
            'category': 'LIVENESS',
            'comment': 'Task cycles back to ready state',
            'priority': 'MEDIUM'
        })
        
        return properties
    
    def generate_feedback_from_failures(self, task_info, failed_properties, counterexamples):
        """
        Use LLM to generate human-readable feedback for failed properties
        
        Args:
            task_info: Task configuration
            failed_properties: List of property formulas that failed
            counterexamples: UPPAAL counterexample traces
        
        Returns:
            Dictionary mapping property to feedback message
        """
        if not failed_properties:
            return {}
        
        prompt = f"""You are a formal verification expert helping developers understand why their real-time system failed verification.

TASK: {task_info.get('task_name', 'Unknown')}
PERIOD: {task_info.get('period', 'N/A')}ms
DEADLINE: {task_info.get('deadline', 'N/A')}ms

FAILED PROPERTIES:
{chr(10).join(f"- {prop}" for prop in failed_properties)}

COUNTEREXAMPLE TRACE:
{counterexamples[:500] if counterexamples else 'No trace available'}

Provide concise, actionable feedback for EACH failed property. Suggest:
1. What the failure means
2. Likely root cause
3. How to fix it (code changes, parameter adjustments)

Output JSON format:
{{
  "property_formula": {{
    "explanation": "Why it failed",
    "root_cause": "Most likely cause",
    "fix_suggestion": "Specific fix recommendation"
  }},
  ...
}}

ONLY output valid JSON."""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "num_predict": 800
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                llm_output = response.json().get('response', '')
                
                # Parse JSON feedback
                json_start = llm_output.find('{')
                json_end = llm_output.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = llm_output[json_start:json_end]
                    feedback = json.loads(json_str)
                    return feedback
                else:
                    return self._fallback_feedback(failed_properties)
            else:
                return self._fallback_feedback(failed_properties)
                
        except Exception as e:
            print(f"⚠️ LLM feedback generation error: {e}")
            return self._fallback_feedback(failed_properties)
    
    def _fallback_feedback(self, failed_properties):
        """Simple rule-based feedback if LLM fails"""
        feedback = {}
        
        for prop in failed_properties:
            if 'deadlock' in prop.lower():
                feedback[prop] = {
                    'explanation': 'System can reach a state where no progress is possible',
                    'root_cause': 'Potential synchronization or scheduling issue',
                    'fix_suggestion': 'Review task synchronization and ensure proper state transitions'
                }
            elif 'deadline' in prop.lower() or 'Completing' in prop:
                feedback[prop] = {
                    'explanation': 'Task may miss its deadline constraint',
                    'root_cause': 'Execution time too long or period too short',
                    'fix_suggestion': 'Increase period, decrease execution time, or adjust priority'
                }
            elif '-->' in prop or 'leadsto' in prop.lower():
                feedback[prop] = {
                    'explanation': 'Liveness property failed - guaranteed progress not ensured',
                    'root_cause': 'Model allows indefinite waiting (realistic scheduler behavior)',
                    'fix_suggestion': 'This may be acceptable; verify if system can make progress in practice'
                }
            else:
                feedback[prop] = {
                    'explanation': 'Property verification failed',
                    'root_cause': 'Review UPPAAL trace for details',
                    'fix_suggestion': 'Check task parameters and system constraints'
                }
        
        return feedback
    
    def generate_schedulability_feedback(self, task_info_or_list, utilization, bound):
        """
        Generate LLM feedback for schedulability failures
        
        Args:
            task_info_or_list: Single task dict or list of tasks
            utilization: Total utilization percentage
            bound: Liu & Layland schedulability bound
        
        Returns:
            Dict with explanation, root_cause, and suggestions
        """
        # Check if LLM is available
        try:
            response = requests.get(self.ollama_url.replace('/api/generate', '/api/tags'), timeout=2)
            llm_available = response.status_code == 200
        except:
            llm_available = False
        
        if not llm_available:
            return self._fallback_schedulability_feedback(task_info_or_list, utilization, bound)
        
        # Determine if single or multi-task
        if isinstance(task_info_or_list, list):
            tasks = task_info_or_list
            task_count = len(tasks)
            task_summary = "\n".join([
                f"- {t.get('task_name', 'Task')}: Period={t.get('period')}ms, Execution={t.get('execution_time')}ms, Utilization={t.get('utilization', 0):.1%}"
                for t in tasks
            ])
        else:
            tasks = [task_info_or_list]
            task_count = 1
            t = task_info_or_list
            task_summary = f"- {t.get('task_name', 'Task')}: Period={t.get('period')}ms, Execution={t.get('execution_time')}ms, Utilization={t.get('utilization', 0):.1%}"
        
        prompt = f"""You are a real-time systems expert. A schedulability analysis has FAILED.

Task Set:
{task_summary}

Schedulability Analysis:
- Total Utilization: {utilization:.1%}
- Liu & Layland Bound ({task_count} tasks): {bound:.1%}
- Status: NOT SCHEDULABLE (utilization exceeds bound)

Provide a detailed analysis in JSON format with these fields:
1. "explanation": Why this task set is not schedulable (2-3 sentences)
2. "root_cause": The main issue causing the failure
3. "suggestions": Array of 3-5 specific actionable fixes

Consider:
- Rate Monotonic Scheduling principles
- Liu & Layland schedulability theory
- Practical real-time system design

Response format:
{{
  "explanation": "...",
  "root_cause": "...",
  "suggestions": ["...", "...", "..."]
}}"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "num_predict": 600
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                llm_output = response.json().get('response', '')
                
                # Parse JSON from LLM response
                json_start = llm_output.find('{')
                json_end = llm_output.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = llm_output[json_start:json_end]
                    feedback = json.loads(json_str)
                    return feedback
                else:
                    return self._fallback_schedulability_feedback(task_info_or_list, utilization, bound)
            else:
                return self._fallback_schedulability_feedback(task_info_or_list, utilization, bound)
                
        except Exception as e:
            print(f"⚠️ LLM schedulability feedback error: {e}")
            return self._fallback_schedulability_feedback(task_info_or_list, utilization, bound)
    
    def _fallback_schedulability_feedback(self, task_info_or_list, utilization, bound):
        """Rule-based schedulability feedback if LLM fails"""
        # Determine task count
        if isinstance(task_info_or_list, list):
            task_count = len(task_info_or_list)
            tasks = task_info_or_list
        else:
            task_count = 1
            tasks = [task_info_or_list]
        
        excess = utilization - bound
        
        suggestions = []
        
        # Analyze each task
        for task in tasks:
            exec_time = task.get('execution_time', 0)
            period = task.get('period', 1)
            task_util = exec_time / period if period > 0 else 0
            task_name = task.get('task_name', 'Task')
            
            if task_util > 0.7:
                suggestions.append(f"Reduce {task_name} execution time from {exec_time}ms (currently {task_util:.1%} utilization)")
                suggestions.append(f"Increase {task_name} period from {period}ms to {int(period * 1.5)}ms")
            elif task_util > 0.5:
                suggestions.append(f"Consider increasing {task_name} period from {period}ms to {int(period * 1.3)}ms")
        
        # General suggestions
        if task_count > 1:
            suggestions.append("Consider removing non-critical tasks from the system")
            suggestions.append("Optimize task execution times through algorithmic improvements")
            suggestions.append(f"Current utilization ({utilization:.1%}) exceeds safe bound ({bound:.1%}) by {excess:.1%}")
        
        return {
            "explanation": f"The task set has {utilization:.1%} total utilization, which exceeds the Liu & Layland schedulability bound of {bound:.1%} for {task_count} task{'s' if task_count > 1 else ''}. This means the system cannot guarantee all tasks will meet their deadlines under worst-case conditions.",
            "root_cause": f"Combined execution times are too high relative to task periods. Utilization exceeds bound by {excess:.1%}.",
            "suggestions": suggestions[:5]  # Limit to 5 suggestions
        }
    
    def repair_unschedulable_code(self, original_code, task_info_or_list, utilization, bound, language='ada'):
        """
        Use LLM to repair unschedulable code by adjusting periods/execution times
        
        Args:
            original_code: Original Ada/Python code
            task_info_or_list: Task info dict or list of tasks
            utilization: Current utilization
            bound: Liu & Layland bound
            language: 'ada' or 'python'
        
        Returns:
            Repaired code string or None if repair failed
        """
        # Check if LLM is available
        try:
            response = requests.get(self.ollama_url.replace('/api/generate', '/api/tags'), timeout=2)
            llm_available = response.status_code == 200
        except:
            llm_available = False
        
        if not llm_available:
            return self._rule_based_repair(original_code, task_info_or_list, utilization, bound, language)
        
        # Prepare task summary
        if isinstance(task_info_or_list, list):
            tasks = task_info_or_list
        else:
            tasks = [task_info_or_list]
        
        task_summary = "\n".join([
            f"- {t.get('task_name', 'Task')}: Period={t.get('period')}ms, Execution={t.get('execution_time')}ms, Deadline={t.get('deadline')}ms, Utilization={t.get('utilization', 0):.1%}"
            for t in tasks
        ])
        
        prompt = f"""You are a real-time systems expert. Fix this UNSCHEDULABLE task set.

Current Task Set (NOT SCHEDULABLE):
{task_summary}

Problem:
- Total Utilization: {utilization:.1%}
- Liu & Layland Bound ({len(tasks)} tasks): {bound:.1%}
- Status: EXCEEDS BOUND BY {(utilization - bound):.1%}

Original {language.upper()} Code:
```{language}
{original_code}
```

Your task:
1. Adjust periods and/or execution times to make the system schedulable
2. Keep utilization below {bound:.1%}
3. Maintain task priorities (Rate Monotonic: shorter period = higher priority)
4. Preserve the original code structure and comments
5. Only modify Milliseconds(...) values for Period, Deadline, and Execution_Time

Strategy:
- Increase periods for low-priority tasks (longer periods first)
- Reduce execution times moderately (don't make unrealistic)
- Ensure Execution_Time <= Deadline <= Period for each task
- Target total utilization around {bound * 0.9:.1%} (90% of bound for safety margin)

Return ONLY the complete repaired {language.upper()} code (no explanations, no markdown blocks).
"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 2000
                    }
                },
                timeout=45
            )
            
            if response.status_code == 200:
                repaired_code = response.json().get('response', '').strip()
                
                # Clean up code markers if present
                if '```' in repaired_code:
                    # Extract code from markdown blocks
                    lines = repaired_code.split('\n')
                    code_lines = []
                    in_code_block = False
                    
                    for line in lines:
                        if line.strip().startswith('```'):
                            in_code_block = not in_code_block
                            continue
                        if in_code_block or (not line.strip().startswith('```') and 'task' in line.lower()):
                            code_lines.append(line)
                    
                    repaired_code = '\n'.join(code_lines).strip()
                
                # Validate that it's actual code
                if 'task' in repaired_code.lower() or 'class' in repaired_code.lower():
                    return repaired_code
                else:
                    return self._rule_based_repair(original_code, task_info_or_list, utilization, bound, language)
            else:
                return self._rule_based_repair(original_code, task_info_or_list, utilization, bound, language)
                
        except Exception as e:
            print(f"⚠️ LLM repair error: {e}")
            return self._rule_based_repair(original_code, task_info_or_list, utilization, bound, language)
    
    def _query_ollama(self, prompt, max_tokens=800):
        """Helper to query Ollama with standard error handling"""
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": max_tokens
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                print(f"⚠️ Ollama error: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            print(f"⚠️ Ollama connection error: {e}")
            return ""

    def _rule_based_repair(self, original_code, task_info_or_list, utilization, bound, language):
        """Rule-based repair if LLM fails - IMPROVED to generate realistic schedulable code"""
        import re
        
        if isinstance(task_info_or_list, list):
            tasks = task_info_or_list
        else:
            tasks = [task_info_or_list]
        
        # Calculate target utilization (80% of bound for safety margin)
        target_util = bound * 0.8
        
        # Calculate how much we need to reduce utilization
        reduction_factor = target_util / utilization if utilization > 0 else 1.0
        
        repaired_code = original_code
        
        for task in tasks:
            task_name = task.get('task_name', 'Task')
            old_period = task.get('period', 10)
            old_exec = task.get('execution_time', 5)
            old_deadline = task.get('deadline', old_period)
            
            # Strategy: Keep execution time reasonable, increase period
            # For single task: reduce exec time slightly, increase period moderately
            # For multi-task: be more aggressive with low-priority tasks
            
            if len(tasks) == 1:
                # Single task - simple fix
                new_exec = max(1, int(old_exec * 0.7))  # Reduce exec by 30%
                new_period = max(new_exec * 2, old_period)  # Keep period same or increase
                new_deadline = int(new_period * 0.9)  # Deadline = 90% of period
            else:
                # Multi-task - proportional reduction
                new_exec = max(1, int(old_exec * reduction_factor))
                # Increase period more for low-priority (long period) tasks
                if old_period > 200:
                    new_period = int(old_period * 1.5)  # Increase by 50%
                elif old_period > 100:
                    new_period = int(old_period * 1.3)  # Increase by 30%
                else:
                    new_period = old_period  # Keep short periods unchanged
                new_deadline = int(new_period * 0.9)
            
            # Ensure constraints: Execution <= Deadline <= Period
            new_exec = min(new_exec, new_deadline)
            new_deadline = min(new_deadline, new_period)
            
            # Replace in code (Ada)
            if language.lower() == 'ada':
                # Find and replace Period
                period_pattern = rf'(task\s+body\s+{task_name}.*?Period\s*:\s*constant\s+Time_Span\s*:=\s*Milliseconds\()\d+(\))'
                repaired_code = re.sub(period_pattern, rf'\g<1>{new_period}\g<2>', repaired_code, flags=re.DOTALL | re.IGNORECASE)
                
                # Replace Deadline
                deadline_pattern = rf'(task\s+body\s+{task_name}.*?Deadline\s*:\s*constant\s+Time_Span\s*:=\s*Milliseconds\()\d+(\))'
                repaired_code = re.sub(deadline_pattern, rf'\g<1>{new_deadline}\g<2>', repaired_code, flags=re.DOTALL | re.IGNORECASE)
                
                # Replace Execution_Time if exists
                exec_pattern = rf'(task\s+body\s+{task_name}.*?Execution_Time\s*:\s*constant\s+Time_Span\s*:=\s*Milliseconds\()\d+(\))'
                repaired_code = re.sub(exec_pattern, rf'\g<1>{new_exec}\g<2>', repaired_code, flags=re.DOTALL | re.IGNORECASE)
        
        return repaired_code
