"""
Advanced UPPAAL Property Templates
Provides complex temporal logic properties for real-time scheduling verification
"""

class UppaalPropertyTemplates:
    """Collection of advanced UPPAAL CTL/TCTL property templates"""
    
    @staticmethod
    def get_basic_properties(task_name):
        """Basic safety and reachability properties"""
        return [
            {
                'formula': 'A[] not deadlock',
                'comment': 'Safety: System never deadlocks',
                'category': 'safety'
            },
            {
                'formula': f'E<> {task_name}.Done',
                'comment': f'Reachability: {task_name} can complete execution',
                'category': 'reachability'
            }
        ]
    
    @staticmethod
    def get_timing_properties(task_name):
        """Timing and bounded execution properties"""
        return [
            {
                'formula': f'A[] ({task_name}.Executing imply x <= PERIOD)',
                'comment': 'Timing: Execution completes within period',
                'category': 'timing'
            },
            {
                'formula': f'A[] ({task_name}.Completing imply x >= MIN_EXECUTION)',
                'comment': 'Timing: Minimum execution time requirement',
                'category': 'timing'
            },
            {
                'formula': f'A[] ({task_name}.Executing imply (x >= 0 and x <= PERIOD))',
                'comment': 'Bounded execution: Time bounds are respected',
                'category': 'timing'
            },
            {
                'formula': f'E<> ({task_name}.Executing and x >= MIN_EXECUTION and x <= MAX_EXECUTION)',
                'comment': 'Reachability: Can execute within expected time range',
                'category': 'timing'
            }
        ]
    
    @staticmethod
    def get_liveness_properties(task_name):
        """Liveness and progress properties"""
        return [
            {
                'formula': f'{task_name}.Executing --> {task_name}.Completing',
                'comment': 'Leads-to: Executing always leads to Completing',
                'category': 'liveness'
            },
            {
                'formula': f'{task_name}.Completing --> {task_name}.Done',
                'comment': 'Leads-to: Completing always leads to Done',
                'category': 'liveness'
            },
            {
                'formula': f'{task_name}.Scheduled --> {task_name}.Executing',
                'comment': 'Leads-to: Scheduled task eventually executes',
                'category': 'liveness'
            },
            {
                'formula': f'E<> ({task_name}.Done and x >= MIN_EXECUTION)',
                'comment': 'Reachability: Task completes after minimum execution',
                'category': 'liveness'
            }
        ]
    
    @staticmethod
    def get_safety_properties(task_name):
        """Safety and mutual exclusion properties"""
        return [
            {
                'formula': f'A[] not ({task_name}.Executing and {task_name}.Done)',
                'comment': 'Mutual exclusion: Never executing and done simultaneously',
                'category': 'safety'
            },
            {
                'formula': f'A[] not ({task_name}.Idle and {task_name}.Executing)',
                'comment': 'Mutual exclusion: Never idle and executing simultaneously',
                'category': 'safety'
            },
            {
                'formula': f'A[] not ({task_name}.Ready and {task_name}.Done)',
                'comment': 'Mutual exclusion: Never ready and done simultaneously',
                'category': 'safety'
            },
            {
                'formula': f'A[] ({task_name}.Executing imply x >= 0)',
                'comment': 'Invariant: Clock is always non-negative',
                'category': 'safety'
            }
        ]
    
    @staticmethod
    def get_state_consistency_properties(task_name):
        """State consistency and coverage properties"""
        return [
            {
                'formula': f'A[] (x <= PERIOD imply ({task_name}.Idle or {task_name}.Ready or {task_name}.Scheduled or {task_name}.Executing or {task_name}.Completing or {task_name}.Done))',
                'comment': 'Coverage: All time within period is in valid state',
                'category': 'consistency'
            },
            {
                'formula': f'A[] ({task_name}.Ready imply ({task_name}.Idle or {task_name}.Ready or {task_name}.Scheduled))',
                'comment': 'State consistency: Ready transitions are valid',
                'category': 'consistency'
            }
        ]
    
    @staticmethod
    def get_advanced_properties(task_name):
        """Advanced temporal and quantitative properties"""
        return [
            {
                'formula': f'sup: {task_name}.Executing',
                'comment': 'Supremum: Maximum time in executing state',
                'category': 'quantitative'
            },
            {
                'formula': f'E<> ({task_name}.Done and x <= MIN_EXECUTION)',
                'comment': 'Reachability: Can complete at minimum execution time',
                'category': 'quantitative'
            },
            {
                'formula': f'A[] ({task_name}.Scheduled imply {task_name}.Executing or {task_name}.Scheduled)',
                'comment': 'State transition: Scheduled leads to execution',
                'category': 'advanced'
            }
        ]
    
    @staticmethod
    def get_multi_task_properties(tasks):
        """Properties for multi-task systems"""
        task_names = [t['task_name'] for t in tasks]
        properties = []
        
        # All tasks can complete
        for task_name in task_names:
            properties.append({
                'formula': f'E<> {task_name}.Done',
                'comment': f'{task_name} can complete',
                'category': 'reachability'
            })
        
        # Priority-based mutual exclusion
        if len(tasks) >= 2:
            task1, task2 = task_names[0], task_names[1]
            properties.extend([
                {
                    'formula': f'A[] not ({task1}.Executing and {task2}.Executing)',
                    'comment': f'Mutual exclusion: {task1} and {task2} never execute simultaneously',
                    'category': 'safety'
                },
                {
                    'formula': f'A<> ({task1}.Done and {task2}.Done)',
                    'comment': f'Liveness: Both {task1} and {task2} eventually complete',
                    'category': 'liveness'
                }
            ])
        
        # All tasks complete eventually
        all_done = ' and '.join([f'{t}.Done' for t in task_names])
        properties.append({
            'formula': f'E<> ({all_done})',
            'comment': 'System property: All tasks can reach completion state',
            'category': 'system'
        })
        
        return properties
    
    @staticmethod
    def get_priority_scheduling_properties(tasks):
        """Priority-based scheduling specific properties"""
        properties = []
        
        # Sort tasks by priority (higher priority = lower number)
        sorted_tasks = sorted(tasks, key=lambda t: t.get('priority', 999))
        
        if len(sorted_tasks) >= 2:
            high_priority = sorted_tasks[0]['task_name']
            low_priority = sorted_tasks[-1]['task_name']
            
            properties.extend([
                {
                    'formula': f'A[] ({low_priority}.Executing and {high_priority}.Ready imply {high_priority}.Executing)',
                    'comment': f'Priority: {high_priority} preempts {low_priority} when ready',
                    'category': 'priority'
                },
                {
                    'formula': f'{high_priority}.Ready --> {high_priority}.Executing',
                    'comment': f'Priority: High-priority {high_priority} always gets to execute',
                    'category': 'priority'
                }
            ])
        
        return properties
    
    @staticmethod
    def get_all_properties(task_name, include_advanced=True):
        """Get all properties for a single task"""
        properties = []
        properties.extend(UppaalPropertyTemplates.get_basic_properties(task_name))
        properties.extend(UppaalPropertyTemplates.get_timing_properties(task_name))
        properties.extend(UppaalPropertyTemplates.get_safety_properties(task_name))
        properties.extend(UppaalPropertyTemplates.get_state_consistency_properties(task_name))
        
        if include_advanced:
            properties.extend(UppaalPropertyTemplates.get_liveness_properties(task_name))
            properties.extend(UppaalPropertyTemplates.get_advanced_properties(task_name))
        
        return properties
    
    @staticmethod
    def properties_to_xml(properties):
        """Convert property list to UPPAAL XML queries format"""
        xml_queries = []
        for prop in properties:
            # Escape XML special characters
            formula = prop['formula'].replace('<', '&lt;').replace('>', '&gt;')
            comment = prop['comment']
            category = prop.get('category', 'general')
            
            xml_queries.append(f'''        <query>
            <formula>{formula}</formula>
            <comment>[{category.upper()}] {comment}</comment>
        </query>''')
        
        return '\n'.join(xml_queries)
    
    @staticmethod
    def properties_to_xml_from_list(properties):
        """Convert LLM-generated property list to UPPAAL XML queries format"""
        xml_queries = []
        for prop in properties:
            # Escape XML special characters
            formula = prop.get('formula', '').replace('<', '&lt;').replace('>', '&gt;')
            comment = prop.get('comment', prop.get('reason', ''))
            category = prop.get('category', 'general')
            priority = prop.get('priority', 'MEDIUM')
            
            xml_queries.append(f'''        <query>
            <formula>{formula}</formula>
            <comment>[{category.upper()}] [{priority}] {comment}</comment>
        </query>''')
        
        return '\n'.join(xml_queries)
