#!/usr/bin/env argorator

# FILE (str): Input file to process
# OUTPUT_DIR (str): Directory for output files

# for line in $FILE
echo "Processing line: $line"

echo "---"

# for file in *.txt
process_file() {
    echo "Processing file: $1"
    cp "$1" "$OUTPUT_DIR/"
    echo "Copied $1 to $OUTPUT_DIR/"
}

echo "Macro processing complete!"