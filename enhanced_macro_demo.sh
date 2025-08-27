#!/usr/bin/env argorator

# LOG_FILE (file): Input log file to process
# OUTPUT_DIR (str): Directory for output files  
# PATTERN (str): Search pattern

echo "=== Type-Based Iteration Macro Demo ==="

# This will automatically use file_lines iteration because LOG_FILE is type 'file'
# for line in $LOG_FILE
echo "Processing log line: $line"

echo "---"

# Explicit type override - force any variable to be treated as file
# for entry in $PATTERN as file
read_file_entry() {
    echo "Reading file entry: $1"
    echo "Output dir: $OUTPUT_DIR"
}

echo "---"

# Pattern iteration (still works as before)
# for txtfile in *.txt
echo "Found text file: $txtfile"

echo "---"

# Range iteration
# for i in {1..3}
echo "Count: $i"

echo "Type-based macro demo complete!"