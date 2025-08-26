"""Parse Google-style annotations from shell script comments."""
import re
from typing import Dict

from .models import ArgumentAnnotation


def parse_group_declarations(script_text: str) -> Dict[str, ArgumentAnnotation]:
	"""Parse natural language group declarations.
	
	Supports:
	- # group VAR1, VAR2, VAR3 as GroupName
	- # group VAR1, VAR2  (auto-named as Group1, Group2, etc.)
	- # one of VAR1, VAR2 as GroupName  
	- # one of VAR1, VAR2  (auto-named as ExclusiveGroup1, etc.)
	
	Returns:
		Dict mapping variable names to ArgumentAnnotation with group info
	"""
	group_annotations = {}
	group_counter = 1
	exclusive_counter = 1
	
	# Pattern for regular groups: # group VAR1, VAR2, VAR3 as GroupName
	group_pattern = re.compile(
		r'^\s*#\s*group\s+'
		r'([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)'  # Variable list
		r'(?:\s+as\s+(.+?))?'  # Optional "as GroupName"
		r'\s*$',
		re.MULTILINE | re.IGNORECASE
	)
	
	# Pattern for exclusive groups: # one of VAR1, VAR2 as GroupName
	exclusive_pattern = re.compile(
		r'^\s*#\s*one\s+of\s+'
		r'([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)'  # Variable list
		r'(?:\s+as\s+(.+?))?'  # Optional "as GroupName"
		r'\s*$',
		re.MULTILINE | re.IGNORECASE
	)
	
	# Parse regular groups
	for match in group_pattern.finditer(script_text):
		var_list_str = match.group(1)
		group_name = match.group(2)
		
		if not group_name:
			group_name = f"Group{group_counter}"
			group_counter += 1
		else:
			group_name = group_name.strip()
		
		# Parse variable list
		variables = [var.strip() for var in var_list_str.split(',')]
		
		# Create annotations for each variable
		for var in variables:
			if var:  # Skip empty strings
				if var in group_annotations:
					raise ValueError(f"Variable '{var}' is already in a group. Variables cannot be in multiple groups.")
				group_annotations[var] = ArgumentAnnotation(group=group_name)
	
	# Parse exclusive groups  
	for match in exclusive_pattern.finditer(script_text):
		var_list_str = match.group(1)
		group_name = match.group(2)
		
		if not group_name:
			group_name = f"ExclusiveGroup{exclusive_counter}"
			exclusive_counter += 1
		else:
			group_name = group_name.strip()
		
		# Parse variable list
		variables = [var.strip() for var in var_list_str.split(',')]
		
		# Create annotations for each variable
		for var in variables:
			if var:  # Skip empty strings
				if var in group_annotations:
					raise ValueError(f"Variable '{var}' is already in a group. Variables cannot be in multiple groups.")
				group_annotations[var] = ArgumentAnnotation(exclusive_group=group_name)
	
	return group_annotations


def parse_arg_annotations(script_text: str) -> Dict[str, ArgumentAnnotation]:
	"""Parse comment-based annotations for argument metadata using Google docstring style.
	
	Supports the Google docstring-style format:
	- # VAR_NAME (type): Description. Default: default_value
	- # VAR_NAME: Description (type defaults to str)
	- # VAR_NAME (type) [alias: -x]: Description
	
	Natural language group syntax:
	- # group VAR1, VAR2, VAR3 as GroupName
	- # one of VAR1, VAR2 as GroupName
	
	For choice types:
	- # VAR_NAME (choice[opt1, opt2, opt3]): Description
	
	Args:
		script_text: The full script content
		
	Returns:
		Dict mapping variable names to ArgumentAnnotation models
	"""
	annotations = {}
	
	# First, parse natural language group declarations
	group_annotations = parse_group_declarations(script_text)
	
	# Pattern for Google-style docstring annotations with support for groups
	# More flexible pattern that can handle annotations in any order
	pattern = re.compile(
		r'^\s*#\s*'
		r'([A-Za-z_][A-Za-z0-9_]*)'  # Variable name (any case)
		r'(?:\s*\('  # Optional type section
		r'(bool|int|float|str|string|choice)'  # Type
		r'(?:\[([^\]]+)\])?'  # Optional choices for choice type
		r'\))?'
		r'((?:\s*\[[^\]]+\])*)'  # Capture all bracket annotations
		r'\s*:\s*'  # Colon separator
		r'([^.]+?)' # Description (up to period or end)
		r'(?:\.\s*[Dd]efault:\s*(.+?))?'  # Optional default value
		r'\s*$',  # End of line
		re.MULTILINE | re.IGNORECASE
	)
	
	for match in pattern.finditer(script_text):
		var_name = match.group(1)
		var_type = match.group(2) or 'str'
		choices_str = match.group(3)
		annotations_str = match.group(4)
		description = match.group(5).strip()
		default = match.group(6)
		
		# Parse bracket annotations (only alias now)
		alias = None
		
		if annotations_str:
			# Find all [key: value] patterns
			bracket_pattern = re.compile(r'\[\s*([^:]+):\s*([^\]]+)\]')
			for bracket_match in bracket_pattern.finditer(annotations_str):
				key = bracket_match.group(1).strip().lower()
				value = bracket_match.group(2).strip()
				
				if key == 'alias':
					alias = value
		
		# Normalize type
		if var_type.lower() in ('string', 'str'):
			var_type = 'str'
		else:
			var_type = var_type.lower()
		
		# Start with group info from natural language declarations (if any)
		if var_name in group_annotations:
			base_annotation = group_annotations[var_name]
			annotation_data = {
				'type': var_type,
				'help': description,
				'group': base_annotation.group,
				'exclusive_group': base_annotation.exclusive_group,
			}
		else:
			annotation_data = {
				'type': var_type,
				'help': description
			}
		
		if var_type == 'choice' and choices_str:
			annotation_data['choices'] = [c.strip() for c in choices_str.split(',')]
			
		if default:
			annotation_data['default'] = default.strip()
			
		if alias:
			annotation_data['alias'] = alias.strip()
		
		# Create ArgumentAnnotation model
		annotations[var_name] = ArgumentAnnotation(**annotation_data)
	
	# Add any variables that were only mentioned in group declarations
	for var_name, group_annotation in group_annotations.items():
		if var_name not in annotations:
			# Variable mentioned in group but no individual annotation found
			annotations[var_name] = group_annotation
	
	return annotations