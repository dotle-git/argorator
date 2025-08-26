#!/bin/bash
# Test script with various variable types

echo "Script name: $0"
echo "First arg: $1"
echo "Second arg: $2"
echo "All args: $@"

echo "Undefined variable: $UNDEFINED_VAR"
echo "Environment variable HOME: $HOME"
echo "Another undefined: $CUSTOM_VAR"

# Define a local variable
LOCAL_VAR="local_value"
echo "Local variable: $LOCAL_VAR"

# Use braced variables
echo "Braced undefined: ${BRACED_VAR}"
echo "Braced environment: ${PATH}"