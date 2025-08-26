#!/bin/bash
# NAME (str) [alias: -n]: Your name
# VERBOSE (bool) [alias: -v]: Verbose output. Default: false

echo "HOME=$HOME"
echo "FOO=$FOO"
echo "ARG1=$1"
echo "REST=$@"

if [ "$VERBOSE" = "true" ]; then
    echo "Hello, $NAME (verbose mode)"
fi
