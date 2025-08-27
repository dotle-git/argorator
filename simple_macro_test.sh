#!/usr/bin/env argorator

# OUTPUT_DIR (str): Output directory

# for file in *.txt
process_file() {
    echo "Processing file: $1"
    echo "Output dir: $OUTPUT_DIR"
    cp "$1" "$OUTPUT_DIR/" 2>/dev/null || echo "Copy failed, but that's OK for demo"
}

echo "Demo complete!"