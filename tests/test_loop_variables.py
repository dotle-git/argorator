"""Tests for loop variable detection and handling."""
import pytest
from pathlib import Path

from argorator import cli
from argorator.analyzers import parse_loop_variables, parse_variable_usages, parse_defined_variables


def write_script(tmp_path: Path, name: str, content: str) -> Path:
    """Helper to write a test script."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


class TestLoopVariableDetection:
    """Test loop variable detection functionality."""
    
    def test_parse_loop_variables_for_loop(self):
        """Test detection of variables in for loops."""
        script = '''#!/bin/bash
for file in *.txt; do
    echo "Processing $file"
done

for item in $LIST; do
    echo "Item: $item"
done
'''
        loop_vars = parse_loop_variables(script)
        assert "file" in loop_vars
        assert "item" in loop_vars
    
    def test_parse_loop_variables_while_read(self):
        """Test detection of variables in while read loops."""
        script = '''#!/bin/bash
while IFS= read -r line; do
    echo "Line: $line"
done < input.txt

while read -r word; do
    echo "Word: $word"
done
'''
        loop_vars = parse_loop_variables(script)
        assert "line" in loop_vars
        assert "word" in loop_vars
    
    def test_parse_loop_variables_c_style_for(self):
        """Test detection of variables in C-style for loops."""
        script = '''#!/bin/bash
for ((i=1; i<=10; i++)); do
    echo "Count: $i"
done

for ((j=0; j<5; j++)); do
    echo "Index: $j"
done
'''
        loop_vars = parse_loop_variables(script)
        assert "i" in loop_vars
        assert "j" in loop_vars
    
    def test_parse_loop_variables_mixed(self):
        """Test detection of variables in mixed loop types."""
        script = '''#!/bin/bash
for file in *.txt; do
    while IFS= read -r line; do
        echo "File: $file, Line: $line"
    done < "$file"
done
'''
        loop_vars = parse_loop_variables(script)
        assert "file" in loop_vars
        assert "line" in loop_vars
    
    def test_parse_loop_variables_no_loops(self):
        """Test that scripts without loops return empty set."""
        script = '''#!/bin/bash
echo "Hello World"
VAR="test"
echo "Variable: $VAR"
'''
        loop_vars = parse_loop_variables(script)
        assert len(loop_vars) == 0


class TestLoopVariableIntegration:
    """Test integration of loop variable detection with the full pipeline."""
    
    def test_for_loop_variables_not_required(self, tmp_path: Path):
        """Test that for loop variables are not treated as required CLI arguments."""
        script = write_script(
            tmp_path,
            "for_loop.sh",
            '''#!/bin/bash
# This script should NOT require 'file' as a CLI argument
for file in *.txt; do
    echo "Processing file: $file"
done
'''
        )
        
        # Create some test files
        (tmp_path / "test1.txt").write_text("content1")
        (tmp_path / "test2.txt").write_text("content2")
        
        # Should run without requiring --file argument
        rc = cli.main(["run", str(script)])
        assert rc == 0
    
    def test_while_read_variables_not_required(self, tmp_path: Path):
        """Test that while read loop variables are not treated as required CLI arguments."""
        script = write_script(
            tmp_path,
            "while_read.sh",
            f'''#!/bin/bash
# This script should NOT require 'line' as a CLI argument
while IFS= read -r line; do
    echo "Processing line: $line"
done < {tmp_path}/input.txt
'''
        )
        
        # Create input file
        (tmp_path / "input.txt").write_text("line1\nline2\nline3")
        
        # Should run without requiring --line argument
        rc = cli.main(["run", str(script)])
        assert rc == 0
    
    def test_c_style_for_variables_not_required(self, tmp_path: Path):
        """Test that C-style for loop variables are not treated as required CLI arguments."""
        script = write_script(
            tmp_path,
            "c_style_for.sh",
            '''#!/bin/bash
# This script should NOT require 'i' as a CLI argument
for ((i=1; i<=3; i++)); do
    echo "Count: $i"
done
'''
        )
        
        # Should run without requiring --i argument
        rc = cli.main(["run", str(script)])
        assert rc == 0
    
    def test_mixed_loop_variables_not_required(self, tmp_path: Path):
        """Test that mixed loop variables are not treated as required CLI arguments."""
        script = write_script(
            tmp_path,
            "mixed_loops.sh",
            f'''#!/bin/bash
# This script should NOT require 'file' or 'line' as CLI arguments
cd {tmp_path}
for file in *.txt; do
    echo "Processing file: $file"
    while IFS= read -r line; do
        echo "  Line: $line"
    done < "$file"
done
'''
        )
        
        # Create test files
        (tmp_path / "test1.txt").write_text("line1\nline2")
        (tmp_path / "test2.txt").write_text("line3\nline4")
        
        # Should run without requiring --file or --line arguments
        rc = cli.main(["run", str(script)])
        assert rc == 0
    
    def test_loop_variables_with_actual_parameters(self, tmp_path: Path):
        """Test that loop variables don't interfere with actual script parameters."""
        script = write_script(
            tmp_path,
            "mixed_params.sh",
            f'''#!/bin/bash
# INPUT_FILE (file): Input file to process
# OUTPUT_DIR (str): Output directory

echo "Processing $INPUT_FILE to $OUTPUT_DIR"

cd {tmp_path}
for file in *.txt; do
    echo "Found file: $file"
done
'''
        )
        
        # Create test files
        (tmp_path / "test1.txt").write_text("content1")
        (tmp_path / "test2.txt").write_text("content2")
        (tmp_path / "input.txt").write_text("input content")
        
        # Should require INPUT_FILE and OUTPUT_DIR but NOT file
        rc = cli.main([
            "run", str(script), 
            "--input_file", str(tmp_path / "input.txt"),
            "--output_dir", str(tmp_path / "output")
        ])
        assert rc == 0
    
    def test_nested_loop_variables(self, tmp_path: Path):
        """Test that nested loop variables are properly detected."""
        script = write_script(
            tmp_path,
            "nested_loops.sh",
            f'''#!/bin/bash
# This script should NOT require any loop variables as CLI arguments
cd {tmp_path}
for dir in */; do
    echo "Processing directory: $dir"
    for file in "$dir"*.txt; do
        echo "  Found file: $file"
        while IFS= read -r line; do
            echo "    Line: $line"
        done < "$file"
    done
done
'''
        )
        
        # Create test directory structure
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("line1\nline2")
        (test_dir / "file2.txt").write_text("line3\nline4")
        
        # Should run without requiring any loop variable arguments
        rc = cli.main(["run", str(script)])
        assert rc == 0


