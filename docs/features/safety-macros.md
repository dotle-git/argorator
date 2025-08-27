# Safety Macros

Safety macros provide an easy way to add robust error handling and cleanup functionality to your bash scripts through simple comment annotations.

## Overview

Safety macros automatically inject standard bash safety patterns into your scripts, eliminating the need to remember complex bash syntax for error handling and cleanup.

## Available Safety Macros

### `# set strict`

Enables bash strict mode with comprehensive error handling:

```bash
#!/usr/bin/env argorator

# set strict

echo "Processing $FILE"
cp "$FILE" backup.txt
```

**Generated code:**
```bash
set -eou --pipefail

echo "Processing $FILE"
cp "$FILE" backup.txt
```

**What it does:**
- `set -e`: Exit immediately if any command fails
- `set -u`: Exit immediately if undefined variables are used
- `set -o pipefail`: Exit if any command in a pipeline fails

### `# trap cleanup`

Adds automatic cleanup handling on script exit or error:

```bash
#!/usr/bin/env argorator

# trap cleanup

echo "Starting processing..."
temp_file=$(mktemp)
echo "Created temp file: $temp_file"
```

**Generated code:**
```bash
# Cleanup trap handler
cleanup() {
    local exit_code=$?
    echo "Cleaning up..." >&2
    # Add your cleanup code here
    exit $exit_code
}

trap cleanup EXIT ERR INT TERM

echo "Starting processing..."
temp_file=$(mktemp)
echo "Created temp file: $temp_file"
```

**What it does:**
- Defines a `cleanup()` function that runs on script exit
- Traps EXIT, ERR, INT, and TERM signals
- Preserves the original exit code
- Provides a standard place to add cleanup logic

## Combining Safety Macros

You can use multiple safety macros together:

```bash
#!/usr/bin/env argorator

# set strict
# trap cleanup

echo "Ultra-safe script processing $INPUT_FILE"
```

**Generated code:**
```bash
set -eou --pipefail

# Cleanup trap handler
cleanup() {
    local exit_code=$?
    echo "Cleaning up..." >&2
    # Add your cleanup code here
    exit $exit_code
}

trap cleanup EXIT ERR INT TERM

echo "Ultra-safe script processing $INPUT_FILE"
```

## Macro Placement

Safety macros are always placed at the beginning of the script (after the shebang if present), regardless of where the comment appears in your source file:

```bash
#!/usr/bin/env argorator

echo "Starting..."

# set strict  # <-- This will be moved to the top

echo "Processing..."

# trap cleanup  # <-- This will also be moved to the top

echo "Done!"
```

## Use Cases

### File Processing with Cleanup

```bash
#!/usr/bin/env argorator

# set strict
# trap cleanup

# LOGFILE (file): Log file to process

echo "Analyzing log file: $LOGFILE"
temp_dir=$(mktemp -d)
echo "Working directory: $temp_dir"

# Customize the cleanup function
cleanup() {
    local exit_code=$?
    echo "Cleaning up temporary files..." >&2
    rm -rf "$temp_dir"
    exit $exit_code
}

grep "ERROR" "$LOGFILE" > "$temp_dir/errors.txt"
grep "WARN" "$LOGFILE" > "$temp_dir/warnings.txt"

echo "Found $(wc -l < "$temp_dir/errors.txt") errors"
echo "Found $(wc -l < "$temp_dir/warnings.txt") warnings"
```

### Database Operations

```bash
#!/usr/bin/env argorator

# set strict
# trap cleanup

# DATABASE_URL (str): Database connection string
# BACKUP_FILE (str): Output backup file

echo "Starting database backup..."

# Customize cleanup for database operations
cleanup() {
    local exit_code=$?
    echo "Cleaning up database connections..." >&2
    # Close any open connections
    # Remove temporary files
    exit $exit_code
}

pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
echo "Backup completed: $BACKUP_FILE"
```

## Best Practices

1. **Always use `# set strict`** for production scripts to catch errors early
2. **Combine with `# trap cleanup`** when working with temporary files or resources
3. **Customize the cleanup function** by redefining it after the macro
4. **Place safety macros early** in your script for clarity (they'll be moved to the top anyway)
5. **Test error conditions** to ensure your cleanup logic works correctly

## Error Scenarios

With safety macros, your scripts will automatically handle common error scenarios:

- **Command failures:** Script exits immediately with proper error code
- **Undefined variables:** Script exits before causing damage
- **Pipeline failures:** Script detects when intermediate commands fail
- **Interruption:** Cleanup runs even if user presses Ctrl+C
- **System errors:** Cleanup runs on unexpected termination

## Implementation Notes

- Safety macros are processed before iteration macros
- Multiple safety macros of the same type are allowed (later ones override earlier ones)
- The generated cleanup function can be customized by redefining it in your script
- Safety macros work with all other Argorator features (annotations, iteration macros, etc.)

## Version Information

Safety macros are available starting in Argorator version 0.6.0.