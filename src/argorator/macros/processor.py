"""Main macro processor that integrates with existing Argorator pipeline."""
from typing import List, Dict, Optional
from .parser import macro_parser
from .models import IterationMacro, MacroComment, MacroTarget

class MacroProcessor:
    """Main processor for macro transformations."""
    
    def __init__(self):
        self.parser = macro_parser
        self.variable_types: Dict[str, str] = {}  # Map variable names to their types
    
    def set_variable_types(self, variable_types: Dict[str, str]) -> None:
        """Set variable type information from argument annotations."""
        self.variable_types = variable_types.copy()
    
    def process_macros(self, script_text: str) -> str:
        """Process all macros in the script and return transformed script."""
        # Find all macro comments
        macro_comments = self.parser.find_macro_comments(script_text)
        
        if not macro_comments:
            return script_text  # No macros to process
        
        # Process each macro
        processed_macros = []
        for comment in macro_comments:
            if comment.macro_type == 'iteration':
                target = self.parser.find_target_for_macro(script_text, comment.line_number)
                if target:
                    try:
                        iteration_macro = self.parser.parse_iteration_macro(comment, target)
                        # Enhance iteration type based on variable type information
                        self._enhance_iteration_type(iteration_macro)
                        processed_macros.append(iteration_macro)
                    except ValueError as e:
                        # Log error but don't fail the entire process
                        print(f"Warning: Failed to parse macro on line {comment.line_number + 1}: {e}")
        
        # Apply transformations
        return self._apply_transformations(script_text, processed_macros)
    
    def _apply_transformations(self, script_text: str, macros: List[IterationMacro]) -> str:
        """Apply macro transformations to the script."""
        lines = script_text.split('\n')
        
        # Process macros in reverse order to maintain line numbers
        for macro in sorted(macros, key=lambda m: m.comment.line_number, reverse=True):
            transformation = macro.generate_transformation()
            lines = self._apply_single_transformation(lines, macro, transformation)
        
        return '\n'.join(lines)
    
    def _apply_single_transformation(self, lines: List[str], macro: IterationMacro, transformation: str) -> List[str]:
        """Apply a single macro transformation."""
        if macro.target.target_type == 'function':
            # Insert loop after function definition
            insertion_point = macro.target.end_line + 1
            transformation_lines = [''] + transformation.split('\n')
            
            # Insert transformation
            for i, line in enumerate(transformation_lines):
                lines.insert(insertion_point + i, line)
                
        elif macro.target.target_type == 'line':
            # Replace target line with loop
            target_line = macro.target.start_line
            lines[target_line:target_line + 1] = transformation.split('\n')
        
        # Remove the original macro comment
        del lines[macro.comment.line_number]
        
        return lines
    
    def _enhance_iteration_type(self, macro: IterationMacro) -> None:
        """Enhance iteration type based on variable type information."""
        # If separator is provided, it's already delimited - don't change
        if macro.separator is not None:
            return
        
        # If explicit type is already provided, keep it
        if macro.source_type:
            return
        
        # Extract variable name from source (handle $VAR format)
        source = macro.source.strip()
        if source.startswith('$'):
            var_name = source[1:]  # Remove $
            # Handle ${VAR} format
            if var_name.startswith('{') and var_name.endswith('}'):
                var_name = var_name[1:-1]
            
            # Look up variable type and update iteration type
            if var_name in self.variable_types:
                var_type = self.variable_types[var_name]
                if var_type == 'file':
                    macro.iteration_type = 'file_lines'
                    macro.source_type = 'file'
                # Add more type mappings as needed
                elif var_type in ['array', 'list']:
                    macro.iteration_type = 'array'
                    macro.source_type = 'array'
    
    def validate_macros(self, script_text: str) -> List[str]:
        """Validate macros and return any error messages."""
        errors = []
        macro_comments = self.parser.find_macro_comments(script_text)
        
        for comment in macro_comments:
            if comment.macro_type == 'iteration':
                try:
                    target = self.parser.find_target_for_macro(script_text, comment.line_number)
                    if not target:
                        errors.append(f"Line {comment.line_number + 1}: No target found for macro")
                        continue
                    
                    # Try to parse the macro
                    self.parser.parse_iteration_macro(comment, target)
                    
                except ValueError as e:
                    errors.append(f"Line {comment.line_number + 1}: {e}")
                except Exception as e:
                    errors.append(f"Line {comment.line_number + 1}: Unexpected error: {e}")
        
        return errors
    
    def list_macros(self, script_text: str) -> List[Dict]:
        """List all detected macros for debugging/info purposes."""
        macro_comments = self.parser.find_macro_comments(script_text)
        result = []
        
        for comment in macro_comments:
            target = self.parser.find_target_for_macro(script_text, comment.line_number)
            macro_info = {
                'line': comment.line_number + 1,
                'type': comment.macro_type,
                'content': comment.content,
                'target_type': target.target_type if target else 'none',
                'target_lines': f"{target.start_line + 1}-{target.end_line + 1}" if target else 'none'
            }
            
            if comment.macro_type == 'iteration' and target:
                try:
                    iteration_macro = self.parser.parse_iteration_macro(comment, target)
                    macro_info.update({
                        'iterator': iteration_macro.iterator_var,
                        'source': iteration_macro.source,
                        'iteration_type': iteration_macro.iteration_type,
                        'params': iteration_macro.additional_params
                    })
                except:
                    macro_info['error'] = 'Failed to parse'
            
            result.append(macro_info)
        
        return result

# Global processor instance
macro_processor = MacroProcessor()