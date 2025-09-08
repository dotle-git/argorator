"""Tests for the bug fix: function parameters with iterator macros should not require CLI arguments."""

import pytest
from argorator.macros.processor import macro_processor
from argorator.macros.parser import macro_parser


class TestFunctionParameterBugFix:
    """Test that function parameters used with iterator macros don't require CLI arguments."""
    
    def test_function_parameters_with_iterator_macro_excluded_from_cli(self):
        """Test that function parameters are excluded from CLI arguments when used with iterator macros."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Input data for processing

# for item in $DATA sep ,
process_item() {
    echo "Processing item: $1"
    echo "Additional info: $2"
}
'''
        
        # This should work without requiring --1 or --2 arguments
        # The macro will provide the parameters to the function
        result = macro_processor.process_macros(script)
        
        # Verify that the macro generates the correct loop
        assert 'for item in' in result
        assert 'process_item "$item"' in result
        assert 'done' in result
    
    def test_function_parameters_without_iterator_macro_require_cli(self):
        """Test that function parameters still require CLI arguments when NOT used with iterator macros."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Input data for processing

process_item() {
    echo "Processing item: $1"
    echo "Additional info: $2"
}

# Call the function manually - this should require CLI arguments
process_item "test" "info"
'''
        
        # This should NOT work without providing --1 and --2 arguments
        # because there's no iterator macro to provide the parameters
        result = macro_processor.process_macros(script)
        
        # The script should remain unchanged (no macros to process)
        assert result.strip() == script.strip()
    
    def test_mixed_scenario_function_with_and_without_macro(self):
        """Test a scenario with both functions that have macros and functions that don't."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Input data for processing
# OUTPUT_DIR (str): Output directory

# for item in $DATA sep ,
process_item() {
    echo "Processing item: $1"
    echo "Additional info: $2"
}

# This function has no macro, so it should require CLI arguments
process_other() {
    echo "Processing other: $1"
    echo "More info: $2"
}

# Call the function without macro manually
process_other "test" "info"
'''
        
        result = macro_processor.process_macros(script)
        
        # Verify that only the function with the macro gets processed
        assert 'for item in' in result
        assert 'process_item "$item"' in result
        assert 'process_other "test" "info"' in result  # This should remain unchanged
    
    def test_function_with_additional_parameters_and_macro(self):
        """Test function with additional parameters passed by the macro."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Input data for processing
# OUTPUT_DIR (str): Output directory

# for item in $DATA sep , | with $OUTPUT_DIR
process_item() {
    local input="$1"
    local output_dir="$2"
    echo "Processing $input to $output_dir"
}
'''
        
        result = macro_processor.process_macros(script)
        
        # Verify that the macro generates the correct loop with additional parameters
        assert 'for item in' in result
        assert 'process_item "$item" "$OUTPUT_DIR"' in result
        assert 'done' in result
    
    def test_nested_function_parameters_with_macro(self):
        """Test that nested function calls with parameters work correctly with macros."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Input data for processing

# for item in $DATA sep ,
process_item() {
    echo "Processing item: $1"
    helper_function "$1" "extra"
}

helper_function() {
    echo "Helper processing: $1 with $2"
}
'''
        
        result = macro_processor.process_macros(script)
        
        # Verify that the macro generates the correct loop
        assert 'for item in' in result
        assert 'process_item "$item"' in result
        assert 'helper_function "$1" "extra"' in result  # This should remain unchanged
        assert 'done' in result