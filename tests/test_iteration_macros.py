"""Tests for iteration macro functionality."""
import pytest
from argorator.macros.processor import macro_processor
from argorator.macros.parser import macro_parser

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

class TestDelimitedIteration:
    """Test delimited string iteration macros."""
    
    def setup_method(self):
        """Reset macro processor state before each test."""
        macro_processor.set_variable_types({})
    
    def test_comma_separated_short_syntax(self):
        """Test comma-separated iteration with short 'sep' syntax."""
        script = '''# for item in $CSV_DATA sep ,
echo "Item: $item"'''
        
        result = macro_processor.process_macros(script)
        
        assert "IFS=',' read -ra ARGORATOR_ARRAY_" in result
        assert "for item in" in result
        assert "echo \"Item: $item\"" in result
        assert "done" in result
    
    def test_colon_separated_long_syntax(self):
        """Test colon-separated iteration with 'separated by' syntax."""
        script = '''# for field in $PATH separated by :
echo "Path: $field"'''
        
        result = macro_processor.process_macros(script)
        
        assert "IFS=':' read -ra ARGORATOR_ARRAY_" in result
        assert "for field in" in result
        assert "echo \"Path: $field\"" in result
        assert "done" in result
    
    def test_quoted_separator(self):
        """Test separator with quotes."""
        script = '''# for item in $DATA separated by ","
echo "Item: $item"'''
        
        result = macro_processor.process_macros(script)
        
        assert "IFS=',' read -ra ARGORATOR_ARRAY_" in result
        assert "for item in" in result
        assert "done" in result
    
    def test_multi_character_separator(self):
        """Test multi-character separator."""
        script = '''# for part in $TEXT separated by "::"
echo "Part: $part"'''
        
        result = macro_processor.process_macros(script)
        
        # Multi-char separators use sed-based approach
        assert "sed 's/::/\\n/g'" in result
        assert "for part in" in result
        assert "echo \"Part: $part\"" in result
        assert "done" in result
    
    def test_escaped_separator(self):
        """Test separator with escape sequences."""
        script = '''# for line in $DATA separated by "\\n"
echo "Line: $line"'''
        
        result = macro_processor.process_macros(script)
        
        # Should handle newline separator properly
        assert "for line in" in result
        assert "echo \"Line: $line\"" in result
        assert "done" in result
    
    def test_function_with_delimiter(self):
        """Test delimited iteration with function target."""
        script = '''# for item in $LIST sep |
process_item() {
    echo "Processing: $1"
    echo "Item processed"
}'''
        
        result = macro_processor.process_macros(script)
        
        # Should contain function definition
        assert "process_item() {" in result
        
        # Should contain delimited loop calling function
        assert "IFS='|' read -ra ARGORATOR_ARRAY_" in result
        assert 'process_item "$item"' in result
        assert "done" in result
    
    def test_space_separator(self):
        """Test space as separator."""
        script = '''# for word in $SENTENCE sep " "
echo "Word: $word"'''
        
        result = macro_processor.process_macros(script)
        
        assert "IFS=' ' read -ra ARGORATOR_ARRAY_" in result
        assert "for word in" in result
        assert "done" in result
    
    def test_tab_separator(self):
        """Test tab separator with escape sequence."""
        script = '''# for field in $TSV_ROW separated by "\\t"
echo "Field: $field"'''
        
        result = macro_processor.process_macros(script)
        
        # Should handle tab character properly
        assert "for field in" in result
        assert "echo \"Field: $field\"" in result
        assert "done" in result
    
    def test_delimiter_with_additional_params(self):
        """Test delimited iteration with additional parameters."""
        script = '''# for item in $CSV sep , | with $OUTPUT_FILE
write_item() {
    local item="$1"
    local output="$2"
    echo "$item" >> "$output"
}'''
        
        result = macro_processor.process_macros(script)
        
        assert "IFS=',' read -ra ARGORATOR_ARRAY_" in result
        assert 'write_item "$item" "$OUTPUT_FILE"' in result
        assert "done" in result

