#!/bin/bash
# Example with boolean flags and aliases

# VERBOSE (bool) [alias: -v]: Enable verbose output. Default: false
# DEBUG (bool) [alias: -d]: Enable debug mode. Default: false
# QUIET (bool) [alias: -q]: Suppress output. Default: true
# SERVICE (str) [alias: -s]: Service name
# PORT (int) [alias: -p]: Port number. Default: 8080

echo "Configuration:"
echo "  Service: $SERVICE"
echo "  Port: $PORT"

if [ "$VERBOSE" = "true" ]; then
    echo "  [VERBOSE] Running in verbose mode"
fi

if [ "$DEBUG" = "true" ]; then
    echo "  [DEBUG] Debug mode enabled"
fi

if [ "$QUIET" = "false" ]; then
    echo "  Output is not suppressed (quiet=false)"
fi