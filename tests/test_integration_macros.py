"""Integration tests for iteration macros to catch real-world bugs."""
import pytest
import subprocess
import tempfile
import os
from pathlib import Path


class TestIterationMacroIntegration:
    """Integration tests for iteration macro functionality."""
    
    def _run_argorator(self, script_content: str, args: list, expect_success: bool = True):
        """Helper to run argorator on a script with given arguments.
        
        Uses dynamic path resolution to work from any directory, avoiding hardcoded paths
        that could cause FileNotFoundError in different environments.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # Find project root (directory containing pyproject.toml)
            current_dir = Path(__file__).parent
            project_root = current_dir.parent  # Go up from tests/ to project root
            src_path = project_root / 'src'
            
            cmd = ['python3', '-m', 'argorator.cli', 'run', script_path] + args
            env = os.environ.copy()
            env['PYTHONPATH'] = str(src_path)
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=str(project_root),
                env=env
            )
            
            if expect_success:
                if result.returncode != 0:
                    pytest.fail(f"Command failed with exit code {result.returncode}\\n"
                              f"STDOUT: {result.stdout}\\n"
                              f"STDERR: {result.stderr}")
                return result.stdout
            else:
                return result
        finally:
            os.unlink(script_path)
    
    def test_iterator_variables_not_in_cli_args(self):
        """Test that iterator variables don't become CLI arguments."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Input data for processing

# for item in $DATA sep ,
echo "Item: $item"
'''
        
        # This should work without requiring --item argument
        output = self._run_argorator(script, ['--data', 'a,b,c'])
        assert 'Item: a' in output
        assert 'Item: b' in output
        assert 'Item: c' in output
    
    def test_single_quote_separator(self):
        """Test that single quote separators work correctly."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Data with single quote separators

# for part in $DATA sep "'"
echo "Part: [$part]"
'''
        
        output = self._run_argorator(script, ['--data', "a'b'c"])
        assert 'Part: [a]' in output
        assert 'Part: [b]' in output
        assert 'Part: [c]' in output
    
    def test_regex_special_chars_separator(self):
        """Test that regex special characters in separators are escaped."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Data with .* separators

# for part in $DATA separated by ".*"
echo "Part: [$part]"
'''
        
        output = self._run_argorator(script, ['--data', 'one.*two.*three'])
        assert 'Part: [one]' in output
        assert 'Part: [two]' in output
        assert 'Part: [three]' in output
    
    def test_backslash_separator(self):
        """Test that backslash separators work correctly."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Data with backslash separators

# for part in $DATA sep "\\\\"
echo "Part: [$part]"
'''
        
        output = self._run_argorator(script, ['--data', 'a\\\\b\\\\c'])
        assert 'Part: [a]' in output
        assert 'Part: [b]' in output  
        assert 'Part: [c]' in output
    
    def test_tab_separator(self):
        """Test that tab separators work correctly."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Data with tab separators

# for part in $DATA sep "\\t"
echo "Part: [$part]"
'''
        
        # Create data with actual tab characters
        tab_data = 'a\tb\tc'  # Actual tab characters
        output = self._run_argorator(script, ['--data', tab_data])
        assert 'Part: [a]' in output
        assert 'Part: [b]' in output
        assert 'Part: [c]' in output
    
    def test_complex_separators_integration(self):
        """Test multiple complex separators in one script."""
        script = '''#!/usr/bin/env argorator
# COMMA_DATA (str): Comma-separated data
# QUOTE_DATA (str): Quote-separated data  
# REGEX_DATA (str): Data with regex chars

echo "=== Comma ==="
# for item in $COMMA_DATA sep ,
echo "[$item]"

echo "=== Quote ==="  
# for item in $QUOTE_DATA sep "'"
echo "[$item]"

echo "=== Regex ==="
# for item in $REGEX_DATA separated by ".*"
echo "[$item]"
'''
        
        output = self._run_argorator(script, [
            '--comma_data', 'a,b,c',
            '--quote_data', "x'y'z", 
            '--regex_data', 'hello.*world.*test'
        ])
        
        # Check comma separation
        lines = output.split('\n')
        comma_section = []
        quote_section = []
        regex_section = []
        current_section = None
        
        for line in lines:
            if '=== Comma ===' in line:
                current_section = comma_section
            elif '=== Quote ===' in line:
                current_section = quote_section
            elif '=== Regex ===' in line:
                current_section = regex_section
            elif line.startswith('[') and line.endswith(']'):
                if current_section is not None:
                    current_section.append(line)
        
        assert '[a]' in comma_section
        assert '[b]' in comma_section
        assert '[c]' in comma_section
        
        assert '[x]' in quote_section  
        assert '[y]' in quote_section
        assert '[z]' in quote_section
        
        assert '[hello]' in regex_section
        assert '[world]' in regex_section
        assert '[test]' in regex_section
    
    def test_function_macros_with_separators(self):
        """Test that function macros work with complex separators."""
        script = '''#!/usr/bin/env argorator
# DATA (str): Data to process

# for item in $DATA sep "'" | with "prefix"
process_item() {
    echo "Processing: $1 with $2"
}
'''
        
        # Function parameters $1 and $2 are provided by the macro, not CLI arguments
        output = self._run_argorator(script, ['--data', "a'b'c"])
        assert 'Processing: a with prefix' in output
        assert 'Processing: b with prefix' in output
        assert 'Processing: c with prefix' in output
    
    def test_nested_iteration_variables_excluded(self):
        """Test that all iterator variables in nested scenarios are excluded."""
        script = '''#!/usr/bin/env argorator
# SERVERS (str): Server list
# PORTS (str): Port list

# for server in $SERVERS sep ,
echo "Server: $server"

# for port in $PORTS sep :
echo "Port: $port"
'''
        
        # Should not require --server or --port arguments
        output = self._run_argorator(script, [
            '--servers', 'web1,web2',
            '--ports', '80:443'
        ])
        assert 'Server: web1' in output
        assert 'Server: web2' in output
        assert 'Port: 80' in output  
        assert 'Port: 443' in output
    
    def test_all_separator_syntaxes(self):
        """Test all supported separator syntax variations."""
        script = '''#!/usr/bin/env argorator
# DATA1 (str): Data for sep syntax
# DATA2 (str): Data for separated by syntax

echo "=== sep syntax ==="
# for item in $DATA1 sep ,
echo "[$item]"

echo "=== separated by syntax ==="
# for item in $DATA2 separated by "::"
echo "[$item]"
'''
        
        output = self._run_argorator(script, [
            '--data1', 'a,b,c',
            '--data2', 'x::y::z'
        ])
        
        # Parse output sections
        lines = output.split('\n')
        sep_items = []
        separated_items = []
        current_section = None
        
        for line in lines:
            if '=== sep syntax ===' in line:
                current_section = sep_items
            elif '=== separated by syntax ===' in line:
                current_section = separated_items
            elif line.startswith('[') and line.endswith(']'):
                if current_section is not None:
                    current_section.append(line.strip('[]'))
        
        assert 'a' in sep_items
        assert 'b' in sep_items  
        assert 'c' in sep_items
        
        assert 'x' in separated_items
        assert 'y' in separated_items
        assert 'z' in separated_items