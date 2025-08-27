"""Decorator registration system for pipeline steps."""
from functools import wraps
from typing import Callable, Dict, List, TypeVar

from .contexts import BaseContext

# Type for pipeline step functions that mutate context in-place
PipelineStep = Callable[[BaseContext], None]
T = TypeVar('T', bound=PipelineStep)


class PipelineRegistry:
    """Registry for pipeline steps using decorator pattern."""
    
    def __init__(self):
        self._steps: Dict[str, List[PipelineStep]] = {}
    
    def register(self, stage: str, order: int = 100):
        """Decorator to register a pipeline step for a specific stage.
        
        Args:
            stage: The pipeline stage name (e.g., 'analyze', 'transform', 'compile')
            order: Execution order within the stage (lower numbers run first)
        """
        def decorator(func: T) -> T:
            if stage not in self._steps:
                self._steps[stage] = []
            
            # Insert function in order
            step_info = (order, func)
            inserted = False
            for i, (existing_order, _) in enumerate(self._steps[stage]):
                if order < existing_order:
                    self._steps[stage].insert(i, step_info)
                    inserted = True
                    break
            if not inserted:
                self._steps[stage].append(step_info)
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def execute_stage(self, stage: str, context: BaseContext) -> None:
        """Execute all registered steps for a given stage.
        
        Args:
            stage: The pipeline stage name
            context: The stage-specific context object (mutated in-place)
        """
        if stage not in self._steps:
            return
        
        for order, step_func in self._steps[stage]:
            step_func(context)
    
    def get_stages(self) -> List[str]:
        """Get all registered stage names."""
        return list(self._steps.keys())
    
    def get_steps_for_stage(self, stage: str) -> List[str]:
        """Get all step function names for a stage."""
        if stage not in self._steps:
            return []
        return [func.__name__ for order, func in self._steps[stage]]


# Global registry instance
pipeline_registry = PipelineRegistry()

# Convenience decorators for common stages
def analyzer(order: int = 100):
    """Register an analyzer step."""
    return pipeline_registry.register('analyze', order)

def transformer(order: int = 100):
    """Register a transformer step."""
    return pipeline_registry.register('transform', order)

def validator(order: int = 100):
    """Register a validator step."""
    return pipeline_registry.register('validate', order)

def compiler(order: int = 100):
    """Register a compiler step."""
    return pipeline_registry.register('compile', order)

def executor(order: int = 100):
    """Register an executor step."""
    return pipeline_registry.register('execute', order)