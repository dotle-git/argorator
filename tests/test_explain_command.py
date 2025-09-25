"""Tests for the explain command functionality."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from argorator.pipeline import Pipeline, PipelineCommand


class TestExplainCommand:
    """Test cases for the explain command."""
    
    def test_explain_simple_script(self):
        """Test explain command with a simple script."""
        script_content = """#!/usr/bin/env argorator
# Description: A simple greeting script

echo "Hello $NAME!"
echo "You are $AGE years old"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            command = PipelineCommand("explain", Path(script_path))
            pipeline = Pipeline()
            
            # Capture stdout
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                result = pipeline.run(command)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            # Verify exit code
            assert result == 0
            
            # Parse and verify JSON output
            json_output = json.loads(output)
            
            # Check structure
            assert "description" in json_output
            assert "arguments" in json_output
            assert "positionals" in json_output
            assert "varargs" in json_output
            
            # Check description
            assert json_output["description"] == "A simple greeting script"
            
            # Check arguments
            assert len(json_output["arguments"]) == 2
            
            # Find NAME and AGE arguments
            name_arg = None
            age_arg = None
            for arg in json_output["arguments"]:
                if arg["name"] == "NAME":
                    name_arg = arg
                elif arg["name"] == "AGE":
                    age_arg = arg
            
            assert name_arg is not None
            assert age_arg is not None
            
            # Check NAME argument
            assert name_arg["type"] == "str"
            assert name_arg["required"] is True
            assert name_arg["default"] is None
            
            # Check AGE argument
            assert age_arg["type"] == "str"
            assert age_arg["required"] is True
            assert age_arg["default"] is None
            
            # Check positionals and varargs
            assert json_output["positionals"] == []
            assert json_output["varargs"] is False
            
        finally:
            os.unlink(script_path)
    
    def test_explain_with_annotations(self):
        """Test explain command with Google-style annotations."""
        script_content = """#!/usr/bin/env argorator
# Description: A script with annotations

# NAME (str): Your full name
# AGE (int): Your age in years
# VERBOSE (bool): Enable verbose output
# OUTPUT_DIR (str): Directory for output files. Default: ./output

echo "Hello $NAME!"
echo "You are $AGE years old"
if [ "$VERBOSE" = "true" ]; then
    echo "Verbose mode enabled"
fi
echo "Output directory: $OUTPUT_DIR"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            command = PipelineCommand("explain", Path(script_path))
            pipeline = Pipeline()
            
            # Capture stdout
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                result = pipeline.run(command)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            # Verify exit code
            assert result == 0
            
            # Parse and verify JSON output
            json_output = json.loads(output)
            
            # Check description
            assert json_output["description"] == "A script with annotations"
            
            # Check arguments
            assert len(json_output["arguments"]) == 4
            
            # Find arguments by name
            args_by_name = {arg["name"]: arg for arg in json_output["arguments"]}
            
            # Check NAME argument
            name_arg = args_by_name["NAME"]
            assert name_arg["type"] == "str"
            assert name_arg["help"] == "Your full name"
            assert name_arg["required"] is True
            assert name_arg["default"] is None
            
            # Check AGE argument
            age_arg = args_by_name["AGE"]
            assert age_arg["type"] == "int"
            assert age_arg["help"] == "Your age in years"
            assert age_arg["required"] is True
            assert age_arg["default"] is None
            
            # Check VERBOSE argument
            verbose_arg = args_by_name["VERBOSE"]
            assert verbose_arg["type"] == "bool"
            assert verbose_arg["help"] == "Enable verbose output"
            assert verbose_arg["required"] is True
            assert verbose_arg["default"] is None
            
            # Check OUTPUT_DIR argument
            output_arg = args_by_name["OUTPUT_DIR"]
            assert output_arg["type"] == "str"
            assert output_arg["help"] == "Directory for output files"
            assert output_arg["required"] is True
            assert output_arg["default"] == "./output"
            
        finally:
            os.unlink(script_path)
    
    def test_explain_with_environment_variables(self):
        """Test explain command with environment variables."""
        script_content = """#!/usr/bin/env argorator
# Description: A script using environment variables

echo "User: $USER"
echo "Home: $HOME"
echo "Path: $PATH"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            command = PipelineCommand("explain", Path(script_path))
            pipeline = Pipeline()
            
            # Capture stdout
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                result = pipeline.run(command)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            # Verify exit code
            assert result == 0
            
            # Parse and verify JSON output
            json_output = json.loads(output)
            
            # Check description
            assert json_output["description"] == "A script using environment variables"
            
            # Check arguments (should be optional with environment defaults)
            assert len(json_output["arguments"]) >= 3
            
            # Find arguments by name
            args_by_name = {arg["name"]: arg for arg in json_output["arguments"]}
            
            # Check USER argument
            user_arg = args_by_name.get("USER")
            if user_arg:  # USER might not be in environment in test
                assert user_arg["required"] is False
                assert user_arg["default"] is not None
            
            # Check HOME argument
            home_arg = args_by_name.get("HOME")
            if home_arg:  # HOME might not be in environment in test
                assert home_arg["required"] is False
                assert home_arg["default"] is not None
            
            # Check PATH argument
            path_arg = args_by_name.get("PATH")
            if path_arg:  # PATH might not be in environment in test
                assert path_arg["required"] is False
                assert path_arg["default"] is not None
            
        finally:
            os.unlink(script_path)
    
    def test_explain_with_positional_arguments(self):
        """Test explain command with positional arguments."""
        script_content = """#!/usr/bin/env argorator
# Description: A script with positional arguments

echo "First argument: $1"
echo "Second argument: $2"
echo "All arguments: $@"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            command = PipelineCommand("explain", Path(script_path))
            pipeline = Pipeline()
            
            # Capture stdout
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                result = pipeline.run(command)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            # Verify exit code
            assert result == 0
            
            # Parse and verify JSON output
            json_output = json.loads(output)
            
            # Check description
            assert json_output["description"] == "A script with positional arguments"
            
            # Check arguments (should be empty for this script)
            assert json_output["arguments"] == []
            
            # Check positionals
            assert len(json_output["positionals"]) == 2
            
            # Check positional arguments
            positionals = json_output["positionals"]
            assert positionals[0]["name"] == "ARG1"
            assert positionals[0]["index"] == 1
            assert positionals[1]["name"] == "ARG2"
            assert positionals[1]["index"] == 2
            
            # Check varargs
            assert json_output["varargs"] is True
            
        finally:
            os.unlink(script_path)
    
    def test_explain_with_choice_arguments(self):
        """Test explain command with choice type arguments."""
        script_content = """#!/usr/bin/env argorator
