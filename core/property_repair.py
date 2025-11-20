"""
Property Repair Engine - Uses LLM to suggest fixes for failed properties
"""
from typing import List, Dict, Optional, Tuple
import re


class PropertyRepairEngine:
    """Uses LLM to analyze failed properties and suggest model/task corrections"""
    
    def __init__(self, llm_generator=None):
        """
        Initialize repair engine
        
        Args:
            llm_generator: Instance of LLMPropertyGenerator for LLM access
        """
        self.llm = llm_generator
    
    def analyze_failure(self, property_text: str, counterexample: str, tasks: List[Dict]) -> Dict:
        """
        Analyze why a property failed and suggest repairs
        
        Args:
            property_text: The failed property formula
            counterexample: UPPAAL counterexample trace
            tasks: Current task configuration
            
        Returns:
            Dictionary with analysis and repair suggestions
        """
        result = {
            'failure_type': self._classify_failure(property_text, counterexample),
            'root_cause': None,
            'suggested_fixes': [],
            'llm_explanation': None,
            'parameter_adjustments': []
        }
        
        # Classify the type of failure
        failure_type = result['failure_type']
        
        # Generate repair suggestions based on failure type
        if failure_type == 'deadline_miss':
            result['suggested_fixes'] = self._suggest_deadline_fixes(tasks, counterexample)
        elif failure_type == 'priority_inversion':
            result['suggested_fixes'] = self._suggest_priority_fixes(tasks, counterexample)
        elif failure_type == 'deadlock':
            result['suggested_fixes'] = self._suggest_deadlock_fixes(tasks)
        elif failure_type == 'liveness':
            result['suggested_fixes'] = self._suggest_liveness_fixes(tasks, counterexample)
        
        # Use LLM for deeper analysis if available
        if self.llm:
            result['llm_explanation'] = self._get_llm_analysis(
                property_text, counterexample, tasks
            )
        
        return result
    
    def _classify_failure(self, property_text: str, counterexample: str) -> str:
        """Classify the type of property failure"""
        
        property_lower = property_text.lower()
        counter_lower = counterexample.lower()
        
        # Check for deadline violations
        if 'deadline' in property_lower or 'done' in property_lower:
            if 'deadline' in counter_lower or 'time' in counter_lower:
                return 'deadline_miss'
        
        # Check for priority violations
        if 'priority' in property_lower or 'preempt' in property_lower:
            return 'priority_inversion'
        
        # Check for deadlock
        if 'deadlock' in property_lower or 'A[] not deadlock' in property_text:
            return 'deadlock'
        
        # Check for liveness issues
        if 'A<>' in property_text or 'E<>' in property_text:
            return 'liveness'
        
        # Check for mutual exclusion
        if 'mutex' in property_lower or 'simultaneously' in property_lower:
            return 'mutual_exclusion'
        
        return 'unknown'
    
    def _suggest_deadline_fixes(self, tasks: List[Dict], counterexample: str) -> List[str]:
        """Suggest fixes for deadline misses"""
        suggestions = []
        
        # Analyze which task missed deadline from counterexample
        missed_tasks = self._extract_deadline_violators(counterexample, tasks)
        
        for task in missed_tasks:
            task_name = task.get('task_name', 'Unknown')
            period = task.get('period', 0)
            deadline = task.get('deadline', 0)
            execution = task.get('max_execution', task.get('min_execution', 0))
            
            # Suggest increasing deadline
            new_deadline = int(execution * 1.5)
            suggestions.append(
                f"📊 Increase deadline for '{task_name}' from {deadline} to {new_deadline}"
            )
            
            # Suggest reducing execution time
            new_execution = int(deadline * 0.7)
            suggestions.append(
                f"⚡ Reduce execution time for '{task_name}' from {execution} to {new_execution}"
            )
            
            # Suggest increasing period
            new_period = int(period * 1.5)
            suggestions.append(
                f"📅 Increase period for '{task_name}' from {period} to {new_period}"
            )
        
        if not suggestions:
            suggestions.append("💡 Increase task deadlines or reduce execution times")
        
        return suggestions
    
    def _suggest_priority_fixes(self, tasks: List[Dict], counterexample: str) -> List[str]:
        """Suggest fixes for priority inversion"""
        suggestions = []
        
        # Sort by current priority
        sorted_tasks = sorted(tasks, key=lambda t: t.get('priority') or 999)
        
        # Suggest priority reassignment based on periods (Rate Monotonic)
        suggestions.append("🔄 Reassign priorities using Rate Monotonic (shorter period = higher priority):")
        
        period_sorted = sorted(tasks, key=lambda t: t.get('period') or 999)
        for idx, task in enumerate(period_sorted):
            task_name = task.get('task_name', 'Unknown')
            current_priority = task.get('priority', 0)
            suggested_priority = idx + 1
            
            if current_priority != suggested_priority:
                suggestions.append(
                    f"   • '{task_name}': Priority {current_priority} → {suggested_priority}"
                )
        
        # Suggest deadline monotonic if deadlines differ from periods
        suggestions.append("⏰ Alternative: Use Deadline Monotonic (shorter deadline = higher priority)")
        
        return suggestions
    
    def _suggest_deadlock_fixes(self, tasks: List[Dict]) -> List[str]:
        """Suggest fixes for deadlock"""
        return [
            "🔓 Enable preemptive scheduling (USE_SHARED_SCHEDULER = True)",
            "🔄 Review task synchronization and resource locks",
            "⚡ Ensure tasks can transition between states",
            "🔍 Check for circular dependencies in task execution"
        ]
    
    def _suggest_liveness_fixes(self, tasks: List[Dict], counterexample: str) -> List[str]:
        """Suggest fixes for liveness violations"""
        suggestions = []
        
        # Calculate total utilization
        total_util = sum(
            task.get('max_execution', task.get('min_execution', 0)) / task.get('period', 1)
            for task in tasks if task.get('period', 0) > 0
        )
        
        if total_util > 1.0:
            suggestions.append(
                f"⚠️ System overloaded: Utilization = {total_util:.2%} > 100%"
            )
            suggestions.append("💡 Reduce total CPU usage by:")
            suggestions.append("   • Increasing task periods")
            suggestions.append("   • Reducing execution times")
            suggestions.append("   • Removing or deferring low-priority tasks")
        else:
            suggestions.append("🔄 Enable priority-based preemption")
            suggestions.append("⚡ Check for tasks stuck in waiting states")
            suggestions.append("🔍 Verify scheduler dispatches all ready tasks")
        
        return suggestions
    
    def _extract_deadline_violators(self, counterexample: str, tasks: List[Dict]) -> List[Dict]:
        """Extract which tasks violated their deadlines from counterexample"""
        violators = []
        
        for task in tasks:
            task_name = task.get('task_name', '')
            if task_name in counterexample:
                # Check if task appears with deadline violation indicators
                if 'deadline' in counterexample.lower() or task_name in counterexample:
                    violators.append(task)
        
        return violators if violators else tasks  # Return all if can't determine
    
    def _get_llm_analysis(self, property_text: str, counterexample: str, tasks: List[Dict]) -> str:
        """Use LLM to provide detailed failure analysis"""
        
        if not self.llm:
            return None
        
        # Construct prompt for LLM
        task_desc = "\n".join(
            f"- {t.get('task_name')}: Period={t.get('period')}, "
            f"Deadline={t.get('deadline')}, Execution={t.get('max_execution', t.get('min_execution'))}, "
            f"Priority={t.get('priority')}"
            for t in tasks
        )
        
        prompt = f"""You are a real-time systems expert analyzing a verification failure.

**Failed Property:**
{property_text}

**Task Configuration:**
{task_desc}

**Counterexample (excerpt):**
{counterexample[:500]}...

Analyze WHY this property failed and suggest 2-3 specific, actionable fixes.
Focus on parameter adjustments (periods, deadlines, priorities, execution times).
Be concise and technical.

Analysis:"""
        
        try:
            # Use LLM's generate method
            response = self.llm._query_ollama(prompt, max_tokens=300)
            return response.strip()
        except Exception as e:
            return f"LLM analysis unavailable: {str(e)}"
    
    def generate_repair_suggestions_html(self, repair_result: Dict) -> str:
        """Generate HTML for repair suggestions"""
        
        failure_type = repair_result.get('failure_type', 'unknown')
        fixes = repair_result.get('suggested_fixes', [])
        llm_explanation = repair_result.get('llm_explanation')
        
        failure_icons = {
            'deadline_miss': '⏰',
            'priority_inversion': '🔄',
            'deadlock': '🔒',
            'liveness': '♾️',
            'mutual_exclusion': '🚫',
            'unknown': '❓'
        }
        
        icon = failure_icons.get(failure_type, '❓')
        
        html = f"""
        <div class="property-repair-suggestions">
            <div class="alert alert-warning">
                <h4>{icon} Failure Analysis: {failure_type.replace('_', ' ').title()}</h4>
            </div>
            
            <h5>🔧 Suggested Fixes:</h5>
            <ul class="list-group mb-3">
        """
        
        for fix in fixes:
            html += f"<li class='list-group-item'>{fix}</li>"
        
        html += "</ul>"
        
        if llm_explanation:
            html += f"""
            <div class="card">
                <div class="card-header">
                    <strong>🤖 LLM Expert Analysis</strong>
                </div>
                <div class="card-body">
                    <pre class="mb-0" style="white-space: pre-wrap;">{llm_explanation}</pre>
                </div>
            </div>
            """
        
        html += "</div>"
        
        return html
