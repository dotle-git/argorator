"""Unified Parsy-based parsers for all shell script language features.

This module replaces regex-based parsing with Parsy parsers for consistency
and better error handling across the codebase.
"""
import parsy
import re
from typing import Dict, List, Optional, Set, Tuple
from .models import ArgumentAnnotation, ScriptMetadata


class ShellScriptParser:
    """Unified parser for shell script language features using Parsy."""
    
    def __init__(self):
        self._setup_grammar()
    
    def _setup_grammar(self):
        """Setup Parsy grammar for shell script parsing."""
        # Basic tokens
        self.whitespace = parsy.regex(r'\s*')
        self.optional_whitespace = parsy.regex(r'\s*')
        self.required_whitespace = parsy.regex(r'\s+')
        self.identifier = parsy.regex(r'[a-zA-Z_][a-zA-Z0-9_]*')
        self.uppercase_identifier = parsy.regex(r'[A-Z_][A-Z0-9_]*')
        self.number = parsy.regex(r'[0-9]+')
        
        # Comment parsing
        self.hash = parsy.string('#')
        
        # Setup Google-style annotation grammar
        self._setup_annotation_grammar()
        
        # Setup variable parsing grammar  
        self._setup_variable_grammar()
        
        # Setup positional parameter grammar
        self._setup_positional_grammar()
    
    def _setup_annotation_grammar(self):
        """Setup grammar for Google-style annotations."""
        # Variable name - can be any case, will be normalized to uppercase
        var_name = parsy.regex(r'[A-Za-z_][A-Za-z0-9_]*')
        
        # Type definitions
        simple_types = parsy.regex(r'bool|int|float|str|string|file')
        
        # Choice type with options: choice[opt1, opt2, opt3]
        choice_option = parsy.regex(r'[^,\]]+').map(str.strip)
        choice_options = choice_option.sep_by(parsy.string(','), min=1)
        choice_type = parsy.seq(
            parsy.string('choice'),
            parsy.string('['),
            choice_options,
            parsy.string(']')
        ).combine(lambda _, __, choices, ___: ('choice', choices))
        
        # Type specification: (type) or (choice[...])
        type_spec = parsy.seq(
            parsy.string('('),
            self.optional_whitespace,
            choice_type | simple_types.map(lambda t: (t, None)),
            self.optional_whitespace,
            parsy.string(')')
        ).combine(lambda _, __, type_info, ___, ____: type_info)
        
        # Alias specification: [alias: -x]
        alias_spec = parsy.seq(
            parsy.string('['),
            self.optional_whitespace,
            parsy.string('alias'),
            self.optional_whitespace,
            parsy.string(':'),
            self.optional_whitespace,
            parsy.regex(r'[^\]]+'),
            self.optional_whitespace,
            parsy.string(']')
        ).combine(lambda _, __, ___, ____, _____, ______, alias, _______, ________: alias.strip())
        
        # Description text (up to period or end of line)
        description_text = parsy.regex(r'[^.]+').map(str.strip)
        
        # Default value: Default: value
        default_spec = parsy.seq(
            parsy.string('.'),
            self.optional_whitespace,
            parsy.regex(r'[Dd]efault'),
            self.optional_whitespace,
            parsy.string(':'),
            self.optional_whitespace,
            parsy.regex(r'.+')
        ).combine(lambda _, __, ___, ____, _____, ______, default: default.strip())
        
        # Complete annotation pattern
        # # VAR_NAME (type) [alias: -x]: description. Default: value
        self.annotation_pattern = parsy.seq(
            self.hash,
            self.optional_whitespace,
            var_name,
            self.optional_whitespace,
            type_spec.optional(),
            self.optional_whitespace,
            alias_spec.optional(),
            self.optional_whitespace,
            parsy.string(':'),
            self.optional_whitespace,
            description_text,
            default_spec.optional()
        ).combine(lambda _, __, var, ___, type_info, ____, alias, _____, ______, _______, desc, default: {
            'var_name': var,
            'type_info': type_info,
            'alias': alias,
            'description': desc,
            'default': default
        })
        
        # Description parsing for script metadata
        description_keyword = parsy.regex(r'[Dd]escription', re.IGNORECASE)
        colon = parsy.string(':')
        description_line = parsy.regex(r'.+')
        
        self.description_pattern = parsy.seq(
            self.hash,
            self.optional_whitespace,
            description_keyword,
            self.optional_whitespace,
            colon,
            self.optional_whitespace,
            description_line
        ).combine(lambda _, __, ___, ____, _____, ______, desc: desc.strip())
    
    def _setup_variable_grammar(self):
        """Setup grammar for variable assignments and usage."""
        # Variable assignment patterns
        # export VAR=value, local VAR=value, declare VAR=value, readonly VAR=value, VAR=value
        assignment_prefix = parsy.seq(
            parsy.string('export') | 
            parsy.string('local') | 
            parsy.string('readonly') |
            parsy.seq(parsy.string('declare'), parsy.regex(r'\s+-[a-zA-Z]+').optional()).combine(lambda d, flags: 'declare'),
            self.required_whitespace
        ).optional()
        
        assignment_value = parsy.regex(r'[^=]*')  # Everything after =
        
        self.variable_assignment = parsy.seq(
            self.optional_whitespace,
            assignment_prefix,
            self.identifier,
            self.optional_whitespace,
            parsy.string('='),
            assignment_value
        ).combine(lambda _, __, var_name, ___, ____, _____: var_name)
        
        # Variable usage patterns: $VAR and ${VAR...}
        simple_var_usage = parsy.seq(
            parsy.string('$'),
            self.identifier
        ).combine(lambda _, var_name: var_name)
        
        brace_var_usage = parsy.seq(
            parsy.string('${'),
            self.identifier,
            parsy.regex(r'[^}]*'),  # Rest of brace content
            parsy.string('}')
        ).combine(lambda _, var_name, __, ___: var_name)
        
        self.variable_usage = brace_var_usage | simple_var_usage
    
    def _setup_positional_grammar(self):
        """Setup grammar for positional parameters."""
        # Positional parameters: $1, $2, etc.
        self.positional_param = parsy.seq(
            parsy.string('$'),
            parsy.regex(r'[1-9][0-9]*')
        ).combine(lambda _, num: int(num))
        
        # Varargs patterns: $@ or $*
        self.varargs_param = parsy.seq(
            parsy.string('$'),
            parsy.regex(r'[@*]')
        ).result(True)
    
    def parse_arg_annotations(self, script_text: str) -> Dict[str, ArgumentAnnotation]:
        """Parse Google-style argument annotations from script text.
        
        Args:
            script_text: The shell script content
            
        Returns:
            Dictionary mapping variable names to ArgumentAnnotation objects
        """
        annotations = {}
        lines = script_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line.startswith('#'):
                continue
            
            try:
                result = self.annotation_pattern.parse(line)
                
                # Extract parsed components
                var_name = result['var_name'].upper()  # Normalize to uppercase
                type_info = result['type_info']
                alias = result['alias']
                description = result['description']
                default = result['default']
                
                # Build annotation data
                annotation_data = {
                    'help': description
                }
                
                if type_info:
                    var_type, choices = type_info
                    # Normalize type
                    if var_type.lower() in ('string', 'str'):
                        var_type = 'str'
                    else:
                        var_type = var_type.lower()
                    
                    annotation_data['type'] = var_type
                    
                    if var_type == 'choice' and choices:
                        annotation_data['choices'] = choices
                else:
                    annotation_data['type'] = 'str'  # Default type
                
                if default:
                    annotation_data['default'] = default
                
                if alias:
                    annotation_data['alias'] = alias
                
                # Create ArgumentAnnotation model
                annotations[var_name] = ArgumentAnnotation(**annotation_data)
                
            except parsy.ParseError:
                # Not a valid annotation, continue
                continue
        
        return annotations
    
    def parse_script_description(self, script_text: str) -> Optional[str]:
        """Parse script description from comments.
        
        Args:
            script_text: The shell script content
            
        Returns:
            Script description if found, None otherwise
        """
        lines = script_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line.startswith('#'):
                continue
            
            try:
                result = self.description_pattern.parse(line)
                return result
            except parsy.ParseError:
                continue
        
        return None
    
    def parse_defined_variables(self, script_text: str) -> Set[str]:
        """Extract variable names that are assigned within the script.
        
        Args:
            script_text: The shell script content
            
        Returns:
            Set of variable names that are defined in the script
        """
        variables = set()
        lines = script_text.split('\n')
        
        for line in lines:
            # Try to parse each line for variable assignments
            try:
                var_name = self.variable_assignment.parse(line)
                variables.add(var_name)
            except parsy.ParseError:
                continue
        
        return variables
    
    def parse_variable_usages(self, script_text: str) -> Set[str]:
        """Find variable names referenced by $VAR or ${VAR...} syntax.
        
        Args:
            script_text: The shell script content
            
        Returns:
            Set of variable names that are used in the script
        """
        variables = set()
        
        # Create a parser that captures variable usage and allows any other character
        anything = parsy.regex(r'.', re.DOTALL)  # DOTALL makes . match newlines too
        variable_or_other = self.variable_usage.map(lambda v: ('var', v)) | anything.map(lambda c: ('other', c))
        
        # Parse the entire text to find all variable usages
        try:
            result = variable_or_other.many().parse(script_text)
            
            for item_type, value in result:
                if item_type == 'var':
                    variables.add(value)
        except parsy.ParseError:
            # Fallback to a simpler approach if parsing fails
            brace_pattern = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)[^}]*\}')
            simple_pattern = re.compile(r'\$([A-Za-z_][A-Za-z0-9_]*)')
            
            variables.update(brace_pattern.findall(script_text))
            for match in simple_pattern.finditer(script_text):
                start_pos = match.start()
                if start_pos == 0 or script_text[start_pos - 1] != '{':
                    variables.add(match.group(1))
        
        # Filter out special shell variables
        special_vars = {"@", "*", "#", "?", "$", "!", "0"}
        return {name for name in variables if name not in special_vars}
    
    def parse_positional_usages(self, script_text: str) -> Tuple[Set[int], bool]:
        """Extract positional parameter indices and varargs usage from script.
        
        Args:
            script_text: The shell script content
            
        Returns:
            Tuple of (positional_indices, varargs_present)
        """
        indices = set()
        varargs = False
        
        # Create a parser that captures positional usage and allows any other character
        anything = parsy.regex(r'.', re.DOTALL)  # DOTALL makes . match newlines too
        positional_or_varargs_or_other = (
            self.positional_param.map(lambda i: ('pos', i)) |
            self.varargs_param.map(lambda _: ('varargs', True)) |
            anything.map(lambda c: ('other', c))
        )
        
        # Parse the entire text to find all positional usages
        try:
            result = positional_or_varargs_or_other.many().parse(script_text)
            
            for item_type, value in result:
                if item_type == 'pos':
                    indices.add(value)
                elif item_type == 'varargs':
                    varargs = True
        except parsy.ParseError:
            # Fallback to regex approach if parsing fails
            digit_pattern = re.compile(r'\$([1-9][0-9]*)')
            varargs_pattern = re.compile(r'\$[@*]')
            
            indices = {int(m) for m in digit_pattern.findall(script_text)}
            varargs = bool(varargs_pattern.search(script_text))
        
        return indices, varargs


# Global parser instance
script_parser = ShellScriptParser()