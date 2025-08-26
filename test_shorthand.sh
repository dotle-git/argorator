#!/bin/bash
# VERBOSE (bool) [xgroup: Output Mode] [alias: -v]: Enable verbose output
# QUIET (bool) [xgroup: Output Mode] [alias: -q]: Enable quiet mode
# DEBUG (bool) [exclusive_group: Debug Level]: Enable debug mode
# TRACE (bool) [xgroup: Debug Level]: Enable trace mode
# CONFIG_FILE (str) [alias: -c]: Configuration file path

echo "Verbose: $VERBOSE"
echo "Quiet: $QUIET" 
echo "Debug: $DEBUG"
echo "Trace: $TRACE"
echo "Config: $CONFIG_FILE"