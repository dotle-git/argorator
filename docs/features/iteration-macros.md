# Iteration Macros

**Transform Python-style loop comments into efficient bash loops automatically.**

Iteration macros let you write intuitive loop syntax in comments, which Argorator automatically converts into proper bash loops. No more wrestling with bash loop syntax - just write what you mean.

## Quick Start

```bash
#!/usr/bin/env argorator

# DATA_FILE (file): Input file to process

# for line in $DATA_FILE
echo "Processing: $line"
```

Becomes:
```bash
while IFS= read -r line; do
    echo "Processing: $line"
done < $DATA_FILE
```

## Syntax Reference

### Basic Format
```
# for ITERATOR in SOURCE [as TYPE] [sep|separated by SEPARATOR] [| with PARAMS]
```

- **ITERATOR**: Variable name for each item (must be valid bash variable)
- **SOURCE**: What to iterate over (variable, pattern, range)
- **TYPE**: Optional type override (`file`, `array`, `pattern`, `range`, `directory`)
- **SEPARATOR**: For delimited strings (`sep ,` or `separated by ":"`)
- **PARAMS**: Additional parameters for function calls

### Supported Iteration Types

#### 1. File Line Iteration
Iterate through each line in a file:

```bash
# Input file annotation triggers automatic file iteration
# LOG_FILE (file): Application log file

# for line in $LOG_FILE
echo "Log entry: $line"
```

Or force any variable to be treated as a file:
```bash
# for line in $DATA as file
echo "Line: $line"
```

#### 2. Pattern Iteration
Iterate over files matching a pattern:

```bash
# for file in *.txt
echo "Processing: $file"

# for backup in backup_*.sql
echo "Found backup: $backup"
```

#### 3. Range Iteration
Numeric ranges:

```bash
# for i in {1..10}
echo "Number: $i"

# for count in {0..100..5}  # 0, 5, 10, ..., 100
echo "Count: $count"
```

#### 4. Array Iteration
Space-separated values:

```bash
# SERVERS (str): Space-separated server list

# for server in $SERVERS
ping -c 1 "$server"
```

#### 5. Directory Iteration
Iterate over directories:

```bash
# for dir in */
echo "Directory: $dir"

# for subdir in backup/*/
echo "Backup dir: $subdir"
```

#### 6. Delimited String Iteration
Handle CSV, colon-separated paths, and custom delimiters:

```bash
# CSV data
# for item in $CSV_DATA sep ,
echo "CSV item: $item"

# PATH-style variables
# for path in $PATH separated by :
echo "Path: $path"

# Custom separators
# for field in $DATA separated by "::"
echo "Field: $field"

# Multi-character with escapes
# for line in $TEXT separated by "\\n"
echo "Line: $line"
```

## Function Integration

### Function Target
When a macro precedes a function definition, it generates a loop that calls the function:

```bash
# for file in *.log
process_log() {
    echo "Processing: $1"
    grep "ERROR" "$1" > "$1.errors"
    echo "Found $(wc -l < "$1.errors") errors"
}
```

Generates:
```bash
process_log() {
    echo "Processing: $1"
    grep "ERROR" "$1" > "$1.errors"
    echo "Found $(wc -l < "$1.errors") errors"
}

for file in *.log; do
    process_log "$file"
done
```

### Additional Parameters
Pass extra parameters to functions:

```bash
# for file in *.txt | with $OUTPUT_DIR $VERBOSE
convert_file() {
    local input="$1"
    local output_dir="$2"
    local verbose="$3"
    
    if [ "$verbose" = "true" ]; then
        echo "Converting $input to $output_dir"
    fi
    
    cp "$input" "$output_dir/"
}
```

## Type System Integration

### Automatic Type Detection
Argorator automatically determines iteration type from argument annotations:

```bash
# INPUT_FILE (file): Input file  
# CSV_DATA (str): CSV string
# FILE_LIST (str): Space-separated files

# Automatically uses file line iteration
# for line in $INPUT_FILE  

# Uses array iteration
# for item in $CSV_DATA

# Uses array iteration  
# for file in $FILE_LIST
```

### Type Override
Force specific iteration behavior:

```bash
# Force string to be treated as file
# for line in $CONFIG_STRING as file

# Force file to be treated as array
# for word in $TEXT_FILE as array
```

