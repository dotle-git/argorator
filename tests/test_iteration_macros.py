"""Tests for iteration macro functionality."""
import pytest
from src.argorator.macros.processor import macro_processor
from src.argorator.macros.parser import macro_parser

class TestMacroParser:
    """Test the macro parser functionality."""
    
    def test_find_simple_function(self):
        """Test finding a simple function definition."""
        script = '''#!/bin/bash
process_file() {
    echo "Processing $1"
}'''
        functions = macro_parser.find_functions(script)
        assert len(functions) == 1
        assert functions[0].name == "process_file"
        assert functions[0].start_line == 1
        assert functions[0].end_line == 3
    
    def test_find_function_with_keyword(self):
        """Test finding function with 'function' keyword."""
        script = '''function process_file() {
    echo "Processing $1"
    return 0
}'''
        functions = macro_parser.find_functions(script)
        assert len(functions) == 1
        assert functions[0].name == "process_file"
    
    def test_find_iteration_macro_comment(self):
        """Test finding iteration macro comments."""
        script = '''# for file in *.txt
echo "Processing $file"

# This is not a macro
echo "Hello"

# for line in $INPUT_FILE
cat "$line"'''
        
        comments = macro_parser.find_macro_comments(script)
        assert len(comments) == 2
        assert comments[0].macro_type == "iteration"
        assert comments[1].macro_type == "iteration"
        assert "file in *.txt" in comments[0].content
        assert "line in $INPUT_FILE" in comments[1].content

class TestIterationMacros:
    """Test iteration macro processing."""
    
    def setup_method(self):
        """Reset macro processor state before each test."""
        macro_processor.set_variable_types({})
    
    def test_simple_line_macro(self):
        """Test macro that applies to a single line."""
        script = '''# for file in *.txt
echo "Processing $file"'''
        
        result = macro_processor.process_macros(script)
        expected = '''for file in *.txt; do
    echo "Processing $file"
done'''
        assert result.strip() == expected.strip()
    
    def test_file_type_annotation(self):
        """Test macro with file type from annotation."""
        script = '''# for line in $INPUT_FILE
echo "Processing: $line"'''
        
        # Set variable type information
        macro_processor.set_variable_types({'INPUT_FILE': 'file'})
        
        result = macro_processor.process_macros(script)
        expected = '''while IFS= read -r line; do
    echo "Processing: $line"
done < $INPUT_FILE'''
        assert result.strip() == expected.strip()
    
    def test_explicit_as_file_syntax(self):
        """Test macro with explicit 'as file' syntax."""
        script = '''# for line in $DATA as file
echo "Processing: $line"'''
        
        result = macro_processor.process_macros(script)
        expected = '''while IFS= read -r line; do
    echo "Processing: $line"
done < $DATA'''
        assert result.strip() == expected.strip()
    
    def test_parenthesized_as_syntax(self):
        """Test macro with parenthesized 'as type' syntax."""
        script = '''# for line in ($INPUT_FILE as file)
echo "Processing: $line"'''
        
        result = macro_processor.process_macros(script)
        expected = '''while IFS= read -r line; do
    echo "Processing: $line"
done < $INPUT_FILE'''
        assert result.strip() == expected.strip()
    
    def test_function_macro(self):
        """Test macro that applies to a function."""
        script = '''# for file in *.log
process_log() {
    echo "Processing: $1"
    grep "ERROR" "$1" > "$1.errors"
}'''
        
        result = macro_processor.process_macros(script)
        
        # Should contain the original function plus a loop that calls it
        assert "process_log() {" in result
        assert "for file in *.log; do" in result
        assert 'process_log "$file"' in result
        assert "done" in result
    
    def test_file_lines_iteration_with_type(self):
        """Test iteration over file lines using type information."""
        script = '''# for line in $INPUT_FILE
echo "Line: $line"'''
        
        # Set file type to trigger file_lines iteration
        macro_processor.set_variable_types({'INPUT_FILE': 'file'})
        
        result = macro_processor.process_macros(script)
        expected = '''while IFS= read -r line; do
    echo "Line: $line"
done < $INPUT_FILE'''
        assert result.strip() == expected.strip()
    
    def test_function_with_parameters(self):
        """Test function macro with additional parameters."""
        script = '''# for file in *.txt | with $OUTPUT_DIR
convert_file() {
    local input="$1"
    local output_dir="$2"
    cp "$input" "$output_dir/"
}'''
        
        result = macro_processor.process_macros(script)
        
        # Should pass both the iterator and additional parameter
        assert 'convert_file "$file" "$OUTPUT_DIR"' in result
    
    def test_no_macros(self):
        """Test script with no macros returns unchanged."""
        script = '''#!/bin/bash
echo "Hello World"
echo "No macros here"'''
        
        result = macro_processor.process_macros(script)
        assert result == script
    
    def test_macro_validation(self):
        """Test macro validation works for valid syntax."""
        # Valid syntax should pass validation
        script = '''# for var in source
echo "test"'''
        
        errors = macro_processor.validate_macros(script)
        assert len(errors) == 0  # Should be no errors for valid syntax
    
    def test_multiple_macros(self):
        """Test processing multiple macros in one script."""
        script = '''# for file in *.txt
echo "Text file: $file"

# for log in *.log
process_log() {
    echo "Log file: $1"
}'''
        
        result = macro_processor.process_macros(script)
        
        # Should have both transformations
        assert "for file in *.txt; do" in result
        assert "for log in *.log; do" in result
        assert 'process_log "$log"' in result

class TestMacroIntegration:
    """Test macro integration with the compilation pipeline."""
    
    def setup_method(self):
        """Reset macro processor state before each test."""
        macro_processor.set_variable_types({})
    
    def test_macro_with_file_type_annotation(self):
        """Test that macros work with file type annotations."""
        script = '''# INPUT_FILE (file): File to process
# OUTPUT_DIR (str): Output directory

# for line in $INPUT_FILE
echo "Processing: $line" > "$OUTPUT_DIR/processed.txt"'''
        
        # Simulate the type information that would come from annotations
        macro_processor.set_variable_types({'INPUT_FILE': 'file', 'OUTPUT_DIR': 'str'})
        
        result = macro_processor.process_macros(script)
        
        # Should still have variable annotations
        assert "# INPUT_FILE (file)" in result
        assert "# OUTPUT_DIR (str)" in result
        
        # Should have transformed macro to file_lines iteration
        assert "while IFS= read -r line; do" in result
        assert "done < $INPUT_FILE" in result