class TestLoopVariableEdgeCases:
    """Test edge cases for loop variable detection."""
    
    def test_loop_variables_with_annotations(self, tmp_path: Path):
        """Test that loop variables are ignored even if they have annotations."""
        script = write_script(
            tmp_path,
            "annotated_loop.sh",
            f'''#!/bin/bash
# file (str): This annotation should be ignored for loop variables
# line (str): This annotation should also be ignored

cd {tmp_path}
for file in *.txt; do
    echo "Processing file: $file"
    while IFS= read -r line; do
        echo "  Line: $line"
    done < "$file"
done
'''
        )
        
        # Create test file
        (tmp_path / "test.txt").write_text("line1\nline2")
        
        # Should run without requiring --file or --line arguments
        # even though they have annotations
        rc = cli.main(["run", str(script)])
        assert rc == 0
    
    def test_loop_variables_in_functions(self, tmp_path: Path):
        """Test that loop variables in functions are properly detected."""
        script = write_script(
            tmp_path,
            "function_loops.sh",
            f'''#!/bin/bash
process_files() {{
    cd {tmp_path}
    for file in *.txt; do
        echo "Processing: $file"
    done
}}

read_lines() {{
    while IFS= read -r line; do
        echo "Line: $line"
    done < {tmp_path}/input.txt
}}

process_files
read_lines
'''
        )
        
        # Create test files
        (tmp_path / "test1.txt").write_text("content1")
        (tmp_path / "test2.txt").write_text("content2")
        (tmp_path / "input.txt").write_text("line1\nline2")
        
        # Should run without requiring loop variable arguments
        rc = cli.main(["run", str(script)])
        assert rc == 0
    
    def test_loop_variables_with_quotes(self, tmp_path: Path):
        """Test that loop variables with quotes are properly detected."""
        script = write_script(
            tmp_path,
            "quoted_loops.sh",
            f'''#!/bin/bash
cd {tmp_path}
for file in *.txt; do
    echo "Processing: $file"
done

while IFS= read -r line; do
    echo "Line: $line"
done < input.txt
'''
        )
        
        # Create test files
        (tmp_path / "test.txt").write_text("content")
        (tmp_path / "input.txt").write_text("line1\nline2")
        
        # Should run without requiring loop variable arguments
        rc = cli.main(["run", str(script)])
        assert rc == 0