"""Testing utilities for running pipeline subsets and creating test parsers.

This module provides helper functions for testing individual pipeline stages
and creating argument parsers for testing purposes.
"""
import argparse
from pathlib import Path
from typing import Dict, Set, List, Optional

from .pipeline import PipelineData
from .contexts import AnalysisContext, TransformContext
from .models import ArgumentAnnotation
from .registry import pipeline_registry


def create_test_pipeline_data(
    script_text: str = "",
    undefined_vars: Optional[List[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    positional_indices: Optional[Set[int]] = None,
    varargs: bool = False,
    annotations: Optional[Dict[str, ArgumentAnnotation]] = None
) -> PipelineData:
    """Create pipeline data for testing purposes.
    
    Args:
        script_text: The script content
        undefined_vars: List of undefined variables
        env_vars: Environment variables with defaults
        positional_indices: Set of positional parameter indices
        varargs: Whether script uses varargs
        annotations: Variable annotations
        
    Returns:
        PipelineData configured for testing
    """
    data = PipelineData()
    data.update(
        script_text=script_text,
        undefined_vars={var: None for var in (undefined_vars or [])},
        env_vars=env_vars or {},
        positional_indices=positional_indices or set(),
        varargs=varargs,
        annotations=annotations or {}
    )
    return data


def run_analysis_stage(script_text: str) -> PipelineData:
    """Run only the analysis stage for testing.
    
    Args:
        script_text: Script content to analyze
        
    Returns:
        PipelineData with analysis results
    """
    data = PipelineData()
    data.update(
        command="run",
        script_path=Path("test.sh"),
        echo_mode=False,
        rest_args=[],
        script_text=script_text
    )
    
    # Create analysis context and run analyzers
    stage_fields = AnalysisContext.model_fields.keys()
    filtered_data = {k: v for k, v in data.data.items() if k in stage_fields}
    stage_context = AnalysisContext(**filtered_data)
    
    # Run analysis stage
    pipeline_registry.execute_stage('analyze', stage_context)
    
    # Update pipeline data with results
    data.data.update(stage_context.model_dump())
    
    return data


def run_transform_stage(data: PipelineData) -> argparse.ArgumentParser:
    """Run only the transform stage for testing.
    
    Args:
        data: Pipeline data with analysis results
        
    Returns:
        Built ArgumentParser
    """
    # Create transform context and run transformers
    stage_fields = TransformContext.model_fields.keys()
    filtered_data = {k: v for k, v in data.data.items() if k in stage_fields}
    stage_context = TransformContext(**filtered_data)
    
    # Run transform stage
    pipeline_registry.execute_stage('transform', stage_context)
    
    # Update pipeline data with results
    data.data.update(stage_context.model_dump())
    
    return data.get('argument_parser')


def build_test_parser(
    undefined_vars: List[str],
    env_vars: Dict[str, str],
    positional_indices: Set[int],
    varargs: bool,
    annotations: Dict[str, ArgumentAnnotation]
) -> argparse.ArgumentParser:
    """Build an argument parser for testing (compatibility function).
    
    This function provides compatibility with the old build_dynamic_arg_parser
    interface for testing purposes.
    
    Args:
        undefined_vars: List of undefined variables
        env_vars: Environment variables with defaults  
        positional_indices: Set of positional parameter indices
        varargs: Whether script uses varargs
        annotations: Variable annotations
        
    Returns:
        Built ArgumentParser
    """
    # Create test pipeline data
    data = create_test_pipeline_data(
        undefined_vars=undefined_vars,
        env_vars=env_vars,
        positional_indices=positional_indices,
        varargs=varargs,
        annotations=annotations
    )
    
    # Run transform stage to build parser
    return run_transform_stage(data)


def run_pipeline_stages(script_text: str, rest_args: List[str]) -> PipelineData:
    """Run analysis and transform stages for testing.
    
    Args:
        script_text: Script content to analyze
        rest_args: Command line arguments to parse
        
    Returns:
        PipelineData with analysis and transform results
    """
    # Run analysis
    data = run_analysis_stage(script_text)
    data.set('rest_args', rest_args)
    
    # Run transform
    run_transform_stage(data)
    
    return data