"""
Schedulability Analyzer Module
Semantic validation and feasibility checking
"""
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class SchedulabilityResult:
    is_schedulable: bool
    total_utilization: float
    ll_bound: float  # Liu & Layland bound
    failed_tasks: List[str]
    warnings: List[str]
    suggestions: List[str]

class SchedulabilityAnalyzer:
    def __init__(self, allow_unschedulable: bool = False):
        """
        Args:
            allow_unschedulable: If False, block verification on unschedulable systems
        """
        self.allow_unschedulable = allow_unschedulable
    
    def analyze(self, tasks: List[Dict]) -> SchedulabilityResult:
        """Perform comprehensive schedulability analysis"""
        n = len(tasks)
        
        # Validate tasks have required fields and set defaults if missing
        validated_tasks = []
        for task in tasks:
            validated_task = task.copy()
            # Ensure all numeric fields have valid values
            # Handle different field names for execution time
            exec_time = task.get('execution_time') or task.get('max_execution') or task.get('min_execution') or 10
            validated_task['execution_time'] = exec_time
            validated_task['period'] = task.get('period') or 100
            validated_task['deadline'] = task.get('deadline') or validated_task['period']
            validated_task['priority'] = task.get('priority') or 5
            validated_tasks.append(validated_task)
        
        # Calculate total utilization
        total_util = sum(
            task['execution_time'] / task['period'] 
            for task in validated_tasks
        )
        
        # Liu & Layland bound: n(2^(1/n) - 1)
        ll_bound = n * (2 ** (1/n) - 1)
        
        # Check basic LL test
        is_schedulable_ll = total_util <= ll_bound
        
        # Response time analysis for exact test
        failed_tasks = []
        warnings = []
        suggestions = []
        
        # Sort by priority (higher number = higher priority)
        sorted_tasks = sorted(validated_tasks, key=lambda t: -t.get('priority', 5))
        
        for task in sorted_tasks:
            response_time = self._calculate_response_time(task, validated_tasks)
            
            if response_time > task['deadline']:
                failed_tasks.append(task['task_name'])
                suggestions.append(
                    f"⚠️ {task['task_name']}: Response time ({response_time:.1f}ms) > Deadline ({task['deadline']}ms). "
                    f"Suggestions: 1) Reduce execution time, 2) Increase period, 3) Increase priority"
                )
        
        # Generate warnings
        if total_util > 1.0:
            warnings.append(
                f"❌ Total utilization ({total_util*100:.1f}%) exceeds 100%. System is DEFINITELY unschedulable."
            )
            suggestions.append(
                "🔧 System overload! Options: "
                "1) Increase task periods, "
                "2) Reduce execution times, "
                "3) Remove or defer lower-priority tasks"
            )
        elif total_util > ll_bound:
            warnings.append(
                f"⚠️ Utilization ({total_util*100:.1f}%) exceeds LL bound ({ll_bound*100:.1f}%). "
                f"Schedulability not guaranteed by LL test, but may still be feasible."
            )
        
        # Check for priority inversion risks
        priority_warnings = self._check_priority_inversion(validated_tasks)
        warnings.extend(priority_warnings)
        
        is_schedulable = len(failed_tasks) == 0 and total_util <= 1.0
        
        return SchedulabilityResult(
            is_schedulable=is_schedulable,
            total_utilization=total_util,
            ll_bound=ll_bound,
            failed_tasks=failed_tasks,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _calculate_response_time(self, task: Dict, all_tasks: List[Dict]) -> float:
        """Calculate worst-case response time using iterative method"""
        C_i = task['execution_time']
        T_i = task['period']
        P_i = task.get('priority', 5)
        
        # Initial response time = execution time
        R_i = C_i
        
        # Iterative calculation (max 100 iterations)
        for iteration in range(100):
            R_new = C_i
            
            # Add interference from higher priority tasks
            for hp_task in all_tasks:
                if hp_task.get('priority', 5) > P_i:
                    C_j = hp_task['execution_time']
                    T_j = hp_task['period']
                    R_new += math.ceil(R_i / T_j) * C_j
            
            # Convergence check
            if abs(R_new - R_i) < 0.01:
                return R_new
            
            R_i = R_new
            
            # Divergence check
            if R_i > task['deadline'] * 2:
                return R_i  # Give up, clearly unschedulable
        
        return R_i
    
    def _check_priority_inversion(self, tasks: List[Dict]) -> List[str]:
        """Check for priority inversion patterns"""
        warnings = []
        
        # Check if shorter period tasks have lower priority
        for i, task_i in enumerate(tasks):
            for task_j in tasks[i+1:]:
                if (task_i['period'] < task_j['period'] and 
                    task_i.get('priority', 5) < task_j.get('priority', 5)):
                    
                    warnings.append(
                        f"⚠️ Priority Inversion: {task_i['task_name']} (period={task_i['period']}ms, priority={task_i['priority']}) "
                        f"has shorter period but lower priority than {task_j['task_name']} (period={task_j['period']}ms, priority={task_j['priority']}). "
                        f"Consider Rate Monotonic scheduling."
                    )
        
        return warnings
    
    def suggest_adjustments(self, result: SchedulabilityResult, tasks: List[Dict]) -> Dict:
        """Generate specific adjustment suggestions"""
        if result.is_schedulable:
            return {'status': 'ok', 'message': '✅ System is schedulable'}
        
        # Validate tasks have required fields
        validated_tasks = []
        for task in tasks:
            validated_task = task.copy()
            validated_task['execution_time'] = task.get('execution_time') or 10
            validated_task['period'] = task.get('period') or 100
            validated_task['deadline'] = task.get('deadline') or validated_task['period']
            validated_task['priority'] = task.get('priority') or 5
            validated_tasks.append(validated_task)
        
        adjustments = {
            'status': 'needs_adjustment',
            'message': '❌ System is not schedulable. Here are specific fixes:',
            'options': []
        }
        
        # Option 1: Scale periods
        if result.total_utilization > 1.0:
            scale_factor = 1.0 / result.total_utilization * 1.1  # 10% margin
            adjustments['options'].append({
                'type': 'scale_periods',
                'description': f'Increase all task periods by {((1/scale_factor - 1)*100):.0f}%',
                'details': [
                    {'task': t['task_name'], 'current_period': t['period'], 'suggested_period': int(t['period'] / scale_factor)}
                    for t in validated_tasks
                ]
            })
        
        # Option 2: Reduce execution times
        if result.failed_tasks:
            adjustments['options'].append({
                'type': 'reduce_execution',
                'description': 'Reduce execution times for failed tasks',
                'details': [
                    {
                        'task': t['task_name'], 
                        'current_exec': t['execution_time'],
                        'suggested_exec': int(t['execution_time'] * 0.8),
                        'reason': 'Missed deadline in analysis'
                    }
                    for t in validated_tasks if t['task_name'] in result.failed_tasks
                ]
            })
        
        # Option 3: Remove low-priority tasks
        sorted_by_priority = sorted(validated_tasks, key=lambda t: t.get('priority', 5))
        adjustments['options'].append({
            'type': 'remove_tasks',
            'description': 'Consider deferring or removing lowest priority tasks',
            'details': [
                {'task': t['task_name'], 'priority': t.get('priority', 5), 'utilization': f"{(t['execution_time']/t['period']*100):.1f}%"}
                for t in sorted_by_priority[:2]  # Suggest removing 2 lowest
            ]
        })
        
        return adjustments
    
    def suggest_periods(self, tasks: List[Dict], target_utilization: float = 0.69) -> Dict[str, int]:
        """
        Suggest adjusted periods to achieve target utilization
        
        Args:
            tasks: Original task set
            target_utilization: Desired utilization (default: RM bound for 3 tasks)
            
        Returns:
            Dictionary mapping task names to suggested periods
        """
        suggestions = {}
        
        # Calculate current utilization
        current_util = 0.0
        for task in tasks:
            period = task.get('period', 1)
            execution = task.get('execution_time') or task.get('max_execution') or 10
            if period > 0:
                current_util += execution / period
        
        if current_util == 0:
            return suggestions
        
        scaling_factor = current_util / target_utilization
        
        for task in tasks:
            task_name = task.get('task_name', 'Unknown')
            current_period = task.get('period', 1)
            suggested_period = int(current_period * scaling_factor)
            
            # Round to nearest "nice" number
            suggested_period = self._round_to_nice_number(suggested_period)
            
            suggestions[task_name] = suggested_period
        
        return suggestions
    
    def _round_to_nice_number(self, value: int) -> int:
        """Round to nearest 'nice' number (10, 20, 50, 100, 200, 500, etc.)"""
        if value < 10:
            return value
        
        magnitude = 10 ** (len(str(value)) - 1)
        normalized = value / magnitude
        
        if normalized < 2:
            nice = 2
        elif normalized < 5:
            nice = 5
        else:
            nice = 10
        
        return int(nice * magnitude)

    def generate_analysis_html(self, result: SchedulabilityResult) -> str:
        """Generate HTML report for schedulability analysis"""
        
        status_class = 'success' if result.is_schedulable else 'danger'
        status_icon = '✅' if result.is_schedulable else '❌'
        
        html = f"""
        <div class="schedulability-analysis">
            <div class="alert alert-{status_class}">
                <h4>{status_icon} Schedulability Analysis</h4>
                <p><strong>Status:</strong> {'SCHEDULABLE' if result.is_schedulable else 'NOT SCHEDULABLE'}</p>
                <p><strong>Total Utilization:</strong> {result.total_utilization:.3f} ({result.total_utilization * 100:.1f}%)</p>
                <p><strong>RM Bound:</strong> {result.ll_bound:.3f} ({result.ll_bound * 100:.1f}%)</p>
            </div>
            
            <h5>Analysis Details</h5>
            <ul class="list-group">
        """
        
        if result.failed_tasks:
            html += f"<li class='list-group-item list-group-item-danger'><strong>Failed Tasks:</strong> {', '.join(result.failed_tasks)}</li>"
            
        for warning in result.warnings:
            html += f"<li class='list-group-item list-group-item-warning'>{warning}</li>"
            
        html += """
            </ul>
            
            <h5>Suggestions</h5>
            <ul class="list-group">
        """
        
        for suggestion in result.suggestions:
            html += f"<li class='list-group-item'>{suggestion}</li>"
        
        html += """
            </ul>
        </div>
        """
        
        return html
