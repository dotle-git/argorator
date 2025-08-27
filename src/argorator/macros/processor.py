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
        
        # Validate macro combinations and detect conflicts
        self._validate_macro_combinations(processed_macros)
        
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
    
    def _generate_nested_loop_alternatives(self, macros: List[IterationMacro], target_line: int) -> str:
        """Generate specific workaround suggestions for nested loop conflicts."""
        alternatives = []
        
        # Option 1: Separate lines approach
        alternatives.append(
            "1️⃣  SEPARATE LINES: Put each loop on its own line\n"
            "   Example:\n"
            "   # for dir in */\n"
            "   echo \"Processing directory: $dir\"\n"
            "   \n"
            "   # for file in $dir/*.txt  \n"
            "   echo \"Processing file: $file\""
        )
        
        # Option 2: Function-based approach
        if len(macros) == 2:
            outer_macro = macros[0]  # Typically the first one
            inner_macro = macros[1]
            
            alternatives.append(
                f"2️⃣  FUNCTION APPROACH: Use a function for the inner loop\n"
                f"   Example:\n"
                f"   # {outer_macro.comment.content}\n"
                f"   process_item() {{\n"
                f"       # {inner_macro.comment.content}\n"
                f"       echo \"Processing: $1 -> ${inner_macro.iterator_var}\"\n"
                f"   }}"
            )
        
        # Option 3: Single combined macro (if possible)
        if len(macros) == 2 and all(m.iteration_type in ['pattern', 'array'] for m in macros):
            alternatives.append(
                "3️⃣  COMBINE PATTERNS: Use a single pattern if possible\n"
                "   Example: # for file in */*.txt (if that matches your intent)"
            )
        
        return "\n\n".join(alternatives)
    
    def _generate_function_conflict_alternatives(self, func_macro: IterationMacro, internal_macros: List[IterationMacro]) -> str:
        """Generate specific workaround suggestions for function macro conflicts."""
        alternatives = []
        func_name = func_macro.target.metadata.get('function_name', 'process_item')
        
        # Option 1: Remove function macro, use internal only
        alternatives.append(
            "1️⃣  INTERNAL ONLY: Remove the function-level macro\n"
            "   Keep the internal macros and call the function manually:\n"
            f"   \n"
            f"   {func_name}() {{\n"
            f"       # Keep your internal macros here\n"
            f"       # {internal_macros[0].comment.content}\n"
            f"       echo \"Processing: ${internal_macros[0].iterator_var}\"\n"
            f"   }}\n"
            f"   \n"
            f"   # Call it manually for each item\n"
            f"   {func_name}"
        )
        
        # Option 2: Remove internal macros, use function-level only  
        alternatives.append(
            "2️⃣  FUNCTION-LEVEL ONLY: Remove internal macros\n"
            "   Let the function-level macro handle iteration:\n"
            f"   \n"
            f"   # {func_macro.comment.content}\n"
            f"   {func_name}() {{\n"
            f"       echo \"Processing: $1\"  # $1 will be the {func_macro.iterator_var}\n"
            f"       # Process $1 directly here\n"
            f"   }}"
        )
        
        # Option 3: Sequential approach
        alternatives.append(
            "3️⃣  SEQUENTIAL: Separate the operations\n"
            "   Use the function macro, then add separate processing:\n"
            f"   \n"
            f"   # {func_macro.comment.content}\n"
            f"   {func_name}() {{\n"
            f"       echo \"Stage 1: $1\"\n"
            f"   }}\n"
            f"   \n"
            f"   # Separate processing\n"
            f"   # {internal_macros[0].comment.content}\n"
            f"   echo \"Stage 2: ${internal_macros[0].iterator_var}\""
        )
        
        return "\n\n".join(alternatives)
    
    def _generate_syntax_error_help(self, comment: MacroComment, error_msg: str) -> str:
        """Generate helpful syntax error messages with examples."""
        content = comment.content.strip()
        
        help_sections = []
        
        # Show what they wrote
        help_sections.append(f"📝 Your macro: # {content}")
        help_sections.append(f"⚠️  Error: {error_msg}")
        
        # Provide correct syntax examples
        examples = [
            "✅ CORRECT SYNTAX EXAMPLES:",
            "   # for file in *.txt",
            "   # for line in $FILE as file", 
            "   # for item in $CSV_DATA sep ,",
            "   # for field in $PATH separated by :",
            "   # for part in $TEXT separated by \"::\"",
            "   # for i in {1..10}",
            "   # for file in *.log | with $OUTPUT_DIR"
        ]
        help_sections.append("\n".join(examples))
        
        # Common fixes based on the error
        if "Invalid iteration macro syntax" in error_msg:
            fixes = [
                "🔧 COMMON FIXES:",
                "   • Check that you have: for VARIABLE in SOURCE",
                "   • Variable names must be valid: letters, numbers, underscore",
                "   • Source must be specified (not empty)",
                "   • Use quotes for multi-word separators: \"::\" not ::"
            ]
            help_sections.append("\n".join(fixes))
        
        # Documentation link
        help_sections.append(
            "📚 FULL DOCUMENTATION: https://github.com/dotle-git/argorator#iteration-macros\n"
            "🐛 REPORT ISSUES: https://github.com/dotle-git/argorator/issues/new"
        )
        
        return "\n\n".join(help_sections)
    
    def _validate_macro_combinations(self, macros: List[IterationMacro]) -> None:
        """Validate macro combinations and detect conflicts."""
        # Group macros by their target lines
        target_groups = {}
        function_macros = []
        
        for macro in macros:
            if macro.target.target_type == 'function':
                function_macros.append(macro)
            else:
                # Group line-based macros by target line
                target_line = macro.target.start_line
                if target_line not in target_groups:
                    target_groups[target_line] = []
                target_groups[target_line].append(macro)
        
        # Check for multiple macros targeting the same line
        for target_line, line_macros in target_groups.items():
            if len(line_macros) > 1:
                macro_lines = [m.comment.line_number + 1 for m in line_macros]
                macro_contents = [m.comment.content for m in line_macros]
                
                alternatives = self._generate_nested_loop_alternatives(line_macros, target_line)
                
                raise ValueError(
                    f"❌ UNSUPPORTED: Multiple iteration macros target the same line {target_line + 1}\n\n"
                    f"📍 Found macros on lines: {', '.join(map(str, macro_lines))}\n"
                    f"   {chr(10).join([f'   Line {macro_lines[i]}: # {macro_contents[i]}' for i in range(len(macro_lines))])}\n\n"
                    f"🔧 WORKAROUNDS:\n{alternatives}\n\n"
                    f"💡 WANT NESTED LOOPS? This feature isn't implemented yet.\n"
                    f"   👆 Please create a GitHub issue: https://github.com/dotle-git/argorator/issues/new\n"
                    f"   📝 Title: 'Support nested iteration macros'\n"
                    f"   📋 Include your use case and the script above."
                )
        
        # Check for function macros with internal conflicts
        for func_macro in function_macros:
            # Find any line macros that fall within this function's range
            func_start = func_macro.target.start_line
            func_end = func_macro.target.end_line
            
            conflicting_lines = []
            for target_line, line_macros in target_groups.items():
                if func_start < target_line < func_end:
                    conflicting_lines.extend(line_macros)
            
            if conflicting_lines:
                func_line = func_macro.comment.line_number + 1
                func_name = func_macro.target.metadata.get('function_name', 'unknown')
                internal_lines = [m.comment.line_number + 1 for m in conflicting_lines]
                internal_contents = [m.comment.content for m in conflicting_lines]
                
                alternatives = self._generate_function_conflict_alternatives(func_macro, conflicting_lines)
                
                raise ValueError(
                    f"❌ UNSUPPORTED: Function macro with internal iteration macros\n\n"
                    f"📍 Function macro: Line {func_line} (function '{func_name}')\n"
                    f"   # {func_macro.comment.content}\n\n"
                    f"⚠️  Internal macros found:\n"
                    f"   {chr(10).join([f'   Line {internal_lines[i]}: # {internal_contents[i]}' for i in range(len(internal_lines))])}\n\n"
                    f"🔧 WORKAROUNDS:\n{alternatives}\n\n"
                    f"💡 WANT FUNCTION-LEVEL + INTERNAL MACROS? This isn't supported yet.\n"
                    f"   👆 Please create a GitHub issue: https://github.com/dotle-git/argorator/issues/new\n"
                    f"   📝 Title: 'Support function macros with internal iteration macros'\n"
                    f"   📋 Include your use case and the script above."
                )
    
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
                    error_details = self._generate_syntax_error_help(comment, str(e))
                    errors.append(f"❌ INVALID MACRO SYNTAX (Line {comment.line_number + 1})\n{error_details}")
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