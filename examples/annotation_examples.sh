#!/bin/bash
# Example script showing various docstring-style annotations

# Basic parameter with description only
# :param NAME: Your name

# Parameter with type specified separately
# :param AGE: Your age in years
# :type AGE: int

# Inline type specification
# :param float HEIGHT: Your height in meters

# Boolean parameter
# :param bool VERBOSE: Enable verbose output

# Choice parameter with separate declarations
# :param COLOR: Your favorite color
# :type COLOR: choice
# :choices COLOR: red, green, blue, yellow

# String parameter with default shown in script
# :param str GREETING: Custom greeting message

echo "$GREETING, $NAME!"
echo "You are $AGE years old and $HEIGHT meters tall."
echo "Your favorite color is $COLOR."

if [ "$VERBOSE" = "true" ]; then
    echo "Additional information:"
    echo "  - Script: $0"
    echo "  - Arguments: $@"
fi