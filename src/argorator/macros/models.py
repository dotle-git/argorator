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
    iteration_type: str  # 'file_lines', 'array', 'pattern', etc.
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
        else:
            return f'''for {self.iterator_var} in {self.source}; do
    {target_line}
done'''