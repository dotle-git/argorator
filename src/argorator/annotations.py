"""Parse Google-style annotations from shell script comments."""
import re
import parsy
from typing import Dict, Optional

from .models import ArgumentAnnotation
from .argument_types import get_all_supported_types, validate_type_name


class CommentParser:
    """Parser for shell script comments using parsy."""
    
    def __init__(self):
        self._setup_grammar()
    
    def _setup_grammar(self):
        """Setup parsy grammar for comment parsing."""
        # Basic tokens
        self.whitespace = parsy.regex(r'\s*')
        self.optional_whitespace = parsy.regex(r'\s*')
        self.required_whitespace = parsy.regex(r'\s+')
        
        # Comment start patterns
        self.hash = parsy.string('#')
        
        # Description parsing
        # Matches: # Description: text content
        # or: #Description: text content (no space after #)
        description_keyword = parsy.regex(r'[Dd]escription', re.IGNORECASE)
        colon = parsy.string(':')
        description_text = parsy.regex(r'.+')  # Rest of the line
        
        self.description_pattern = parsy.seq(
            parsy.string('#'),
            self.optional_whitespace,
            description_keyword,
            self.optional_whitespace,
            colon,
            self.optional_whitespace,
            description_text
        ).combine(lambda _, __, ___, ____, _____, ______, desc: desc.strip())
    
    def parse_description(self, script_text: str) -> Optional[str]:
        """Parse script description from comments."""
        lines = script_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line.startswith('#'):
                continue
                
            try:
                # Try to parse this line as a description
                result = self.description_pattern.parse(line)
                return result
            except parsy.ParseError:
                continue
        
        return None


# Global parser instance
_comment_parser = CommentParser()


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
	
	# Build dynamic type pattern from supported types
	supported_types = get_all_supported_types()
	type_pattern = '|'.join(re.escape(t) for t in supported_types)
	
	# Pattern for Google-style docstring annotations
	# Matches: # VAR_NAME (type) [alias: -x]: description. Default: value
	# or: # VAR_NAME (choice[opt1, opt2]): description
	# or: # VAR_NAME: description
	pattern = re.compile(
		r'^\s*#\s*'
		r'([A-Za-z_][A-Za-z0-9_]*)'  # Variable name (any case)
		r'(?:\s*\('  # Optional type section
		rf'({type_pattern})'  # Dynamic type pattern from registry
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
		
		# Validate and normalize type using the type registry
		try:
			var_type = validate_type_name(var_type)
		except ValueError as e:
			# Skip invalid type annotations with a warning
			print(f"Warning: Skipping annotation for {var_name}: {e}")
			continue
		
		# Build annotation data
		annotation_data = {
			'type': var_type,
			'help': description
		}
		
		# Handle choices for choice-type annotations
		if choices_str:
			annotation_data['choices'] = [c.strip() for c in choices_str.split(',')]
			# If choices are provided but type isn't a choice type, set it to choice
			from .argument_types import get_type_handler
			handler = get_type_handler(var_type)
			if 'choice' not in handler.get_type_names():
				annotation_data['type'] = 'choice'
			
		if default:
			annotation_data['default'] = default.strip()
			
		if alias:
			annotation_data['alias'] = alias.strip()
		
		# Create ArgumentAnnotation model (this will validate using the new type system)
		try:
			annotations[var_name] = ArgumentAnnotation(**annotation_data)
		except ValueError as e:
			print(f"Warning: Skipping annotation for {var_name}: {e}")
			continue
	
	return annotations


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
	return _comment_parser.parse_description(script_text)