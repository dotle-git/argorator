"""Focused parsy parser for macro functionality only."""
import parsy
import re
from typing import List, Optional, Tuple
from .models import FunctionBlock, MacroComment, IterationMacro, MacroTarget

class MacroParser:
    """Parser focused specifically on macro processing needs."""
    
    def __init__(self):
        self._setup_grammar()
    
    def _setup_grammar(self):
        """Setup parsy grammar for function detection."""
        # Basic tokens
        whitespace = parsy.regex(r'\s*')
        identifier = parsy.regex(r'[a-zA-Z_][a-zA-Z0-9_]*')
        
        # Function definition patterns
        # Pattern 1: function_name() {
        self.function_pattern1 = parsy.seq(
            whitespace,
            identifier,
            whitespace,
            parsy.string('()'),
            whitespace,
            parsy.string('{')
        ).combine(lambda _, name, __, ___, ____, _____: name)
        
        # Pattern 2: function function_name() {
        self.function_pattern2 = parsy.seq(
            whitespace,
            parsy.string('function'),
            parsy.regex(r'\s+'),
            identifier,
            whitespace,
            parsy.string('()').optional(),
            whitespace,
            parsy.string('{')
        ).combine(lambda _, __, ___, name, ____, _____, ______, _______: name)
        
        # Pattern 3: function function_name {
        self.function_pattern3 = parsy.seq(
            whitespace,
            parsy.string('function'),
            parsy.regex(r'\s+'),
            identifier,
            whitespace,
            parsy.string('{')
        ).combine(lambda _, __, ___, name, ____, _____: name)
    
    def find_functions(self, script_text: str) -> List[FunctionBlock]:
        """Find all function definitions in the script."""
        lines = script_text.split('\n')
        functions = []
        
        for i, line in enumerate(lines):
            func_name = self._try_parse_function_start(line)
            if func_name:
                end_line = self._find_function_end(lines, i)
                if end_line is not None:
                    full_def = '\n'.join(lines[i:end_line + 1])
                    functions.append(FunctionBlock(
                        name=func_name,
                        start_line=i,
                        end_line=end_line,
                        full_definition=full_def
                    ))
        
        return functions
    
    def _try_parse_function_start(self, line: str) -> Optional[str]:
        """Try to parse a function definition start."""
        try:
            return self.function_pattern1.parse(line)
        except:
            pass
        
        try:
            return self.function_pattern2.parse(line)
        except:
            pass
        
        try:
            return self.function_pattern3.parse(line)
        except:
            pass
        
        return None
    
    def _find_function_end(self, lines: List[str], start_line: int) -> Optional[int]:
        """Find the end of a function by matching braces."""
        brace_count = 0
        
        # Count opening braces on the start line
        brace_count += lines[start_line].count('{')
        brace_count -= lines[start_line].count('}')
        
        if brace_count == 0:
            return start_line  # Single line function (rare but possible)
        
        # Search subsequent lines
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            
            # Skip lines that are comments or strings (simple heuristic)
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            
            # Count braces, being careful about strings
            brace_count += self._count_braces_excluding_strings(line)
            
            if brace_count == 0:
                return i
        
        return None  # Unclosed function
    
    def _count_braces_excluding_strings(self, line: str) -> int:
        """Count braces while trying to avoid those in strings."""
        # Simple heuristic: remove quoted strings first
        # This is not perfect but good enough for most cases
        
        # Remove single-quoted strings
        line = re.sub(r"'[^']*'", '', line)
        # Remove double-quoted strings (simple version)
        line = re.sub(r'"[^"]*"', '', line)
        
        return line.count('{') - line.count('}')
    
    def find_macro_comments(self, script_text: str) -> List[MacroComment]:
        """Find all macro annotation comments."""
        lines = script_text.split('\n')
        macros = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith('#'):
                continue
            
            content = stripped[1:].strip()
            macro_type = self._detect_macro_type(content)
            
            if macro_type:
                macros.append(MacroComment(
                    line_number=i,
                    content=content,
                    macro_type=macro_type,
                    raw_line=line
                ))
        
        return macros
    
    def _detect_macro_type(self, content: str) -> Optional[str]:
        """Detect if a comment is a macro and what type."""
        # Iteration macro: for VAR in SOURCE (stricter pattern)
        if re.match(r'for\s+\w+\s+in\s+\S+', content, re.IGNORECASE):
            return 'iteration'
        
        # Future macro types can be added here
        # if re.match(r'parallel', content, re.IGNORECASE):
        #     return 'parallel'
        # if re.match(r'timeout\s+', content, re.IGNORECASE):
        #     return 'timeout'
        
        return None
    
    def find_target_for_macro(self, script_text: str, macro_line: int) -> Optional[MacroTarget]:
        """Find what a macro applies to (function or line after it)."""
        lines = script_text.split('\n')
        
        # Skip over consecutive macro comments to find the actual target
        target_line = macro_line + 1
        while target_line < len(lines):
            line = lines[target_line].strip()
            # If this line is also a macro comment, skip it
            if line.startswith('#') and self._detect_macro_type(line[1:].strip()):
                target_line += 1
                continue
            break
        
        if target_line >= len(lines):
            return None
        
        # First, check if it's a function
        func_name = self._try_parse_function_start(lines[target_line])
        if func_name:
            end_line = self._find_function_end(lines, target_line)
            if end_line is not None:
                full_def = '\n'.join(lines[target_line:end_line + 1])
                return MacroTarget(
                    target_type="function",
                    start_line=target_line,
                    end_line=end_line,
                    content=full_def,
                    metadata={"function_name": func_name}
                )
        
        # Otherwise, it's a single line target
        return MacroTarget(
            target_type="line",
            start_line=target_line,
            end_line=target_line,
            content=lines[target_line],
            metadata={}
        )
    
    def parse_iteration_macro(self, comment: MacroComment, target: MacroTarget) -> IterationMacro:
        """Parse an iteration macro comment into a structured object."""
        content = comment.content
        
        # Parse separator syntax first
        separator = None
        processed_content = content
        
        # Check for separator syntax variations
        separator_patterns = [
            # "sep X" syntax (quoted)
            (r'(.+?)\s+sep\s+([\'"])(.+?)\2(?:\s+|$)', 3),
            # "separated by X" syntax (quoted)  
            (r'(.+?)\s+separated\s+by\s+([\'"])(.+?)\2(?:\s+|$)', 3),
            # "sep X" syntax (unquoted) - match any non-whitespace character(s)
            (r'(.+?)\s+sep\s+(\S+)(?:\s+|$)', 2),
            # "separated by X" syntax (unquoted) - match any non-whitespace character(s)
            (r'(.+?)\s+separated\s+by\s+(\S+)(?:\s+|$)', 2),
        ]
        
        for pattern, sep_group in separator_patterns:
            sep_match = re.search(pattern, content, re.IGNORECASE)
            if sep_match:
                # Extract everything before the separator syntax
                before_sep = sep_match.group(1).strip()
                separator = self._process_separator(sep_match.group(sep_group))
                
                # Find everything after the separator in the original content
                sep_end = sep_match.end()
                after_sep = content[sep_end:].strip()
                
                # Combine before separator with anything after separator (like | with params)
                if after_sep:
                    processed_content = f"{before_sep} {after_sep}"
                else:
                    processed_content = before_sep
                break
        
        # Enhanced pattern to support "as Type" syntax:
        # for ITERATOR in SOURCE | with PARAM1 PARAM2
        # for ITERATOR in (SOURCE as TYPE) | with PARAM1 PARAM2
        # for ITERATOR in SOURCE as TYPE | with PARAM1 PARAM2
        
        # First, handle parenthesized format
        paren_pattern = r'for\s+(\w+)\s+in\s+\(([^)]+?)\s+as\s+(\w+)\)\s*(?:\|\s*with\s+(.+))?'
        paren_match = re.match(paren_pattern, processed_content, re.IGNORECASE)
        
        if paren_match:
            iterator_var = paren_match.group(1)
            source = paren_match.group(2).strip()
            source_type = paren_match.group(3).lower()
            additional_params = []
            if paren_match.group(4):
                additional_params = [p.strip() for p in paren_match.group(4).split()]
        else:
            # Handle non-parenthesized format
            # First try to match with "as TYPE" 
            as_pattern = r'for\s+(\w+)\s+in\s+(.+?)\s+as\s+(\w+)\s*(?:\|\s*with\s+(.+))?'
            as_match = re.match(as_pattern, processed_content, re.IGNORECASE)
            
            if as_match:
                iterator_var = as_match.group(1)
                source = as_match.group(2).strip()
                source_type = as_match.group(3).lower()
                additional_params = []
                if as_match.group(4):
                    additional_params = [p.strip() for p in as_match.group(4).split()]
            else:
                # No "as TYPE", just normal format
                pattern = r'for\s+(\w+)\s+in\s+(.+?)(?:\|\s*with\s+(.+?))?$'
                match = re.match(pattern, processed_content, re.IGNORECASE)
                
                if not match:
                    raise ValueError(f"Invalid iteration macro syntax: {content}")
                
                iterator_var = match.group(1)
                source = match.group(2).strip()
                source_type = None
                additional_params = []
                
                if match.group(3):
                    additional_params = [p.strip() for p in match.group(3).split()]
        
        # Determine iteration type (enhanced with separator detection)
        iteration_type = self._detect_iteration_type(source, source_type, separator)
        
        # Validate the iterator variable name
        if not self._is_valid_bash_variable_name(iterator_var):
            raise ValueError(f"Invalid variable name '{iterator_var}'. Bash variables must start with a letter or underscore, followed by letters, numbers, or underscores.")
        
        return IterationMacro(
            comment=comment,
            target=target,
            iterator_var=iterator_var,
            source=source,
            source_type=source_type,
            iteration_type=iteration_type,
            separator=separator,
            additional_params=additional_params
        )
    
    def _detect_iteration_type(self, source: str, source_type: Optional[str] = None, separator: Optional[str] = None) -> str:
        """Detect the type of iteration based on source, type, and separator."""
        # If separator is provided, it's delimited iteration
        if separator is not None:
            return 'delimited'
        
        # If explicit type is provided, use it
        if source_type:
            if source_type == 'file':
                return 'file_lines'
            elif source_type == 'array':
                return 'array'
            elif source_type == 'pattern':
                return 'pattern'
            elif source_type == 'range':
                return 'range'
            elif source_type == 'directory':
                return 'directory'
        
        # Fall back to heuristic detection (legacy behavior)
        if '*' in source or '?' in source or '[' in source:
            return 'pattern'
        elif source.startswith('{') and '..' in source and source.endswith('}'):
            return 'range'
        elif source.endswith('/') or source.endswith('*/'):
            return 'directory'
        else:
            # Default to array iteration for variables
            return 'array'
    
    def _process_separator(self, separator_str: str) -> str:
        """Process separator string, handling escape sequences."""
        if not separator_str:
            raise ValueError("Empty separator")
        
        # Handle Python-style escape sequences
        result = separator_str
        
        # Common escape sequences
        escape_map = {
            '\\n': '\n',
            '\\t': '\t',
            '\\r': '\r',
            '\\\\': '\\',
            '\\"': '"',
            "\\'": "'",
        }
        
        for escaped, actual in escape_map.items():
            result = result.replace(escaped, actual)
        
        return result
    
    def _is_valid_bash_variable_name(self, name: str) -> bool:
        """Check if a string is a valid bash variable name."""
        if not name:
            return False
        
        # Must start with letter or underscore
        if not (name[0].isalpha() or name[0] == '_'):
            return False
        
        # Rest must be letters, numbers, or underscores
        for char in name[1:]:
            if not (char.isalnum() or char == '_'):
                return False
        
        return True

# Global parser instance
macro_parser = MacroParser()