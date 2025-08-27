"""Parse Google-style annotations from shell script comments."""
from typing import Dict, Optional

from .models import ArgumentAnnotation
from .parsers import script_parser


def parse_arg_annotations(script_text: str) -> Dict[str, ArgumentAnnotation]:
	"""Parse comment-based annotations for argument metadata using Google docstring style.
	
	Supports the Google docstring-style format:
	- # VAR_NAME (type): Description. Default: default_value
	- # var_name (type): Description (parameter names are normalized to uppercase)
	- # VAR_NAME: Description (type defaults to str)
	- # VAR_NAME (type) [alias: -x]: Description
	
	For choice types:
	- # VAR_NAME (choice[opt1, opt2, opt3]): Description
	
	Args:
		script_text: The full script content
		
	Returns:
		Dict mapping variable names to ArgumentAnnotation models
	"""
	return script_parser.parse_arg_annotations(script_text)


def parse_script_description(script_text: str) -> Optional[str]:
	"""Parse script description from comments using # Description: format.
	
	Looks for comments in the format:
	- # Description: My script description
	- #Description: My script description (no space after #)
	
	Args:
		script_text: The full script content
		
	Returns:
		Script description string if found, None otherwise
	"""
	return script_parser.parse_script_description(script_text)