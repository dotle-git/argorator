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
        
        # Look at the line immediately after the macro
        target_line = macro_line + 1
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
        
        # Pattern: for ITERATOR in SOURCE | with PARAM1 PARAM2
        pattern = r'for\s+(\w+)\s+in\s+([^|]+)(?:\s*\|\s*with\s+(.+))?'
        match = re.match(pattern, content, re.IGNORECASE)
        
        if not match:
            raise ValueError(f"Invalid iteration macro syntax: {content}")
        
        iterator_var = match.group(1)
        source = match.group(2).strip()
        additional_params = []
        
        if match.group(3):
            additional_params = [p.strip() for p in match.group(3).split()]
        
        # Determine iteration type
        iteration_type = self._detect_iteration_type(source)
        
        return IterationMacro(
            comment=comment,
            target=target,
            iterator_var=iterator_var,
            source=source,
            iteration_type=iteration_type,
            additional_params=additional_params
        )
    
    def _detect_iteration_type(self, source: str) -> str:
        """Detect the type of iteration based on source."""
        if source.startswith('$') and ('FILE' in source.upper() or 'INPUT' in source.upper()):
            return 'file_lines'
        elif '*' in source or '?' in source or '[' in source:
            return 'pattern'
        elif source.startswith('{') and '..' in source and source.endswith('}'):
            return 'range'
        elif source.endswith('/') or source.endswith('*/'):
            return 'directory'
        else:
            return 'array'

# Global parser instance
macro_parser = MacroParser()