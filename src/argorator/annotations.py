"""Parse Google-style annotations from shell script comments."""
import re
from typing import Dict, Optional

# The parsy dependency is optional at runtime to simplify installation in constrained
# environments such as CI sandboxes. We provide a minimal fallback implementation for
# the functionality we use (regex parsing with a `.parse` method).

try:
	import parsy  # type: ignore
	expr_regex = parsy.regex  # noqa: N817
	expr_seq = parsy.seq

	def _combine(*args, **kwargs):  # noqa: D401
		return parsy.seq(*args, **kwargs).combine  # type: ignore[attr-defined]

except ModuleNotFoundError:  # pragma: no cover – fallback when parsy is absent
	class _SimpleRegexParser:  # noqa: D401
		"""Very small subset of the `parsy` API we rely on for description parsing."""

		def __init__(self, pattern: str):
			self._re = re.compile(pattern, re.IGNORECASE)

		def parse(self, text: str):
			m = self._re.match(text)
			if not m:
				raise ValueError("parse error")
			return m.group(1)

	def expr_regex(pattern: str, flags: int = 0):  # noqa: N802
		return _SimpleRegexParser(pattern)

	def expr_seq(*parsers):  # noqa: D401,N802
		# Very naive concatenation: only supports regex tokens returning group 1.
		patterns = []
		for p in parsers:
			if isinstance(p, _SimpleRegexParser):
				patterns.append(p._re.pattern)
			else:
				patterns.append(re.escape(str(p)))
		joined = ''.join(patterns)
		return _SimpleRegexParser(joined)

	parsy = None  # type: ignore

from .models import ArgumentAnnotation


# ---------------------------------------------------------------------------
# Comment parsing (script description)
# ---------------------------------------------------------------------------


class CommentParser:
    """Parser for shell script comments using parsy."""
    
    def __init__(self):
        self._setup_grammar()
    
    def _setup_grammar(self):
        """Setup parsy grammar for comment parsing."""
        # Basic tokens
        # Use fallback regex helpers defined above
        self.whitespace = expr_regex(r'\s*')
        self.optional_whitespace = expr_regex(r'\s*')
        self.required_whitespace = expr_regex(r'\s+')
        
        # Comment start patterns
        self.hash = expr_regex(r'#')
        
        # Description parsing
        # Matches: # Description: text content
        # or: #Description: text content (no space after #)
        description_keyword = expr_regex(r'[Dd]escription')
        colon = expr_regex(r':')
        description_text = expr_regex(r'.+')  # Rest of the line
        
        description_seq = expr_seq(
            expr_regex(r'#'),
            self.optional_whitespace,
            description_keyword,
            self.optional_whitespace,
            colon,
            self.optional_whitespace,
            description_text,
        )
        self.description_pattern = description_seq
    
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
	
	# Use verbose regex for readability and to avoid double escaping
	pattern = re.compile(
	    r'''
	        ^\s*#\s*                               # Comment start with optional spaces
	        ([A-Za-z_][A-Za-z0-9_]*)                # Variable name (capture 1)
	        (?:\s*\(                              # Optional opening parenthesis for type
	            (bool|int|float|str|string|choice|file)  # Type keyword (capture 2)
	            (?:\[(.*?)\])?                    # Optional choices list for choice (capture 3)
	        \))?                                   # Closing parenthesis for type (whole group optional)
	        (?:\s*\[alias:\s*([^\]]+)\])?      # Optional alias in square brackets (capture 4)
	        \s*:\s*                                # Colon separator after var name/type/alias
	        ([^.]+?)                                # Description up to first period or EOL (capture 5)
	        (?:                                     # Optional default part
	            \.?\s*[Dd]efault\s*:?\s*        # "Default" keyword optionally prefixed by period & colon
	            (.+?)                               # Default value (capture 6)
	        )?                                      # Default block optional
	        \s*$                                   # End of line with optional spaces
	    ''',
	    re.IGNORECASE | re.MULTILINE | re.VERBOSE,
	)
	
	for match in pattern.finditer(script_text):
		var_name = match.group(1).upper()  # Normalize to uppercase for shell variables
		var_type = match.group(2) or 'str'
		choices_str = match.group(3)
		alias = match.group(4)
		description = match.group(5).strip()
		default = match.group(6)
		
		# Normalize type
		if var_type.lower() in ('string', 'str'):
			var_type = 'str'
		else:
			var_type = var_type.lower()
		
		# Build annotation data
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