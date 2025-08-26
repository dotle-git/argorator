# Argorator Docstring-Style Annotations

Argorator now supports Python docstring-style annotations in shell script comments to provide type information and help text for your script arguments.

## Basic Usage

Add special comments to your shell script to annotate variables:

```bash
#!/bin/bash
# :param NAME: Your name
# :param int AGE: Your age in years
# :param bool VERBOSE: Enable verbose output

echo "Hello $NAME, you are $AGE years old"
if [ "$VERBOSE" = "true" ]; then
    echo "Running in verbose mode"
fi
```

## Annotation Formats

### 1. Basic Parameter with Description

```bash
# :param VARIABLE_NAME: Description of the parameter
```

### 2. Parameter with Type

You can specify the type either inline or separately:

```bash
# Inline type specification
# :param type VARIABLE_NAME: Description

# Separate type specification
# :param VARIABLE_NAME: Description
# :type VARIABLE_NAME: type
```

### 3. Choice Parameters

For parameters with a fixed set of allowed values:

```bash
# :param ENVIRONMENT: Target environment
# :type ENVIRONMENT: choice
# :choices ENVIRONMENT: dev, staging, prod
```

## Supported Types

- `str` (or `string`) - String values (default if no type specified)
- `int` - Integer values
- `float` - Floating-point numbers
- `bool` - Boolean values (accepts: true/false, 1/0, yes/no, y/n)
- `choice` - String with restricted set of values

## Examples

### Example 1: Simple Script with Types

```bash
#!/bin/bash
# :param str NAME: User's name
# :param int COUNT: Number of items to process
# :param float THRESHOLD: Processing threshold
# :param bool DRY_RUN: Run without making changes

echo "Processing $COUNT items for $NAME"
echo "Threshold: $THRESHOLD"
if [ "$DRY_RUN" = "true" ]; then
    echo "DRY RUN - no changes will be made"
fi
```

### Example 2: Deployment Script with Choices

```bash
#!/bin/bash
# :param SERVICE: Service to deploy
# :type SERVICE: str

# :param ENVIRONMENT: Deployment environment
# :type ENVIRONMENT: choice
# :choices ENVIRONMENT: dev, staging, prod

# :param bool RESTART: Restart service after deployment

echo "Deploying $SERVICE to $ENVIRONMENT"
if [ "$RESTART" = "true" ]; then
    echo "Service will be restarted"
fi
```

### Example 3: Mixed Annotation Styles

```bash
#!/bin/bash
# Basic parameter
# :param PROJECT: Project name

# Inline type
# :param int PORT: Port number

# Separate declarations
# :param DATABASE: Database name
# :type DATABASE: str

# Choice with all declarations
# :param LOG_LEVEL: Logging level
# :type LOG_LEVEL: choice  
# :choices LOG_LEVEL: debug, info, warning, error

echo "Starting $PROJECT on port $PORT"
echo "Database: $DATABASE"
echo "Log level: $LOG_LEVEL"
```

## Benefits

1. **Type Safety**: Arguments are automatically converted to the correct type
2. **Input Validation**: Invalid types or choices are caught before script execution
3. **Better Help Text**: Generated help messages include your descriptions
4. **IDE Support**: Docstring format is familiar to Python developers
5. **Backward Compatible**: Scripts work normally when run directly with bash

## Running Annotated Scripts

```bash
# View generated help
argorator script.sh --help

# Run with arguments
argorator script.sh --name "Alice" --count 5 --threshold 0.8 --dry-run true

# Using shebang
#!/usr/bin/env argorator
./script.sh --name "Alice" --count 5
```