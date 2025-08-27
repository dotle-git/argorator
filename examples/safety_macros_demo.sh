#!/usr/bin/env argorator

# This script demonstrates Argorator's safety macros
# Safety macros provide bulletproof error handling and cleanup

# set strict
# trap cleanup

# INPUT_FILE (file): File to process (required)
# OUTPUT_DIR (str): Output directory (default: ./output)
# VERBOSE (bool): Enable verbose output (default: false)

echo "🛡️  Safety Macros Demo"
echo "===================="

# The safety macros above will generate:
# 1. set -eou --pipefail (strict mode)
# 2. A cleanup() function with trap handlers

echo "📁 Input file: $INPUT_FILE"
echo "📂 Output directory: $OUTPUT_DIR"

# Create output directory
if [ "$VERBOSE" = "true" ]; then
    echo "Creating output directory: $OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

# Create a temporary working directory
temp_dir=$(mktemp -d)
if [ "$VERBOSE" = "true" ]; then
    echo "Created temporary directory: $temp_dir"
fi

# The trap cleanup macro will automatically handle our temporary files
# trap cleanup
rm -rf "$temp_dir"
if [ "$VERBOSE" = "true" ]; then
    echo "🧹 Cleaned up temporary directory: $temp_dir" >&2
fi
echo "✨ Cleanup completed" >&2

# Process the input file
echo "📊 Processing file..."

# Count lines, words, and characters
line_count=$(wc -l < "$INPUT_FILE")
word_count=$(wc -w < "$INPUT_FILE")
char_count=$(wc -c < "$INPUT_FILE")

# Save statistics to temporary file
stats_file="$temp_dir/stats.txt"
cat > "$stats_file" << EOF
File Statistics for: $INPUT_FILE
================================
Lines: $line_count
Words: $word_count
Characters: $char_count
Processed: $(date)
EOF

# Copy to output directory
final_stats="$OUTPUT_DIR/$(basename "$INPUT_FILE").stats"
cp "$stats_file" "$final_stats"

echo "✅ Processing completed!"
echo "📈 Statistics saved to: $final_stats"

if [ "$VERBOSE" = "true" ]; then
    echo ""
    echo "📋 File Statistics:"
    cat "$final_stats"
fi

echo ""
echo "🎯 Demo completed successfully!"
echo "   Try interrupting the script (Ctrl+C) to see cleanup in action"
echo "   Try providing a non-existent file to see error handling"