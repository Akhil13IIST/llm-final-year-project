"""
Priority Validation Module
Handles extraction, validation, and auto-repair of task priorities
"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class PriorityIssue:
    task_id: int
    task_name: str
    issue_type: str  # 'missing', 'duplicate', 'invalid'
    severity: str  # 'error', 'warning'
    message: str
    suggested_fix: Optional[int] = None

class PriorityValidator:
    def __init__(self, strict_mode: bool = False):
        """
        Args:
            strict_mode: If True, block on errors. If False, auto-fix with warnings.
        """
        self.strict_mode = strict_mode
        self.issues: List[PriorityIssue] = []

    @classmethod
    def validate_priorities(cls, tasks: List[Dict], strict_mode: bool = False) -> Tuple[bool, Dict]:
        """Convenience wrapper to validate priority assignments without manual instantiation.

        Returns a tuple ``(is_valid, report_dict)`` mirroring :meth:`get_report`.
        """
        validator = cls(strict_mode=strict_mode)

        # Ensure every task exposes a priority value
        for idx, task in enumerate(tasks):
            priority = task.get('priority')
            name = task.get('task_name', f'Task{idx + 1}')
            if priority is None:
                validator.issues.append(PriorityIssue(
                    task_id=task.get('task_id', idx),
                    task_name=name,
                    issue_type='missing',
                    severity='error' if strict_mode else 'warning',
                    message=f'No priority specified for task {name}',
                    suggested_fix=5
                ))
                if not strict_mode:
                    task['priority'] = 5
            elif not (1 <= int(priority) <= 10):
                validator.issues.append(PriorityIssue(
                    task_id=task.get('task_id', idx),
                    task_name=name,
                    issue_type='invalid',
                    severity='error',
                    message=f'Priority {priority} out of range (1-10)',
                    suggested_fix=max(1, min(10, int(priority)))
                ))
                if not strict_mode:
                    task['priority'] = max(1, min(10, int(priority)))

        unique_ok = validator.validate_uniqueness(tasks)
        report = validator.get_report()
        is_valid = unique_ok and not report['has_errors']
        return is_valid, report
    
    def extract_priority_ada(self, ada_code: str, task_name: str) -> Optional[int]:
        """Extract priority from Ada pragma Priority directive"""
        # Pattern: pragma Priority(N) OR Priority(N)
        pattern = rf'(?:task\s+{task_name}.*?pragma\s+Priority\s*\(\s*(\d+)\s*\))|(?:Priority\s*\(\s*(\d+)\s*\))'
        match = re.search(pattern, ada_code, re.DOTALL | re.IGNORECASE)
        
        if match:
            priority = int(match.group(1) or match.group(2))
            if not (1 <= priority <= 10):
                self.issues.append(PriorityIssue(
                    task_id=-1,
                    task_name=task_name,
                    issue_type='invalid',
                    severity='error',
                    message=f'Priority {priority} out of range (1-10)',
                    suggested_fix=max(1, min(10, priority))
                ))
                return None if self.strict_mode else max(1, min(10, priority))
            return priority
        
        # Missing priority
        self.issues.append(PriorityIssue(
            task_id=-1,
            task_name=task_name,
            issue_type='missing',
            severity='warning' if not self.strict_mode else 'error',
            message=f'No priority specified for task {task_name}',
            suggested_fix=5  # Default medium priority
        ))
        
        return None if self.strict_mode else 5
    
    def extract_priority_python(self, python_code: str, class_name: str) -> Optional[int]:
        """Extract priority from Python class PRIORITY attribute"""
        # Pattern: PRIORITY = N
        pattern = rf'class\s+{class_name}.*?PRIORITY\s*=\s*(\d+)'
        match = re.search(pattern, python_code, re.DOTALL | re.IGNORECASE)
        
        if match:
            priority = int(match.group(1))
            if not (1 <= priority <= 10):
                self.issues.append(PriorityIssue(
                    task_id=-1,
                    task_name=class_name,
                    issue_type='invalid',
                    severity='error',
                    message=f'Priority {priority} out of range (1-10)',
                    suggested_fix=max(1, min(10, priority))
                ))
                return None if self.strict_mode else max(1, min(10, priority))
            return priority
        
        self.issues.append(PriorityIssue(
            task_id=-1,
            task_name=class_name,
            issue_type='missing',
            severity='warning' if not self.strict_mode else 'error',
            message=f'No PRIORITY specified for class {class_name}',
            suggested_fix=5
        ))
        
        return None if self.strict_mode else 5
    
    def validate_uniqueness(self, tasks: List[Dict]) -> bool:
        """Check for duplicate priorities"""
        priorities = [t.get('priority') for t in tasks if t.get('priority') is not None]
        
        if len(priorities) != len(set(priorities)):
            # Find duplicates
            seen = set()
            duplicates = set()
            for p in priorities:
                if p in seen:
                    duplicates.add(p)
                seen.add(p)
            
            for dup in duplicates:
                dup_tasks = [t['task_name'] for t in tasks if t.get('priority') == dup]
                self.issues.append(PriorityIssue(
                    task_id=-1,
                    task_name=', '.join(dup_tasks),
                    issue_type='duplicate',
                    severity='error',
                    message=f'Duplicate priority {dup} found in tasks: {", ".join(dup_tasks)}'
                ))
            
            return False
        
        return True
    
    def auto_fix_priorities(self, tasks: List[Dict]) -> List[Dict]:
        """Auto-fix duplicate priorities using Rate Monotonic principle"""
        if self.strict_mode and not self.validate_uniqueness(tasks):
            return tasks  # Don't auto-fix in strict mode
        
        # Sort by period (shorter period = higher priority)
        sorted_tasks = sorted(tasks, key=lambda t: t.get('period') or 999999)
        
        # Assign priorities 10 (highest) to 1 (lowest)
        for i, task in enumerate(sorted_tasks):
            old_priority = task.get('priority', 5)
            new_priority = max(1, 10 - i)
            
            if old_priority != new_priority:
                self.issues.append(PriorityIssue(
                    task_id=task.get('task_id', -1),
                    task_name=task.get('task_name', 'Unknown'),
                    issue_type='auto_fixed',
                    severity='warning',
                    message=f'Auto-fixed priority from {old_priority} to {new_priority} (Rate Monotonic)',
                    suggested_fix=new_priority
                ))
            
            task['priority'] = new_priority
            task['priority_auto_fixed'] = (old_priority != new_priority)
        
        return tasks
    
    def get_report(self) -> Dict:
        """Generate validation report"""
        errors = [i for i in self.issues if i.severity == 'error']
        warnings = [i for i in self.issues if i.severity == 'warning']
        
        return {
            'has_errors': len(errors) > 0,
            'has_warnings': len(warnings) > 0,
            'errors': [
                {
                    'task': i.task_name,
                    'type': i.issue_type,
                    'message': i.message,
                    'fix': i.suggested_fix
                }
                for i in errors
            ],
            'warnings': [
                {
                    'task': i.task_name,
                    'type': i.issue_type,
                    'message': i.message,
                    'fix': i.suggested_fix
                }
                for i in warnings
            ],
            'strict_mode': self.strict_mode
        }
