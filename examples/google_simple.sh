#!/bin/bash
# Simple example with Google-style annotations

# NAME: Your name (required, no type = string)
# AGE (int): Your age in years
# HEIGHT (float): Your height in meters
# CITY (str): City where you live. Default: Unknown
# VERBOSE (bool): Enable verbose output. Default: false
# COLOR (choice[red, green, blue]): Your favorite color

echo "Hello, $NAME!"
echo "You are $AGE years old and $HEIGHT meters tall."
echo "You live in $CITY and your favorite color is $COLOR."

if [ "$VERBOSE" = "true" ]; then
    echo ""
    echo "=== Verbose Information ==="
    echo "Script: $0"
    echo "All arguments: $@"
fi