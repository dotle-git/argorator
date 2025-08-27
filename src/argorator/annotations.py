"""Parse Google-style annotations from shell script comments."""
import re
from typing import Dict

from .models import ArgumentAnnotation, get_argument_type_handler, TYPE_NAME_TO_HANDLER


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
	annotations = {}
	
	# Build dynamic type pattern from registered types
	all_type_names = '|'.join(sorted(TYPE_NAME_TO_HANDLER.keys(), key=len, reverse=True))
	
	# Pattern for Google-style docstring annotations
	# Matches: # VAR_NAME (type) [alias: -x]: description. Default: value
	# or: # VAR_NAME (choice[opt1, opt2]): description
	# or: # VAR_NAME: description
	pattern = re.compile(
		r'^\s*#\s*'
		r'([A-Za-z_][A-Za-z0-9_]*)'  # Variable name (any case)
		r'(?:\s*\('  # Optional type section
		rf'({all_type_names})'  # Type (dynamic from registry)
		r'(?:\[([^\]]+)\])?'  # Optional choices for choice type
		r'\))?'
		r'(?:\s*\[alias:\s*([^\]]+)\])?'  # Optional alias
		r'\s*:\s*'  # Colon separator
		r'([^.]+?)' # Description (up to period or end)
		r'(?:\.\s*[Dd]efault:\s*(.+?))?'  # Optional default value
		r'\s*$',  # End of line
		re.MULTILINE | re.IGNORECASE
	)
	
	for match in pattern.finditer(script_text):
		var_name = match.group(1).upper()  # Normalize to uppercase for shell variables
		var_type = match.group(2) or 'str'
		choices_str = match.group(3)
		alias = match.group(4)
		description = match.group(5).strip()
		default = match.group(6)
		
		# Get the type handler and normalize to canonical type_id
		type_handler = get_argument_type_handler(var_type)
		canonical_type = type_handler.type_id
		
		# Build annotation data
		annotation_data = {
			'type': canonical_type,
			'help': description
		}
		
		# Handle choices for choice types
		if canonical_type == 'choice' and choices_str:
			annotation_data['choices'] = [c.strip() for c in choices_str.split(',')]
		
		# Validate annotation data using the type handler
		try:
			type_handler.validate_annotation_data(annotation_data)
		except ValueError as e:
			# Skip invalid annotations, or raise depending on desired behavior
			print(f"Warning: Invalid annotation for {var_name}: {e}")
			continue
			
		if default:
			annotation_data['default'] = default.strip()
			
		if alias:
			annotation_data['alias'] = alias.strip()
		
		# Create ArgumentAnnotation model
		annotations[var_name] = ArgumentAnnotation(**annotation_data)
	
	return annotations