---
layout: page
title: Argument Groups
permalink: /features/argument-groups/
parent: Features
nav_order: 2
---

# Argument Groups

Argorator supports organizing related command-line arguments into groups for better help organization and creating mutually exclusive argument sets. This feature enhances the user experience by logically grouping related options and enforcing constraints where only one option from a set should be used.

Argorator uses natural language syntax for defining groups, making it intuitive and easy to read.

## Table of Contents

- [Natural Language Syntax](#natural-language-syntax)
- [Regular Argument Groups](#regular-argument-groups)
- [Mutually Exclusive Groups](#mutually-exclusive-groups)
- [Mixed Groups Example](#mixed-groups-example)
- [Syntax Reference](#syntax-reference)
- [Constraints and Validation](#constraints-and-validation)
- [Integration with Other Features](#integration-with-other-features)

## Natural Language Syntax

Define groups using intuitive English-like declarations that are easy to read and write.

### Basic Syntax

```bash
# group VAR1, VAR2, VAR3 as Group Name
# one of VAR1, VAR2 as Group Name
```

**Regular Groups**: Use `group VAR1, VAR2 as GroupName` to organize related arguments together in help output.

**Mutually Exclusive Groups**: Use `one of VAR1, VAR2 as GroupName` to ensure only one argument from the set can be specified.

### Auto-Naming

If you omit the `as GroupName` part, Argorator automatically generates group names:

```bash
# group SERVER_HOST, SERVER_PORT          # Auto-named "Group1"
# group LOG_LEVEL, LOG_FILE               # Auto-named "Group2"  
# one of VERBOSE, QUIET                   # Auto-named "ExclusiveGroup1"
# one of JSON_OUTPUT, XML_OUTPUT          # Auto-named "ExclusiveGroup2"
```

### Complete Example

```bash
#!/bin/bash
# group SERVER_HOST, SERVER_PORT, SERVER_TIMEOUT as Server Configuration
# one of VERBOSE, QUIET as Output Mode
# group LOG_LEVEL, LOG_FILE as Logging

# SERVER_HOST (str): Server hostname to connect to
# SERVER_PORT (int): Server port. Default: 8080
# SERVER_TIMEOUT (int): Connection timeout. Default: 30
# VERBOSE (bool) [alias: -v]: Enable verbose output
# QUIET (bool) [alias: -q]: Enable quiet mode
# LOG_LEVEL (choice[debug, info, warn, error]): Log level. Default: info
# LOG_FILE (str): Path to log file
# CONFIG_FILE (str): Configuration file path

echo "Server: $SERVER_HOST:$SERVER_PORT (timeout: $SERVER_TIMEOUT)"
echo "Logging: $LOG_LEVEL to $LOG_FILE"
echo "Config: $CONFIG_FILE"
echo "Verbose: $VERBOSE, Quiet: $QUIET"
```

This produces beautifully organized help output:

```bash
$ argorator server.sh --help
usage: server.sh [-h] --config_file CONFIG_FILE --log_file LOG_FILE
                 [--log_level {debug,info,warn,error}] [-q]
                 --server_host SERVER_HOST [--server_port SERVER_PORT]
                 [--server_timeout SERVER_TIMEOUT] [-v]

options:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
                        Configuration file path
  -q, --quiet           Enable quiet mode (default: false)
  -v, --verbose         Enable verbose output (default: false)

Server Configuration:
  --server_host SERVER_HOST
                        Server hostname to connect to
  --server_port SERVER_PORT
                        Server port (default: 8080)
  --server_timeout SERVER_TIMEOUT
                        Connection timeout (default: 30)

Logging:
  --log_file LOG_FILE   Path to log file
  --log_level {debug,info,warn,error}
                        Log level (default: info)
```

## Regular Argument Groups

Regular argument groups organize related arguments together in the help output, making it easier for users to understand which options work together.

### Basic Example

```bash
#!/bin/bash
# SERVER_HOST (str) [group: Server Configuration]: Server hostname  
# SERVER_PORT (int) [group: Server Configuration]: Server port. Default: 8080
# LOG_LEVEL (choice[debug, info, warn, error]) [group: Logging]: Log level. Default: info
# LOG_FILE (str) [group: Logging]: Path to log file

echo "Starting server on $SERVER_HOST:$SERVER_PORT"
echo "Logging at level $LOG_LEVEL to $LOG_FILE"
```

When you run this script, the help output will organize arguments into clear groups:

```bash
$ argorator server.sh --help
usage: argorator server.sh [-h] --server_host SERVER_HOST --log_file LOG_FILE
                           [--server_port SERVER_PORT] [--log_level LOG_LEVEL]

options:
  -h, --help            show this help message and exit

Server Configuration:
  --server_host SERVER_HOST
                        Server hostname
  --server_port SERVER_PORT
                        Server port (default: 8080)

Logging:
  --log_level LOG_LEVEL
                        Log level (default: info)
  --log_file LOG_FILE   Path to log file
```

### Usage Example

```bash
$ argorator server.sh --server_host api.example.com --log_file /var/log/app.log
Starting server on api.example.com:8080
Logging at level info to /var/log/app.log
```

## Mutually Exclusive Groups

Mutually exclusive groups ensure that only one argument from a set can be specified at a time. This is useful for options that conflict with each other, such as verbose vs. quiet modes.

### Basic Example

```bash
#!/bin/bash
# VERBOSE (bool) [exclusive: Output Mode]: Enable verbose output
# QUIET (bool) [exclusive: Output Mode]: Enable quiet mode  
# JSON_OUTPUT (bool) [exclusive: Format]: Output in JSON format
# XML_OUTPUT (bool) [exclusive: Format]: Output in XML format

if [ "$VERBOSE" = "true" ]; then
    echo "Verbose mode enabled"
elif [ "$QUIET" = "true" ]; then
    echo "Quiet mode enabled"
fi

if [ "$JSON_OUTPUT" = "true" ]; then
    echo "Using JSON output format"
elif [ "$XML_OUTPUT" = "true" ]; then
    echo "Using XML output format"
fi
```

### Help Output

```bash
$ argorator format.sh --help
usage: argorator format.sh [-h] [--verbose | --quiet] [--json_output | --xml_output]

options:
  -h, --help       show this help message and exit
  --verbose        Enable verbose output (default: false)
  --quiet          Enable quiet mode (default: false)
  --json_output    Output in JSON format (default: false)
  --xml_output     Output in XML format (default: false)
```

### Valid Usage

```bash
# Valid: Only one option from each exclusive group
$ argorator format.sh --verbose --json_output

# Valid: No options from exclusive groups (uses defaults)
$ argorator format.sh

# Invalid: Multiple options from the same exclusive group
$ argorator format.sh --verbose --quiet
usage: argorator format.sh [-h] [--verbose | --quiet] [--json_output | --xml_output]
argorator format.sh: error: argument --quiet: not allowed with argument --verbose
```

## Mixed Groups Example

You can combine regular groups and mutually exclusive groups in the same script:

```bash
#!/bin/bash
# DB_HOST (str) [group: Database]: Database hostname
# DB_PORT (int) [group: Database]: Database port. Default: 5432
# DB_NAME (str) [group: Database]: Database name
# 
# VERBOSE (bool) [exclusive_group: Verbosity]: Enable verbose logging
# QUIET (bool) [exclusive_group: Verbosity]: Enable quiet mode
#
# OUTPUT_FILE (str): Output file path
# CONFIG_FILE (str): Configuration file path

echo "Connecting to database: $DB_HOST:$DB_PORT/$DB_NAME"
echo "Output file: $OUTPUT_FILE"
echo "Config file: $CONFIG_FILE"

if [ "$VERBOSE" = "true" ]; then
    echo "Debug: Verbose mode active"
elif [ "$QUIET" = "true" ]; then
    echo "Running in quiet mode"
fi
```

### Help Output

```bash
$ argorator mixed.sh --help
usage: argorator mixed.sh [-h] --db_host DB_HOST --db_name DB_NAME --output_file OUTPUT_FILE 
                          --config_file CONFIG_FILE [--db_port DB_PORT] [--verbose | --quiet]

options:
  -h, --help            show this help message and exit
  --output_file OUTPUT_FILE
                        Output file path
  --config_file CONFIG_FILE
                        Configuration file path
  --verbose             Enable verbose logging (default: false)
  --quiet               Enable quiet mode (default: false)

Database:
  --db_host DB_HOST     Database hostname
  --db_name DB_NAME     Database name
  --db_port DB_PORT     Database port (default: 5432)
```



## Syntax Reference

### Natural Language Syntax

```bash
# group VAR1, VAR2, VAR3 as Group Name         # Regular group
# one of VAR1, VAR2 as Group Name              # Mutually exclusive group
# group VAR1, VAR2                             # Auto-named regular group
# one of VAR1, VAR2                            # Auto-named exclusive group
```

### Complete Syntax

Natural language groups work with all other annotation features:

```bash
# Natural language groups (defined once)
# group SERVER_HOST, SERVER_PORT as Server
# one of VERBOSE, QUIET as Output

# Individual annotations with full features
# SERVER_HOST (str) [alias: -h]: Server hostname. Default: localhost
# VERBOSE (bool) [alias: -v]: Enable verbose output
```

## Constraints and Validation

### Model Validation

- An argument cannot be in both a regular group and an exclusive group
- Group names can contain spaces and special characters
- Multiple variables can share the same group name

### Runtime Validation

- Mutually exclusive groups enforce that only one argument is provided
- If no arguments from an exclusive group are provided, all get their default values
- Regular groups have no runtime constraints—they're purely organizational

## Integration with Other Features

### Environment Variables

Environment variables work normally with groups:

```bash
#!/bin/bash
# API_KEY (str) [group: API Configuration]: API key for authentication
# API_URL (str) [group: API Configuration]: API endpoint URL

export API_KEY="default-key"
export API_URL="https://api.example.com"
```

### Aliases

Short aliases work with both group types:

```bash
#!/bin/bash
# VERBOSE (bool) [alias: -v] [exclusive_group: Verbosity]: Verbose mode
# QUIET (bool) [alias: -q] [exclusive_group: Verbosity]: Quiet mode
# CONFIG (str) [alias: -c] [group: Configuration]: Config file path
```

### Choice Types

Choice validation works with groups:

```bash
#!/bin/bash
# LOG_LEVEL (choice[debug, info, warn, error]) [group: Logging]: Log level
# FORMAT (choice[json, xml, yaml]) [exclusive_group: Output]: Output format
```

### Positional Arguments

Positional arguments are not affected by grouping and appear in their normal section:

```bash
#!/bin/bash
# VERBOSE (bool) [exclusive_group: Mode]: Verbose output
# QUIET (bool) [exclusive_group: Mode]: Quiet output

echo "Processing: $1 $2"
echo "Mode: verbose=$VERBOSE, quiet=$QUIET"
```

## Best Practices

1. **Use Descriptive Group Names**: Choose clear names that describe the purpose
   ```bash
   # Good
   # SERVER_HOST (str) [group: Server Configuration]: Server hostname
   
   # Avoid
   # SERVER_HOST (str) [group: Misc]: Server hostname
   ```

2. **Group Related Options**: Put logically related arguments together
   ```bash
   # Database connection options
   # DB_HOST (str) [group: Database]: Database host
   # DB_PORT (int) [group: Database]: Database port
   # DB_USER (str) [group: Database]: Database user
   ```

3. **Use Exclusive Groups for Conflicting Options**: Perfect for modes or formats
   ```bash
   # Output modes that conflict
   # VERBOSE (bool) [exclusive_group: Output Level]: Verbose output
   # QUIET (bool) [exclusive_group: Output Level]: Quiet output
   ```

4. **Combine with Defaults**: Provide sensible defaults for optional grouped arguments
   ```bash
   # LOG_LEVEL (choice[debug, info, warn]) [group: Logging]: Log level. Default: info
   ```

This feature enhances the usability of your shell scripts by providing better organization and preventing conflicting argument combinations, making your CLI tools more professional and user-friendly.