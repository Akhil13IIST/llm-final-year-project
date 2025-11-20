"""
Property Pattern Library - Pre-built verification property templates
"""
from typing import List, Dict


class PropertyPatternLibrary:
    """Library of common verification property patterns for real-time systems"""
    
    @staticmethod
    def get_all_patterns() -> Dict[str, Dict]:
        """Get all available property patterns"""
        return {
            'safety': PropertyPatternLibrary.get_safety_patterns(),
            'liveness': PropertyPatternLibrary.get_liveness_patterns(),
            'real_time': PropertyPatternLibrary.get_realtime_patterns(),
            'resource': PropertyPatternLibrary.get_resource_patterns(),
            'communication': PropertyPatternLibrary.get_communication_patterns()
        }
    
    @staticmethod
    def get_safety_patterns() -> List[Dict]:
        """Safety properties - something bad never happens"""
        return [
            {
                'name': 'Mutual Exclusion',
                'pattern': 'A[] not ({entity1} and {entity2})',
                'description': 'Two entities never occur simultaneously',
                'parameters': ['entity1', 'entity2'],
                'example': 'A[] not (Task1.Executing and Task2.Executing)',
                'category': 'safety'
            },
            {
                'name': 'No Deadlock',
                'pattern': 'A[] not deadlock',
                'description': 'System never enters deadlock state',
                'parameters': [],
                'example': 'A[] not deadlock',
                'category': 'safety'
            },
            {
                'name': 'State Invariant',
                'pattern': 'A[] {condition}',
                'description': 'A condition always holds',
                'parameters': ['condition'],
                'example': 'A[] (cpu_lock >= -1 and cpu_lock < NUM_TASKS)',
                'category': 'safety'
            },
            {
                'name': 'Bounded Buffer',
                'pattern': 'A[] ({buffer_size} <= {max_size})',
                'description': 'Buffer never exceeds maximum size',
                'parameters': ['buffer_size', 'max_size'],
                'example': 'A[] (queue_length <= 10)',
                'category': 'safety'
            },
            {
                'name': 'Never Reach Bad State',
                'pattern': 'A[] not {bad_state}',
                'description': 'System never reaches an error state',
                'parameters': ['bad_state'],
                'example': 'A[] not Task1.Error',
                'category': 'safety'
            }
        ]
    
    @staticmethod
    def get_liveness_patterns() -> List[Dict]:
        """Liveness properties - something good eventually happens"""
        return [
            {
                'name': 'Eventually Reaches',
                'pattern': 'A<> {state}',
                'description': 'System eventually reaches a state on all paths',
                'parameters': ['state'],
                'example': 'A<> Task1.Done',
                'category': 'liveness'
            },
            {
                'name': 'Possibly Reaches',
                'pattern': 'E<> {state}',
                'description': 'System can possibly reach a state',
                'parameters': ['state'],
                'example': 'E<> (Task1.Done and Task2.Done)',
                'category': 'liveness'
            },
            {
                'name': 'Leads To',
                'pattern': '{state1} --> {state2}',
                'description': 'Whenever state1 holds, state2 will eventually hold',
                'parameters': ['state1', 'state2'],
                'example': 'Task1.Ready --> Task1.Executing',
                'category': 'liveness'
            },
            {
                'name': 'Infinitely Often',
                'pattern': 'A[] {state} --> A<> not {state}',
                'description': 'State occurs infinitely often (not continuously)',
                'parameters': ['state'],
                'example': 'A[] Task1.Executing --> A<> not Task1.Executing',
                'category': 'liveness'
            },
            {
                'name': 'Fair Scheduling',
                'pattern': 'A[] (A<> {task}.Executing)',
                'description': 'Task gets fair chance to execute',
                'parameters': ['task'],
                'example': 'A[] (A<> Task1.Executing)',
                'category': 'liveness'
            }
        ]
    
    @staticmethod
    def get_realtime_patterns() -> List[Dict]:
        """Real-time specific properties"""
        return [
            {
                'name': 'Deadline Guarantee',
                'pattern': 'A[] ({task}.Done imply {task}.{clock} <= {deadline})',
                'description': 'Task always completes within deadline',
                'parameters': ['task', 'clock', 'deadline'],
                'example': 'A[] (Task1.Done imply Task1.x <= DEADLINE)',
                'category': 'real_time'
            },
            {
                'name': 'Bounded Response',
                'pattern': '{request} --> {response} and ({clock} <= {bound})',
                'description': 'Response occurs within time bound after request',
                'parameters': ['request', 'response', 'clock', 'bound'],
                'example': 'Task1.Ready --> Task1.Executing and (x <= 100)',
                'category': 'real_time'
            },
            {
                'name': 'Periodic Execution',
                'pattern': 'A[] ({task}.Done imply ({task}.{clock} >= {period} - {jitter}))',
                'description': 'Task executes periodically with bounded jitter',
                'parameters': ['task', 'clock', 'period', 'jitter'],
                'example': 'A[] (Task1.Done imply (Task1.x >= PERIOD - 5))',
                'category': 'real_time'
            },
            {
                'name': 'Priority Enforcement',
                'pattern': 'A[] ({low_priority}.Executing and {high_priority}.Ready imply {high_priority}.Executing)',
                'description': 'Higher priority task preempts lower priority',
                'parameters': ['low_priority', 'high_priority'],
                'example': 'A[] (Task2.Executing and Task1.Ready imply Task1.Executing)',
                'category': 'real_time'
            },
            {
                'name': 'WCET Bound',
                'pattern': 'A[] ({task}.Executing imply {task}.{clock} <= {wcet})',
                'description': 'Task execution never exceeds worst-case time',
                'parameters': ['task', 'clock', 'wcet'],
                'example': 'A[] (Task1.Executing imply Task1.x <= MAX_EXECUTION)',
                'category': 'real_time'
            }
        ]
    
    @staticmethod
    def get_resource_patterns() -> List[Dict]:
        """Resource management properties"""
        return [
            {
                'name': 'Resource Mutual Exclusion',
                'pattern': 'A[] ({count_using_resource} <= 1)',
                'description': 'At most one entity uses resource at a time',
                'parameters': ['count_using_resource'],
                'example': 'A[] (cpu_lock == -1 or (cpu_lock >= 0 and cpu_lock < 3))',
                'category': 'resource'
            },
            {
                'name': 'Resource Always Released',
                'pattern': '{acquire} --> {release}',
                'description': 'Every resource acquisition leads to release',
                'parameters': ['acquire', 'release'],
                'example': 'Task1.Executing --> Task1.Done',
                'category': 'resource'
            },
            {
                'name': 'Bounded Waiting',
                'pattern': 'A[] ({waiting} imply {clock} <= {max_wait})',
                'description': 'Waiting for resource is bounded',
                'parameters': ['waiting', 'clock', 'max_wait'],
                'example': 'A[] (Task1.Scheduled imply x <= 100)',
                'category': 'resource'
            },
            {
                'name': 'No Resource Starvation',
                'pattern': 'A[] ({requesting} --> A<> {acquired})',
                'description': 'Request eventually leads to acquisition',
                'parameters': ['requesting', 'acquired'],
                'example': 'A[] (Task1.Scheduled --> A<> Task1.Executing)',
                'category': 'resource'
            }
        ]
    
    @staticmethod
    def get_communication_patterns() -> List[Dict]:
        """Communication and synchronization properties"""
        return [
            {
                'name': 'Message Ordering',
                'pattern': 'A[] ({send1} and not {received1} imply not {send2})',
                'description': 'Messages are received in order sent',
                'parameters': ['send1', 'received1', 'send2'],
                'example': 'A[] (msg1_sent and not msg1_received imply not msg2_sent)',
                'category': 'communication'
            },
            {
                'name': 'No Message Loss',
                'pattern': '{send} --> {receive}',
                'description': 'Every sent message is eventually received',
                'parameters': ['send', 'receive'],
                'example': 'msg_sent --> msg_received',
                'category': 'communication'
            },
            {
                'name': 'Bounded Channel',
                'pattern': 'A[] ({messages_in_transit} <= {capacity})',
                'description': 'Communication channel has bounded capacity',
                'parameters': ['messages_in_transit', 'capacity'],
                'example': 'A[] (queue_size <= 10)',
                'category': 'communication'
            },
            {
                'name': 'Synchronous Communication',
                'pattern': 'A[] ({send} imply {receive})',
                'description': 'Send and receive happen simultaneously',
                'parameters': ['send', 'receive'],
                'example': 'A[] (Task1.Sending imply Task2.Receiving)',
                'category': 'communication'
            }
        ]
    
    @staticmethod
    def instantiate_pattern(pattern: Dict, bindings: Dict[str, str]) -> Dict:
        """
        Instantiate a property pattern with concrete values
        
        Args:
            pattern: Pattern dictionary from library
            bindings: Dictionary mapping parameter names to concrete values
            
        Returns:
            Instantiated property dictionary
        """
        formula = pattern['pattern']
        
        # Replace each parameter with its binding
        for param, value in bindings.items():
            placeholder = f'{{{param}}}'
            formula = formula.replace(placeholder, value)
        
        return {
            'type': 'template',
            'name': pattern['name'],
            'formula': formula,
            'comment': pattern['description'],
            'category': pattern['category'],
            'pattern': pattern['name']
        }
    
    @staticmethod
    def suggest_patterns_for_system(tasks: List[Dict], system_type: str = 'general') -> List[Dict]:
        """
        Suggest relevant patterns based on system configuration
        
        Args:
            tasks: List of tasks in the system
            system_type: Type of system (general, real_time, communication, etc.)
            
        Returns:
            List of suggested property patterns with bindings
        """
        suggestions = []
        
        # Always suggest basic safety properties
        suggestions.append({
            'pattern_name': 'No Deadlock',
            'formula': 'A[] not deadlock',
            'reasoning': 'Fundamental safety property for all systems'
        })
        
        if len(tasks) > 1:
            # Suggest mutual exclusion
            task_names = [t.get('task_name', f'Task{i}') for i, t in enumerate(tasks)]
            for i in range(len(task_names)):
                for j in range(i + 1, min(i + 2, len(task_names))):  # Just first few pairs
                    suggestions.append({
                        'pattern_name': 'Mutual Exclusion',
                        'formula': f'A[] not ({task_names[i]}_inst.Executing and {task_names[j]}_inst.Executing)',
                        'reasoning': f'Ensure {task_names[i]} and {task_names[j]} don\'t execute simultaneously'
                    })
        
        # Suggest reachability for each task
        for task in tasks[:3]:  # Limit to first 3 tasks
            task_name = task.get('task_name', 'Task')
            suggestions.append({
                'pattern_name': 'Eventually Reaches',
                'formula': f'E<> {task_name}_inst.Done',
                'reasoning': f'Verify {task_name} can complete'
            })
        
        # If tasks have priorities, suggest priority enforcement
        if any(t.get('priority') for t in tasks):
            sorted_tasks = sorted(tasks, key=lambda t: t.get('priority', 999))
            if len(sorted_tasks) >= 2:
                high_pri = sorted_tasks[0].get('task_name', 'Task1')
                low_pri = sorted_tasks[-1].get('task_name', 'Task2')
                suggestions.append({
                    'pattern_name': 'Priority Enforcement',
                    'formula': f'A[] ({low_pri}_inst.Executing and {high_pri}_inst.Ready --> {high_pri}_inst.Executing)',
                    'reasoning': f'Higher priority {high_pri} should preempt lower priority {low_pri}'
                })
        
        # If tasks have deadlines, suggest deadline properties
        if any(t.get('deadline') for t in tasks):
            for task in tasks[:2]:  # First 2 tasks
                task_name = task.get('task_name', 'Task')
                deadline = task.get('deadline', 100)
                suggestions.append({
                    'pattern_name': 'Deadline Guarantee',
                    'formula': f'{task_name}_inst.Ready --> {task_name}_inst.Executing',
                    'reasoning': f'Ensure {task_name} makes progress toward deadline'
                })
        
        return suggestions
    
    @staticmethod
    def generate_pattern_library_html() -> str:
        """Generate HTML documentation for pattern library"""
        
        all_patterns = PropertyPatternLibrary.get_all_patterns()
        
        html = """
        <div class="pattern-library">
            <h3>📚 Property Pattern Library</h3>
            <p>Common verification property patterns for real-time systems</p>
        """
        
        category_names = {
            'safety': '🛡️ Safety Properties',
            'liveness': '♾️ Liveness Properties',
            'real_time': '⏱️ Real-Time Properties',
            'resource': '💾 Resource Properties',
            'communication': '📡 Communication Properties'
        }
        
        for category, patterns in all_patterns.items():
            html += f"""
            <div class="card mb-3">
                <div class="card-header">
                    <h4>{category_names.get(category, category.title())}</h4>
                </div>
                <div class="card-body">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Pattern</th>
                                <th>Formula</th>
                                <th>Description</th>
                                <th>Example</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for pattern in patterns:
                html += f"""
                            <tr>
                                <td><strong>{pattern['name']}</strong></td>
                                <td><code>{pattern['pattern']}</code></td>
                                <td>{pattern['description']}</td>
                                <td><small><code>{pattern['example']}</code></small></td>
                            </tr>
                """
            
            html += """
                        </tbody>
                    </table>
                </div>
            </div>
            """
        
        html += "</div>"
        return html
