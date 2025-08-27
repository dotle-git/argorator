#!/usr/bin/env python3

import sys
sys.path.insert(0, '/workspace/src')

from argorator.macros.processor import macro_processor

def test_edge_case_1_nested_loops():
    """Test multiple iteration annotations for a single line."""
    print("=== EDGE CASE 1: Nested loops ===")
    script = '''# for file in *.txt
# for line in $file as file  
echo "Processing $file: $line"'''
    
    try:
        result = macro_processor.process_macros(script)
        print("RESULT:")
        print(result)
        print("SUCCESS: Nested loops processed")
    except Exception as e:
        print(f"FAILED: {e}")
    print()

def test_edge_case_2_function_with_internal_macros():
    """Test function with iteration annotation + internal iteration."""
    print("=== EDGE CASE 2: Function with internal macros ===")
    script = '''# for file in *.log
process_file() {
    echo "Processing file: $1"
    # for line in $1 as file
    echo "Line: $line"
}'''
    
    try:
        result = macro_processor.process_macros(script)
        print("RESULT:")
        print(result)
        print("SUCCESS: Function with internal macros processed")
    except Exception as e:
        print(f"FAILED: {e}")
    print()

def test_edge_case_3_macro_in_if_block():
    """Test iteration annotation within if block."""
    print("=== EDGE CASE 3: Macro in if block ===")
    script = '''if [ "$ENABLE_PROCESSING" = "true" ]; then
    # for item in $LIST sep ,
    echo "Processing: $item"
fi'''
    
    try:
        result = macro_processor.process_macros(script)
        print("RESULT:")
        print(result)
        print("SUCCESS: Macro in if block processed")
    except Exception as e:
        print(f"FAILED: {e}")
    print()

def test_edge_case_4_macro_in_existing_loop():
    """Test iteration annotation within existing loop."""
    print("=== EDGE CASE 4: Macro in existing loop ===")
    script = '''for dir in */; do
    echo "Processing directory: $dir"
    # for file in $dir/*.txt
    echo "Found: $file"
done'''
    
    try:
        result = macro_processor.process_macros(script)
        print("RESULT:")
        print(result)
        print("SUCCESS: Macro in existing loop processed")
    except Exception as e:
        print(f"FAILED: {e}")
    print()

if __name__ == "__main__":
    test_edge_case_1_nested_loops()
    test_edge_case_2_function_with_internal_macros()
    test_edge_case_3_macro_in_if_block()
    test_edge_case_4_macro_in_existing_loop()