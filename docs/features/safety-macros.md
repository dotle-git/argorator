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

Adds automatic cleanup handling on script exit or error by wrapping the target line/block in a trap handler:

```bash
#!/usr/bin/env argorator

# trap cleanup
rm -f "$temp_file"
echo "Cleanup completed"

echo "Starting processing..."
temp_file=$(mktemp)
echo "Created temp file: $temp_file"
```

**Generated code:**
```bash
# Trap cleanup handler
_cleanup_line_2() {
    local exit_code=$?
    rm -f "$temp_file"
    echo "Cleanup completed"
    exit $exit_code
}

trap _cleanup_line_2 EXIT ERR INT TERM

echo "Starting processing..."
temp_file=$(mktemp)
echo "Created temp file: $temp_file"
```

**What it does:**
- Takes the line/block after the comment as cleanup code
- Wraps that code in a trap handler function
- Traps EXIT, ERR, INT, and TERM signals by default
- Preserves the original exit code
- Removes the original target line (it's now in the trap handler)

**Custom signals:**
You can specify which signals to trap:

```bash
#!/usr/bin/env argorator

# trap cleanup EXIT,INT,TERM
echo "Custom cleanup for specific signals"
```

## Combining Safety Macros

You can use multiple safety macros together:

```bash
#!/usr/bin/env argorator

# set strict
# trap cleanup
rm -rf "$WORK_DIR"
echo "Removed working directory"

echo "Ultra-safe script processing $INPUT_FILE"
WORK_DIR=$(mktemp -d)
echo "Working in: $WORK_DIR"
```

**Generated code:**
```bash
set -eou --pipefail

# Trap cleanup handler
_cleanup_line_3() {
    local exit_code=$?
    rm -rf "$WORK_DIR"
    echo "Removed working directory"
    exit $exit_code
}

trap _cleanup_line_3 EXIT ERR INT TERM

echo "Ultra-safe script processing $INPUT_FILE"
WORK_DIR=$(mktemp -d)
echo "Working in: $WORK_DIR"
```

## Macro Placement

- **`# set strict`** is always placed at the beginning of the script (after the shebang)
- **`# trap cleanup`** applies to the line or block immediately following the comment

```bash
#!/usr/bin/env argorator

echo "Starting..."

# set strict  # <-- This will be moved to the top

echo "Processing..."

# trap cleanup  # <-- This applies to the next line
rm -f /tmp/workfile

echo "Done!"
```

**Generated code:**
```bash
#!/usr/bin/env argorator

set -eou --pipefail

echo "Starting..."

echo "Processing..."

# Trap cleanup handler
_cleanup_line_7() {
    local exit_code=$?
    rm -f /tmp/workfile
    exit $exit_code
}

trap _cleanup_line_7 EXIT ERR INT TERM

echo "Done!"
```

## Use Cases

### File Processing with Cleanup

```bash
#!/usr/bin/env argorator

# set strict

# LOGFILE (file): Log file to process

echo "Analyzing log file: $LOGFILE"
temp_dir=$(mktemp -d)
echo "Working directory: $temp_dir"

grep "ERROR" "$LOGFILE" > "$temp_dir/errors.txt"
grep "WARN" "$LOGFILE" > "$temp_dir/warnings.txt"

echo "Found $(wc -l < "$temp_dir/errors.txt") errors"
echo "Found $(wc -l < "$temp_dir/warnings.txt") warnings"

# trap cleanup
rm -rf "$temp_dir"
echo "Cleaned up temporary files"
```

**Generated code includes:**
- `set -eou --pipefail` at the top
- A trap handler that removes `$temp_dir` and logs cleanup
- Trap set to run on EXIT, ERR, INT, TERM

### Database Operations

```bash
#!/usr/bin/env argorator

# set strict

# DATABASE_URL (str): Database connection string
# BACKUP_FILE (str): Output backup file

echo "Starting database backup..."
lock_file="/tmp/backup.lock"
touch "$lock_file"

pg_dump "$DATABASE_URL" > "$BACKUP_FILE"
echo "Backup completed: $BACKUP_FILE"

# trap cleanup
rm -f "$lock_file"
echo "Cleaned up lock file"
```

**What this generates:**
- Strict mode for immediate error detection
- A trap handler that removes the lock file on any exit condition
- Automatic cleanup even if the backup fails or is interrupted

## Best Practices

1. **Always use `# set strict`** for production scripts to catch errors early
2. **Use `# trap cleanup`** when working with temporary files or resources that need cleanup
3. **Put cleanup code immediately after the trap comment** - this becomes your cleanup handler
4. **Use specific cleanup actions** rather than generic ones for better reliability
5. **Test error conditions** to ensure your cleanup logic works correctly
6. **Specify custom signals** when you only need to trap specific conditions (e.g., `EXIT,INT`)

## Error Scenarios

With safety macros, your scripts will automatically handle common error scenarios:

- **Command failures:** Script exits immediately with proper error code
- **Undefined variables:** Script exits before causing damage
- **Pipeline failures:** Script detects when intermediate commands fail
- **Interruption:** Cleanup runs even if user presses Ctrl+C
- **System errors:** Cleanup runs on unexpected termination

## Implementation Notes

- `# set strict` macros are processed at script beginning, before all other code
- `# trap cleanup` macros are processed like iteration macros, replacing their target
- Multiple safety macros are allowed - each trap macro creates its own handler
- Trap macros require a target line or function immediately following the comment
- Function targets: the function body becomes the cleanup code
- Line targets: the line content becomes the cleanup code
- Safety macros work with all other Argorator features (annotations, iteration macros, etc.)

## Signal Reference

Valid signals for `# trap cleanup` macros:
- `EXIT` - Script exit (normal or error)
- `ERR` - Command failure (when using `set -e`)
- `INT` - Interrupt signal (Ctrl+C)
- `TERM` - Termination signal
- `HUP` - Hang up signal
- `QUIT` - Quit signal
- `USR1`, `USR2` - User-defined signals
- `PIPE` - Broken pipe
- `ALRM` - Alarm signal

Default signals: `EXIT ERR INT TERM`

## Version Information

Safety macros are available starting in Argorator version 0.6.0.