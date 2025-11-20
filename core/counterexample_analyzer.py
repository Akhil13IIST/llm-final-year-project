"""
Counterexample Analyzer - Parse and visualize UPPAAL counterexamples
"""
import re
from typing import List, Dict, Tuple, Optional
import xml.etree.ElementTree as ET


class CounterexampleAnalyzer:
    """Analyzes UPPAAL counterexamples and generates visualizations"""
    
    def __init__(self):
        self.trace_steps = []
        self.task_executions = []
        
    def parse_counterexample(self, uppaal_output: str) -> Dict:
        """
        Parse UPPAAL counterexample trace from verification output
        
        Args:
            uppaal_output: Raw output from verifyta containing trace
            
        Returns:
            Dictionary with parsed trace information
        """
        result = {
            'has_counterexample': False,
            'property_violated': None,
            'trace_steps': [],
            'task_timeline': {},
            'total_time': 0,
            'visualization_data': []
        }
        
        # Check if there's a counterexample
        if 'Property is NOT satisfied' not in uppaal_output and 'FAIL' not in uppaal_output:
            return result
            
        result['has_counterexample'] = True
        
        # Extract property that failed
        prop_match = re.search(r'Verifying property.*?\n(.*?)\n', uppaal_output)
        if prop_match:
            result['property_violated'] = prop_match.group(1).strip()
        
        # Parse trace if available
        trace_section = self._extract_trace_section(uppaal_output)
        if trace_section:
            result['trace_steps'] = self._parse_trace_steps(trace_section)
            result['task_timeline'] = self._build_task_timeline(result['trace_steps'])
            result['total_time'] = self._calculate_total_time(result['trace_steps'])
            result['visualization_data'] = self._generate_visualization_data(result['trace_steps'])
        
        return result
    
    def _extract_trace_section(self, output: str) -> Optional[str]:
        """Extract the trace section from UPPAAL output"""
        # UPPAAL outputs trace in different formats
        # Look for state transitions
        match = re.search(r'State:.*?(?=\n\n|\Z)', output, re.DOTALL)
        if match:
            return match.group(0)
        return None
    
    def _parse_trace_steps(self, trace_text: str) -> List[Dict]:
        """Parse individual steps in the trace"""
        steps = []
        
        # Split into state transitions
        state_pattern = r'State:\s*\d+.*?(?=State:|\Z)'
        states = re.findall(state_pattern, trace_text, re.DOTALL)
        
        for idx, state in enumerate(states):
            step = {
                'step_number': idx,
                'time': self._extract_time(state),
                'active_tasks': self._extract_active_tasks(state),
                'cpu_lock': self._extract_cpu_lock(state),
                'task_states': self._extract_task_states(state),
                'transitions': self._extract_transitions(state)
            }
            steps.append(step)
        
        return steps
    
    def _extract_time(self, state_text: str) -> int:
        """Extract time value from state"""
        # Look for clock values
        time_match = re.search(r'(\w+)\s*=\s*(\d+)', state_text)
        if time_match:
            return int(time_match.group(2))
        return 0
    
    def _extract_active_tasks(self, state_text: str) -> List[str]:
        """Extract which tasks are active in this state"""
        tasks = []
        # Look for task instances in executing state
        task_pattern = r'(\w+)_inst\.(\w+)'
        matches = re.findall(task_pattern, state_text)
        for task_name, state in matches:
            if state == 'Executing':
                tasks.append(task_name)
        return tasks
    
    def _extract_cpu_lock(self, state_text: str) -> int:
        """Extract cpu_lock value"""
        lock_match = re.search(r'cpu_lock\s*=\s*(-?\d+)', state_text)
        if lock_match:
            return int(lock_match.group(1))
        return -1
    
    def _extract_task_states(self, state_text: str) -> Dict[str, str]:
        """Extract state of each task"""
        states = {}
        task_pattern = r'(\w+)_inst\.(\w+)'
        matches = re.findall(task_pattern, state_text)
        for task_name, state in matches:
            states[task_name] = state
        return states
    
    def _extract_transitions(self, state_text: str) -> List[str]:
        """Extract transitions taken"""
        transitions = []
        trans_pattern = r'Transition:\s*(.*?)(?=\n|$)'
        matches = re.findall(trans_pattern, state_text)
        transitions.extend(matches)
        return transitions
    
    def _build_task_timeline(self, steps: List[Dict]) -> Dict[str, List[Tuple[int, int, str]]]:
        """
        Build timeline showing when each task was executing
        
        Returns:
            Dict mapping task_name -> [(start_time, end_time, state), ...]
        """
        timeline = {}
        current_executing = {}
        
        for step in steps:
            time = step['time']
            
            # Track which tasks are executing
            for task, state in step['task_states'].items():
                if task not in timeline:
                    timeline[task] = []
                
                if state == 'Executing':
                    if task not in current_executing:
                        current_executing[task] = time
                elif task in current_executing:
                    # Task finished executing
                    start = current_executing[task]
                    timeline[task].append((start, time, 'Executing'))
                    del current_executing[task]
        
        # Close any remaining executions
        for task, start in current_executing.items():
            if steps:
                end_time = steps[-1]['time']
                timeline[task].append((start, end_time, 'Executing'))
        
        return timeline
    
    def _calculate_total_time(self, steps: List[Dict]) -> int:
        """Calculate total time in trace"""
        if not steps:
            return 0
        return max(step['time'] for step in steps)
    
    def _generate_visualization_data(self, steps: List[Dict]) -> List[Dict]:
        """Generate data structure for Gantt chart visualization"""
        viz_data = []
        
        for step in steps:
            for task, state in step['task_states'].items():
                viz_data.append({
                    'time': step['time'],
                    'task': task,
                    'state': state,
                    'cpu_lock': step['cpu_lock']
                })
        
        return viz_data
    
    def generate_gantt_chart_html(self, trace_result: Dict) -> str:
        """Generate HTML/JavaScript for interactive Gantt chart"""
        
        timeline = trace_result.get('task_timeline', {})
        total_time = trace_result.get('total_time', 0)
        
        if not timeline or total_time == 0:
            return "<p>No trace data available for visualization</p>"
        
        # Generate HTML with Chart.js
        html = f"""
        <div class="counterexample-visualization">
            <h3>Task Execution Timeline (Gantt Chart)</h3>
            <canvas id="ganttChart" width="800" height="{len(timeline) * 60 + 100}"></canvas>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
                const ctx = document.getElementById('ganttChart').getContext('2d');
                const tasks = {list(timeline.keys())};
                const totalTime = {total_time};
                
                const datasets = [
        """
        
        # Add dataset for each task
        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
        for idx, (task, executions) in enumerate(timeline.items()):
            color = colors[idx % len(colors)]
            data_points = []
            for start, end, state in executions:
                data_points.append(f"{{x: [{start}, {end}], y: '{task}'}}")
            
            html += f"""
                    {{
                        label: '{task}',
                        data: [{', '.join(data_points)}],
                        backgroundColor: '{color}',
                        borderColor: '{color}',
                        borderWidth: 1
                    }},
            """
        
        html += """
                ];
                
                const chart = new Chart(ctx, {
                    type: 'bar',
                    data: { datasets: datasets },
                    options: {
                        indexAxis: 'y',
                        scales: {
                            x: {
                                type: 'linear',
                                position: 'bottom',
                                title: { display: true, text: 'Time (ms)' }
                            },
                            y: {
                                title: { display: true, text: 'Tasks' }
                            }
                        },
                        plugins: {
                            legend: { display: true },
                            title: {
                                display: true,
                                text: 'Counterexample: Task Execution Timeline'
                            }
                        }
                    }
                });
            </script>
        </div>
        """
        
        return html
    
    def generate_trace_table_html(self, trace_result: Dict) -> str:
        """Generate HTML table showing trace steps"""
        
        steps = trace_result.get('trace_steps', [])
        if not steps:
            return "<p>No trace steps available</p>"
        
        html = """
        <div class="trace-table">
            <h3>Execution Trace Steps</h3>
            <table class="table table-striped table-sm">
                <thead>
                    <tr>
                        <th>Step</th>
                        <th>Time</th>
                        <th>CPU Lock</th>
                        <th>Active Tasks</th>
                        <th>Task States</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for step in steps[:50]:  # Limit to first 50 steps
            active = ', '.join(step['active_tasks']) or 'None'
            states = ', '.join(f"{k}:{v}" for k, v in step['task_states'].items())
            
            html += f"""
                    <tr>
                        <td>{step['step_number']}</td>
                        <td>{step['time']}</td>
                        <td>{step['cpu_lock']}</td>
                        <td>{active}</td>
                        <td><small>{states}</small></td>
                    </tr>
            """
        
        if len(steps) > 50:
            html += f"<tr><td colspan='5' class='text-center'><em>... {len(steps) - 50} more steps ...</em></td></tr>"
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def generate_summary_html(self, trace_result: Dict) -> str:
        """Generate summary of counterexample"""
        
        if not trace_result['has_counterexample']:
            return "<div class='alert alert-success'>✅ No counterexample - Property is satisfied</div>"
        
        property_violated = trace_result.get('property_violated', 'Unknown property')
        total_time = trace_result.get('total_time', 0)
        num_steps = len(trace_result.get('trace_steps', []))
        
        html = f"""
        <div class="alert alert-danger">
            <h4>❌ Counterexample Found</h4>
            <p><strong>Property Violated:</strong> {property_violated}</p>
            <p><strong>Trace Length:</strong> {num_steps} steps</p>
            <p><strong>Total Time:</strong> {total_time} time units</p>
        </div>
        """
        
        return html