class TestEdgeCasesAndValidation:
    """Test edge cases and validation scenarios."""
    
    def setup_method(self):
        """Reset macro processor state before each test."""
        macro_processor.set_variable_types({})
    
    def test_multiple_macros_same_line_conflict(self):
        """Test that multiple macros targeting the same line are detected as conflicts."""
        script = '''# for file in *.txt
# for line in $file as file  
echo "Processing $file: $line"'''
        
        errors = macro_processor.validate_macros(script)
        # Should detect the conflict during processing
        try:
            result = macro_processor.process_macros(script)
            assert False, "Should have raised ValueError for conflicting macros"
        except ValueError as e:
            assert "Multiple iteration macros target the same line" in str(e)
    
    def test_function_macro_with_internal_macro_conflict(self):
        """Test that function macros with internal macros are detected as conflicts."""
        script = '''# for file in *.log
process_file() {
    echo "Processing file: $1"
    # for line in $1 as file
    echo "Line: $line"
}'''
        
        try:
            result = macro_processor.process_macros(script)
            assert False, "Should have raised ValueError for function macro conflict"
        except ValueError as e:
            assert "UNSUPPORTED: Function macro with internal iteration macros" in str(e)
    
    def test_macro_in_if_block_allowed(self):
        """Test that macros within if blocks are allowed and work correctly."""
        script = '''if [ "$ENABLE_PROCESSING" = "true" ]; then
    # for item in $LIST sep ,
    echo "Processing: $item"
fi'''
        
        result = macro_processor.process_macros(script)
        
        # Should work correctly
        assert "if [" in result
        assert "IFS=',' read -ra ARGORATOR_ARRAY_" in result
        assert "for item in" in result
        assert "fi" in result
    
    def test_macro_in_existing_loop_allowed(self):
        """Test that macros within existing loops are allowed and work correctly."""
        script = '''for dir in */; do
    echo "Processing directory: $dir"
    # for file in $dir/*.txt
    echo "Found: $file"
done'''
        
        result = macro_processor.process_macros(script)
        
        # Should create properly nested loops
        assert "for dir in */" in result
        assert "for file in $dir/*.txt" in result
        assert result.count("done") == 2  # Two "done" statements for nested loops
    
    def test_valid_sequential_macros(self):
        """Test that macros on separate lines work correctly."""
        script = '''# for file in *.txt
echo "Processing file: $file"

# for line in $ANOTHER_FILE as file
echo "Processing line: $line"'''
        
        result = macro_processor.process_macros(script)
        
        # Should create two separate loops
        assert "for file in *.txt" in result
        assert "while IFS= read -r line" in result
        assert result.count("done") == 2
    
    def test_function_macro_without_internal_macros_allowed(self):
        """Test that function macros without internal macros work correctly."""
        script = '''# for file in *.log
process_file() {
    echo "Processing file: $1"
    grep "ERROR" "$1" > "$1.errors"
}'''
        
        result = macro_processor.process_macros(script)
        
        # Should contain function definition and external loop
        assert "process_file() {" in result
        assert "for file in *.log" in result
        assert 'process_file "$file"' in result
        assert "done" in result
    
    def test_malformed_macro_validation(self):
        """Test validation catches malformed macros."""
        script = '''# for 123invalid in source
echo "test"'''
        
        errors = macro_processor.validate_macros(script)
        assert len(errors) > 0
        assert "INVALID MACRO SYNTAX" in errors[0]
        assert "CORRECT SYNTAX EXAMPLES" in errors[0]
    
    def test_mixed_supported_scenarios(self):
        """Test complex but supported combinations of macros."""
        script = '''# Process individual files
# for file in *.txt
echo "Text file: $file"

# Process CSV data
# for item in $CSV_DATA sep ,
echo "CSV item: $item"

# Function-based processing (no internal macros)
# for log in *.log
analyze_log() {
    echo "Analyzing: $1"
    wc -l "$1"
}'''
        
        result = macro_processor.process_macros(script)
        
        # Should process all three macros successfully
        assert "for file in *.txt" in result
        assert "IFS=',' read -ra ARGORATOR_ARRAY_" in result
        assert "for log in *.log" in result
        assert 'analyze_log "$log"' in result
        assert result.count("done") >= 3