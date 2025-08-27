# Argument Type System

Argorator provides a comprehensive and extensible argument type system that allows you to specify the data type for each argument in your shell scripts. This system has been redesigned in v0.6.0 to use an object-oriented approach with extensible type classes.

## Supported Types

### Basic Types

#### String Types
- **Type names**: `str`, `string`, `text`
- **Description**: Text values (default type)
- **Example**: 
  ```bash
  # NAME (str): User's full name
  ```

#### Integer Types  
- **Type names**: `int`, `integer`, `number`
- **Description**: Whole numbers
- **Example**:
  ```bash
  # COUNT (int): Number of items to process
  ```

#### Float Types
- **Type names**: `float`, `decimal`, `real`
- **Description**: Decimal numbers
- **Example**:
  ```bash
  # RATE (float): Processing rate in items per second
  ```

#### Boolean Types
- **Type names**: `bool`, `boolean`, `flag`
- **Description**: True/false flags (creates store_true arguments)
- **Example**:
  ```bash
  # VERBOSE (bool): Enable verbose output
  ```

#### Choice Types
- **Type names**: `choice`, `enum`, `select`, `option`
- **Description**: Must be one of the specified choices
- **Example**:
  ```bash
  # MODE (choice[fast, slow, auto]): Processing mode
  ```

#### File Types
- **Type names**: `file`, `path`, `filepath`
- **Description**: File or directory paths
- **Example**:
  ```bash
  # CONFIG_FILE (file): Path to configuration file
  ```

## Type Validation

The type system provides comprehensive validation:

- **Type validation**: Ensures specified types are supported
- **Value validation**: Validates that provided values match the expected type
- **Choice validation**: For choice types, ensures values are from the allowed set
- **Format validation**: For file types, ensures valid path format

## Backward Compatibility

All existing type names from previous versions continue to work:
- `str`, `int`, `float`, `bool`, `choice`, `file`

The new system is fully backward compatible with existing scripts and annotations.

## Advanced Features

### Type Aliases
Multiple type names can refer to the same underlying type:
```bash
# AGE (integer): User's age        # same as 'int'
# SCORE (decimal): Test score      # same as 'float'  
# ENABLED (flag): Enable feature   # same as 'bool'
```

### Automatic Type Conversion
When you provide choices without specifying a type, it automatically becomes a choice type:
```bash
# MODE [fast, slow]: Processing mode
# Automatically treated as: MODE (choice[fast, slow]): Processing mode
```

### Custom Validation
Each type can implement custom validation logic. For example:
- Integer types ensure values can be converted to integers
- Float types ensure values can be converted to floats
- Boolean types accept various formats: `true/false`, `yes/no`, `1/0`, `on/off`
- Choice types ensure values are in the allowed choices
- File types ensure valid path format

## Implementation Details

The type system is built on an extensible architecture:

### BaseArgumentType
All argument types inherit from `BaseArgumentType`, which defines:
- Type names/aliases the handler supports
- Value validation logic
- Argparse integration configuration

### Type Registry
A central registry maps type names to their handlers, allowing:
- Case-insensitive type lookup
- Multiple aliases per type
- Easy extensibility for custom types

### Integration Points
The type system integrates with:
- **Annotation parsing**: Dynamic regex generation from supported types
- **Argparse configuration**: Each type knows how to configure argparse
- **Value conversion**: Type-specific conversion and validation
- **Error handling**: Clear error messages for invalid types or values

## Examples

### Basic Usage
```bash
#!/bin/bash
# DESCRIPTION: Process files with various options

# INPUT_FILE (file): Path to input file
# OUTPUT_DIR (path): Directory for output files  
# COUNT (integer): Number of items to process
# RATE (decimal): Processing rate
# MODE (choice[fast, slow, auto]): Processing mode
# VERBOSE (boolean): Enable verbose output
# DRY_RUN (flag): Show what would be done without executing

echo "Processing $INPUT_FILE..."
echo "Output directory: $OUTPUT_DIR"
echo "Count: $COUNT, Rate: $RATE"
echo "Mode: $MODE"
[[ "$VERBOSE" == "true" ]] && echo "Verbose mode enabled"
[[ "$DRY_RUN" == "true" ]] && echo "Dry run mode"
```

### Advanced Usage with Aliases
```bash
#!/bin/bash
# Server configuration script

# HOST (string): Server hostname
# PORT (number): Server port number  
# TIMEOUT (real): Connection timeout in seconds
# PROTOCOL (enum[http, https, ftp]): Connection protocol
# ENABLE_SSL (boolean): Enable SSL/TLS encryption
# LOG_LEVEL (select[debug, info, warn, error]): Logging level
```

This new type system provides a solid foundation for extending Argorator with additional argument types in the future while maintaining full backward compatibility with existing scripts.