# Description: A script with choice arguments

# MODE (choice[debug,info,warn,error]): Log level
# FORMAT (choice[json,xml,yaml]): Output format. Default: json

echo "Mode: $MODE"
echo "Format: $FORMAT"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            command = PipelineCommand("explain", Path(script_path))
            pipeline = Pipeline()
            
            # Capture stdout
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                result = pipeline.run(command)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            # Verify exit code
            assert result == 0
            
            # Parse and verify JSON output
            json_output = json.loads(output)
            
            # Check description
            assert json_output["description"] == "A script with choice arguments"
            
            # Check arguments
            assert len(json_output["arguments"]) == 2
            
            # Find arguments by name
            args_by_name = {arg["name"]: arg for arg in json_output["arguments"]}
            
            # Check MODE argument
            mode_arg = args_by_name["MODE"]
            assert mode_arg["type"] == "choice"
            assert mode_arg["help"] == "Log level"
            assert mode_arg["required"] is True
            assert mode_arg["default"] is None
            assert mode_arg["choices"] == ["debug", "info", "warn", "error"]
            
            # Check FORMAT argument
            format_arg = args_by_name["FORMAT"]
            assert format_arg["type"] == "choice"
            assert format_arg["help"] == "Output format"
            assert format_arg["required"] is True
            assert format_arg["default"] == "json"
            assert format_arg["choices"] == ["json", "xml", "yaml"]
            
        finally:
            os.unlink(script_path)
    
    def test_explain_with_aliases(self):
        """Test explain command with argument aliases."""
        script_content = """#!/usr/bin/env argorator
# Description: A script with argument aliases

# NAME (str) [alias: -n]: Your name
# VERBOSE (bool) [alias: -v]: Enable verbose output

echo "Hello $NAME!"
if [ "$VERBOSE" = "true" ]; then
    echo "Verbose mode enabled"
fi
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            command = PipelineCommand("explain", Path(script_path))
            pipeline = Pipeline()
            
            # Capture stdout
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                result = pipeline.run(command)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            # Verify exit code
            assert result == 0
            
            # Parse and verify JSON output
            json_output = json.loads(output)
            
            # Check description
            assert json_output["description"] == "A script with argument aliases"
            
            # Check arguments
            assert len(json_output["arguments"]) == 2
            
            # Find arguments by name
            args_by_name = {arg["name"]: arg for arg in json_output["arguments"]}
            
            # Check NAME argument
            name_arg = args_by_name["NAME"]
            assert name_arg["type"] == "str"
            assert name_arg["help"] == "Your name"
            assert name_arg["alias"] == "-n"
            
            # Check VERBOSE argument
            verbose_arg = args_by_name["VERBOSE"]
            assert verbose_arg["type"] == "bool"
            assert verbose_arg["help"] == "Enable verbose output"
            assert verbose_arg["alias"] == "-v"
            
        finally:
            os.unlink(script_path)
    
    def test_explain_no_description(self):
        """Test explain command with a script that has no description."""
        script_content = """#!/usr/bin/env argorator

echo "Hello $NAME!"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            command = PipelineCommand("explain", Path(script_path))
            pipeline = Pipeline()
            
            # Capture stdout
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                result = pipeline.run(command)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            # Verify exit code
            assert result == 0
            
            # Parse and verify JSON output
            json_output = json.loads(output)
            
            # Check description is None
            assert json_output["description"] is None
            
            # Check arguments
            assert len(json_output["arguments"]) == 1
            assert json_output["arguments"][0]["name"] == "NAME"
            
        finally:
            os.unlink(script_path)
    
    def test_explain_empty_script(self):
        """Test explain command with an empty script."""
        script_content = """#!/usr/bin/env argorator
# Description: An empty script

echo "No variables here"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            command = PipelineCommand("explain", Path(script_path))
            pipeline = Pipeline()
            
            # Capture stdout
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                result = pipeline.run(command)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            # Verify exit code
            assert result == 0
            
            # Parse and verify JSON output
            json_output = json.loads(output)
            
            # Check description
            assert json_output["description"] == "An empty script"
            
            # Check arguments and positionals are empty
            assert json_output["arguments"] == []
            assert json_output["positionals"] == []
            assert json_output["varargs"] is False
            
        finally:
            os.unlink(script_path)