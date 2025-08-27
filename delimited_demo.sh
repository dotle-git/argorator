#!/usr/bin/env argorator

# CSV_DATA (str): Comma-separated values to process
# PATH_VAR (str): Colon-separated paths

echo "=== Delimited Iteration Macros Demo ==="

# CSV processing with short syntax
# for item in $CSV_DATA sep ,
echo "CSV item: $item"

echo "---"

# Path processing with readable syntax  
# for path in $PATH_VAR separated by :
echo "Path: $path"

echo "---"

# Multi-character separator
# for part in $CSV_DATA separated by "::"
echo "Part: $part"

echo "---"

# Function with delimiter and additional params
# for record in $CSV_DATA sep , | with $OUTPUT_DIR
process_record() {
    echo "Processing record: $1"
    echo "Output to: $2"
}

echo "Delimited iteration demo complete!"