## Advanced Examples

### Log Analysis
```bash
#!/usr/bin/env argorator

# LOG_FILE (file): Application log to analyze
# ERROR_CODES (str): Comma-separated error codes to find

# for line in $LOG_FILE
    if echo "$line" | grep -q "ERROR"; then
        echo "Error found: $line"
    fi

echo "--- Specific Error Analysis ---"

# for code in $ERROR_CODES sep ,
    echo "Searching for error code: $code"
    grep "ERROR.*$code" "$LOG_FILE" || echo "No instances of $code found"
```

### Batch File Processing
```bash
#!/usr/bin/env argorator

# INPUT_DIR (str): Directory containing files to process
# OUTPUT_DIR (str): Output directory

# for file in $INPUT_DIR/*.jpg
process_image() {
    local input="$1"
    local output="$2"
    local filename=$(basename "$input")
    
    echo "Processing: $filename"
    convert "$input" -resize 800x600 "$output/thumb_$filename"
    echo "Saved: $output/thumb_$filename"
}
```

### CSV Data Processing
```bash
#!/usr/bin/env argorator

# CSV_FILE (file): CSV file to process 
# COLUMNS (str): Comma-separated column names

echo "Processing CSV data..."

# Read header
# for header in $COLUMNS sep ,
echo "Column: $header"

echo "Processing rows..."

# Process each row
# for row in $CSV_FILE
    echo "Row data: $row"
    
    # Split row into fields  
    # for field in $row sep ,
    echo "  Field: $field"
```

## Error Handling and Limitations

### Unsupported Scenarios

#### Multiple Macros on Same Line
```bash
# ❌ NOT SUPPORTED
# for file in *.txt
# for line in $file as file  
echo "Processing $file: $line"
```

**Error**: Clear message with workarounds:
- Use separate lines
- Use function-based approach
- Combine into single pattern if possible

#### Function with Internal Macros
```bash
# ❌ NOT SUPPORTED  
# for file in *.log
process_file() {
    # for line in $1 as file  # Conflicts with function macro
    echo "Line: $line"
}
```

**Error**: Helpful alternatives provided:
- Remove function-level macro
- Remove internal macros
- Use sequential approach

### Validation

Argorator validates:
- Variable names (must be valid bash identifiers)
- Macro syntax (proper format required)
- Target conflicts (multiple macros → same line)
- Function conflicts (function + internal macros)

Invalid syntax gets helpful error messages with examples and fixes.

## Generated Bash Patterns

### File Lines (`file` type or `as file`)
```bash
while IFS= read -r ITERATOR; do
    # your code
done < SOURCE
```

### Delimited Strings (single character)
```bash
IFS='SEPARATOR' read -ra TEMP_ARRAY <<< SOURCE
for ITERATOR in "${TEMP_ARRAY[@]}"; do
    # your code  
done
```

### Delimited Strings (multi-character)
```bash
TEMP_ARRAY=()
IFS=$'\n' read -d '' -ra TEMP_ARRAY < <(echo SOURCE | sed 's/SEPARATOR/\n/g' && printf '\0')
for ITERATOR in "${TEMP_ARRAY[@]}"; do
    # your code
done
```

### Regular Patterns/Arrays/Ranges
```bash
for ITERATOR in SOURCE; do
    # your code
done
```

## Performance Notes

- **File iteration**: Uses efficient `while read` with proper IFS handling
- **Delimited parsing**: Optimized for single vs multi-character separators
- **Memory usage**: Large arrays are handled efficiently 
- **Error handling**: Preserves exit codes and error propagation

## Best Practices

1. **Use type annotations** for clear iteration behavior
2. **Prefer explicit separators** for delimited data
3. **Use functions** for complex processing logic
4. **Test with edge cases** like empty files or special characters
5. **Keep macros simple** - one concept per macro
6. **Use meaningful variable names** for clarity

## Migration from Manual Loops

### Before (Manual)
```bash
while IFS= read -r line; do
    echo "Processing: $line"
done < "$INPUT_FILE"
```

### After (Macro)
```bash
# INPUT_FILE (file): Input file to process

# for line in $INPUT_FILE
echo "Processing: $line"
```

The macro version is:
- **Shorter** and more readable
- **Type-safe** with validation
- **Consistent** across your scripts
- **Self-documenting** with clear intent