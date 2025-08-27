#!/usr/bin/env argorator

# LOGFILE (file): Input log file to process
# OUTDIR (str): Directory for output files

echo "=== Type-Based Iteration Macros ==="

# Type-based: LOGFILE is 'file' type so automatically uses file_lines iteration
# for line in $LOGFILE
echo "Log line: $line" | tee -a "$OUTDIR/processed.log"

echo "---"

# Explicit override: force string variable to be treated as file
# for record in $OUTDIR as file  
process_record() {
    echo "Processing record: $1"
}

echo "Demo complete!"