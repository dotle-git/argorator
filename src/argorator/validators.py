"""Argument validation and transformation steps.

This module contains validator functions that validate and transform parsed
arguments after argparse processing but before compilation. This allows for:
- Additional validation beyond what argparse provides
- Type transformations (e.g., string paths to pathlib.Path objects)
- Cross-argument validation
- Value normalization

Currently empty - validation steps will be added in future releases.
"""
from .contexts import ValidateContext
from .registry import validator

# Example validator (commented out):
# @validator(order=10)
# def example_validator(context: ValidateContext) -> None:
#     """Example validation step."""
#     if not context.parsed_args:
#         return
#     
#     # Add validation logic here
#     pass

# Validation steps will be implemented in future releases
# The infrastructure is in place for easy extension