"""Tests for safety macro functionality."""
import pytest
from argorator.macros.processor import macro_processor
from argorator.macros.parser import macro_parser
from argorator.macros.models import SafetyMacro, MacroComment


class TestSafetyMacroParser:
    """Test the safety macro parser functionality."""
    
    def test_detect_set_strict_macro(self):
        """Test detection of set strict macro."""
        script = '''#!/bin/bash
# set strict
echo "Hello World"'''
        
        comments = macro_parser.find_macro_comments(script)
        assert len(comments) == 1
        assert comments[0].macro_type == "safety"
        assert comments[0].content == "set strict"
    
    def test_detect_trap_cleanup_macro(self):
        """Test detection of trap cleanup macro."""
        script = '''#!/bin/bash
# trap cleanup
echo "Hello World"'''
        
        comments = macro_parser.find_macro_comments(script)
        assert len(comments) == 1
        assert comments[0].macro_type == "safety"
        assert comments[0].content == "trap cleanup"
    
    def test_case_insensitive_detection(self):
        """Test that safety macros are detected case-insensitively."""
        script = '''#!/bin/bash
# SET STRICT
# Trap Cleanup
echo "Hello World"'''
        
        comments = macro_parser.find_macro_comments(script)
        assert len(comments) == 2
        assert all(c.macro_type == "safety" for c in comments)
    
    def test_parse_set_strict_macro(self):
        """Test parsing of set strict macro."""
        comment = MacroComment(
            line_number=1,
            content="set strict",
            macro_type="safety",
            raw_line="# set strict"
        )
        
        safety_macro = macro_parser.parse_safety_macro(comment)
        assert isinstance(safety_macro, SafetyMacro)
        assert safety_macro.safety_type == "set_strict"
        assert safety_macro.options == []
    
    def test_parse_trap_cleanup_macro(self):
        """Test parsing of trap cleanup macro."""
        comment = MacroComment(
            line_number=1,
            content="trap cleanup",
            macro_type="safety",
            raw_line="# trap cleanup"
        )
        
        safety_macro = macro_parser.parse_safety_macro(comment)
        assert isinstance(safety_macro, SafetyMacro)
        assert safety_macro.safety_type == "trap_cleanup"
        assert safety_macro.options == []
    
    def test_invalid_safety_macro(self):
        """Test error handling for invalid safety macro."""
        comment = MacroComment(
            line_number=1,
            content="set invalid",
            macro_type="safety",
            raw_line="# set invalid"
        )
        
        with pytest.raises(ValueError, match="Unknown safety macro type"):
            macro_parser.parse_safety_macro(comment)


class TestSafetyMacroTransformations:
    """Test safety macro code generation."""
    
    def test_set_strict_transformation(self):
        """Test set strict macro generates correct bash code."""
        comment = MacroComment(
            line_number=1,
            content="set strict",
            macro_type="safety",
            raw_line="# set strict"
        )
        
        safety_macro = macro_parser.parse_safety_macro(comment)
        transformation = safety_macro.generate_transformation()
        assert transformation == "set -eou --pipefail"
    
    def test_trap_cleanup_transformation(self):
        """Test trap cleanup macro generates correct bash code."""
        comment = MacroComment(
            line_number=1,
            content="trap cleanup",
            macro_type="safety",
            raw_line="# trap cleanup"
        )
        
        safety_macro = macro_parser.parse_safety_macro(comment)
        transformation = safety_macro.generate_transformation()
        
        expected = '''# Cleanup trap handler
cleanup() {
    local exit_code=$?
    echo "Cleaning up..." >&2
    # Add your cleanup code here
    exit $exit_code
}

trap cleanup EXIT ERR INT TERM'''
        
        assert transformation == expected


class TestSafetyMacroProcessing:
    """Test safety macro processing integration."""
    
    def test_process_set_strict_macro(self):
        """Test processing of set strict macro."""
        script = '''#!/bin/bash
# set strict
echo "Hello $NAME!"'''
        
        result = macro_processor.process_macros(script)
        lines = result.split('\n')
        
        # Should have shebang, set command, blank line, then echo
        assert lines[0] == "#!/bin/bash"
        assert lines[1] == "set -eou --pipefail"
        assert lines[2] == ""
        assert lines[3] == 'echo "Hello $NAME!"'
    
    def test_process_trap_cleanup_macro(self):
        """Test processing of trap cleanup macro."""
        script = '''#!/bin/bash
# trap cleanup
echo "Hello $NAME!"'''
        
        result = macro_processor.process_macros(script)
        lines = result.split('\n')
        
        # Should have shebang, trap setup, blank line, then echo
        assert lines[0] == "#!/bin/bash"
        assert "cleanup()" in result
        assert "trap cleanup EXIT ERR INT TERM" in result
        assert 'echo "Hello $NAME!"' in result
    
    def test_process_both_safety_macros(self):
        """Test processing both safety macros together."""
        script = '''#!/bin/bash
# set strict
# trap cleanup
echo "Hello $NAME!"'''
        
        result = macro_processor.process_macros(script)
        lines = result.split('\n')
        
        # Should have both macros processed
        assert "set -eou --pipefail" in result
        assert "cleanup()" in result
        assert "trap cleanup EXIT ERR INT TERM" in result
        assert 'echo "Hello $NAME!"' in result
        # Should start with shebang
        assert lines[0] == "#!/bin/bash"
    
    def test_safety_macros_without_shebang(self):
        """Test safety macros work without shebang."""
        script = '''# set strict
echo "Hello $NAME!"'''
        
        result = macro_processor.process_macros(script)
        lines = result.split('\n')
        
        # Should start with set command
        assert lines[0] == "set -eou --pipefail"
        assert lines[1] == ""
        assert lines[2] == 'echo "Hello $NAME!"'
    
    def test_safety_macros_with_iteration_macros(self):
        """Test safety macros work alongside iteration macros."""
        script = '''#!/bin/bash
# set strict
# for file in *.txt
echo "Processing $file"'''
        
        result = macro_processor.process_macros(script)
        
        # Should have both safety and iteration transformations
        assert "set -eou --pipefail" in result
        assert "for file in *.txt" in result
        assert "echo \"Processing $file\"" in result
    
    def test_multiple_safety_macros_order(self):
        """Test that multiple safety macros are processed in correct order."""
        script = '''#!/bin/bash
# trap cleanup
echo "Some code"
# set strict
echo "More code"'''
        
        result = macro_processor.process_macros(script)
        lines = result.split('\n')
        
        # Safety macros should be processed in order they appear
        # First trap, then set strict
        trap_line = None
        set_line = None
        for i, line in enumerate(lines):
            if "cleanup()" in line:
                trap_line = i
            elif "set -eou --pipefail" in line:
                set_line = i
        
        assert trap_line is not None
        assert set_line is not None
        assert trap_line < set_line


class TestSafetyMacroValidation:
    """Test safety macro validation."""
    
    def test_validate_valid_safety_macros(self):
        """Test validation passes for valid safety macros."""
        script = '''#!/bin/bash
# set strict
# trap cleanup
echo "Hello World"'''
        
        errors = macro_processor.validate_macros(script)
        assert len(errors) == 0
    
    def test_validate_invalid_safety_macro(self):
        """Test validation catches invalid safety macros."""
        script = '''#!/bin/bash
# set invalid
echo "Hello World"'''
        
        errors = macro_processor.validate_macros(script)
        assert len(errors) == 1
        assert "INVALID SAFETY MACRO" in errors[0]
        assert "Line 2" in errors[0]