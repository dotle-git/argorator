"""Parse Google-style annotations from shell script comments."""
import re
from typing import Dict


def parse_arg_annotations(script_text: str) -> Dict[str, Dict[str, str]]:
	"""Parse comment-based annotations for argument metadata using Google docstring style.
	
	Supports the Google docstring-style format:
	- # VAR_NAME (type): Description. Default: default_value
	- # VAR_NAME: Description (type defaults to str)
	- # VAR_NAME (type) [alias: -x]: Description
	
	For choice types:
	- # VAR_NAME (choice[opt1, opt2, opt3]): Description
	
	Args:
		script_text: The full script content
		
	Returns:
		Dict mapping variable names to metadata dicts with 'type', 'help', 'default', 'alias', and optionally 'choices'
	"""
	annotations = {}
	
	# Pattern for Google-style docstring annotations
	# Matches: # VAR_NAME (type) [alias: -x]: description. Default: value
	# or: # VAR_NAME (choice[opt1, opt2]): description
	# or: # VAR_NAME: description
	pattern = re.compile(
		r'^\s*#\s*'
		r'([A-Za-z_][A-Za-z0-9_]*)'  # Variable name (any case)
		r'(?:\s*\('  # Optional type section
		r'(bool|int|float|str|string|choice)'  # Type
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
		var_name = match.group(1)
		var_type = match.group(2) or 'str'
		choices = match.group(3)
		alias = match.group(4)
		description = match.group(5).strip()
		default = match.group(6)
		
		# Normalize type
		if var_type.lower() in ('string', 'str'):
			var_type = 'str'
		
		metadata = {
			'type': var_type.lower(),
			'help': description
		}
		
		if var_type.lower() == 'choice' and choices:
			metadata['choices'] = [c.strip() for c in choices.split(',')]
			
		if default:
			metadata['default'] = default.strip()
			
		if alias:
			metadata['alias'] = alias.strip()
			
		annotations[var_name] = metadata
	
	return annotations