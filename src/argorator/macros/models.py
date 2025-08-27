"""Simple AST models for macro processing only."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class MacroTarget(BaseModel):
    """Represents what a macro applies to."""
    target_type: str  # 'function' or 'line'
    start_line: int
    end_line: int
    content: str
    metadata: Dict[str, Any] = {}

class FunctionBlock(BaseModel):
    """Represents a bash function definition."""
    name: str
    start_line: int
    end_line: int
    full_definition: str
    
    @property
    def target(self) -> MacroTarget:
        """Convert to MacroTarget for use with macros."""
        return MacroTarget(
            target_type="function",
            start_line=self.start_line,
            end_line=self.end_line,
            content=self.full_definition,
            metadata={"function_name": self.name}
        )

class MacroComment(BaseModel):
    """Represents a macro annotation comment."""
    line_number: int
    content: str
    macro_type: str  # 'iteration', 'parallel', etc.
    raw_line: str

class IterationMacro(BaseModel):
    """Represents a parsed iteration macro."""
    comment: MacroComment
    target: Optional[MacroTarget] = None
    iterator_var: str
    source: str
    source_type: Optional[str] = None  # Explicit type like 'file', 'array', etc.
    iteration_type: str  # 'file_lines', 'array', 'pattern', 'delimited', etc.
    separator: Optional[str] = None  # Delimiter for delimited iteration
    additional_params: List[str] = []
    
    def generate_transformation(self) -> str:
        """Generate the bash loop code."""
        if not self.target:
            raise ValueError("No target set for iteration macro")
        
        if self.target.target_type == 'function':
            return self._generate_function_loop()
        else:
            return self._generate_line_loop()
    
    def _generate_function_loop(self) -> str:
        """Generate loop that calls a function."""
        func_name = self.target.metadata['function_name']
        
        # Build parameters
        params = [f'"${self.iterator_var}"']
        params.extend(f'"{param}"' for param in self.additional_params)
        param_str = ' '.join(params)
        
        if self.iteration_type == 'file_lines':
            return f'''while IFS= read -r {self.iterator_var}; do
    {func_name} {param_str}
done < {self.source}'''
        elif self.iteration_type == 'delimited':
            return self._generate_delimited_function_loop(func_name, param_str)
        else:
            return f'''for {self.iterator_var} in {self.source}; do
    {func_name} {param_str}
done'''
    
    def _generate_line_loop(self) -> str:
        """Generate loop that wraps a line."""
        target_line = self.target.content.strip()
        
        if self.iteration_type == 'file_lines':
            return f'''while IFS= read -r {self.iterator_var}; do
    {target_line}
done < {self.source}'''
        elif self.iteration_type == 'delimited':
            return self._generate_delimited_line_loop(target_line)
        else:
            return f'''for {self.iterator_var} in {self.source}; do
    {target_line}
done'''
    
    def _escape_separator_for_ifs(self, separator: str) -> str:
        """Escape separator for use in IFS assignment."""
        # Use $'...' format for all special characters to avoid quoting issues
        if separator == "'":
            return "$'\\047'"  # Octal for single quote
        elif separator == '"':
            return '$"\""'  # Use $"..." format for double quote
        elif separator == '\\':
            return "$'\\\\'"  # Backslash
        elif separator == '\t':
            return "$'\\t'"  # Tab
        elif separator == '\n':
            return "$'\\n'"  # Newline  
        elif separator == '\r':
            return "$'\\r'"  # Carriage return
        else:
            # For regular characters, use simple single quotes
            return f"'{separator}'"

    def _escape_separator_for_sed(self, separator: str) -> str:
        """Escape separator for use in sed substitution."""
        # Create escaped version character by character
        result = ""
        for char in separator:
            if char == '.':
                result += '\\.'
            elif char == '*':
                result += '\\*'
            elif char == '[':
                result += '\\['
            elif char == ']':
                result += '\\]'
            elif char == '^':
                result += '\\^'
            elif char == '$':
                result += '\\$'
            elif char == '(':
                result += '\\('
            elif char == ')':
                result += '\\)'
            elif char == '+':
                result += '\\+'
            elif char == '{':
                result += '\\{'
            elif char == '}':
                result += '\\}'
            elif char == '|':
                result += '\\|'
            elif char == '?':
                result += '\\?'
            elif char == '\\':
                result += '\\\\'
            elif char == '/':
                result += '\\/'
            else:
                result += char
        
        return result

    def _generate_delimited_function_loop(self, func_name: str, param_str: str) -> str:
        """Generate delimited iteration loop that calls a function."""
        if not self.separator:
            raise ValueError("Separator required for delimited iteration")
        
        # Generate temporary array name
        temp_array = f"ARGORATOR_ARRAY_{id(self) % 10000}"
        
        # Handle single character vs multi-character separators
        if len(self.separator) == 1:
            # Single character: use IFS
            ifs_separator = self._escape_separator_for_ifs(self.separator)
            return f'''IFS={ifs_separator} read -ra {temp_array} <<< {self.source}
for {self.iterator_var} in "${{{temp_array}[@]}}"; do
    {func_name} {param_str}
done'''
        else:
            # Multi-character: use parameter expansion
            escaped_sep = self._escape_separator_for_sed(self.separator)
            # Use format() instead of f-string to avoid double-escaping backslashes
            return '''{temp_array}=()
IFS=$'\\n' read -d '' -ra {temp_array} < <(echo {source} | sed 's/{escaped_sep}/\\n/g' && printf '\\0')
for {iterator_var} in "${{{temp_array}[@]}}"; do
    {func_name} {param_str}
done'''.format(
                temp_array=temp_array,
                source=self.source,
                escaped_sep=escaped_sep,
                iterator_var=self.iterator_var,
                func_name=func_name,
                param_str=param_str
            )
    
    def _generate_delimited_line_loop(self, target_line: str) -> str:
        """Generate delimited iteration loop that wraps a line."""
        if not self.separator:
            raise ValueError("Separator required for delimited iteration")
        
        # Generate temporary array name
        temp_array = f"ARGORATOR_ARRAY_{id(self) % 10000}"
        
        # Handle single character vs multi-character separators
        if len(self.separator) == 1:
            # Single character: use IFS
            ifs_separator = self._escape_separator_for_ifs(self.separator)
            return f'''IFS={ifs_separator} read -ra {temp_array} <<< {self.source}
for {self.iterator_var} in "${{{temp_array}[@]}}"; do
    {target_line}
done'''
        else:
            # Multi-character: use parameter expansion
            escaped_sep = self._escape_separator_for_sed(self.separator)
            # Use format() instead of f-string to avoid double-escaping backslashes
            return '''{temp_array}=()
IFS=$'\\n' read -d '' -ra {temp_array} < <(echo {source} | sed 's/{escaped_sep}/\\n/g' && printf '\\0')
for {iterator_var} in "${{{temp_array}[@]}}"; do
    {target_line}
done'''.format(
                temp_array=temp_array,
                source=self.source,
                escaped_sep=escaped_sep,
                iterator_var=self.iterator_var,
                target_line=target_line
            )