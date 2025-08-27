"""Tests for safety macro functionality."""
import pytest
from argorator.macros.processor import macro_processor
from argorator.macros.parser import macro_parser
from argorator.macros.models import SafetyMacro, MacroComment, MacroTarget


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
        """Test parsing of trap cleanup macro with target."""
        comment = MacroComment(
            line_number=1,
            content="trap cleanup",
            macro_type="safety",
            raw_line="# trap cleanup"
        )
        
        target = MacroTarget(
            target_type="line",
            start_line=2,
            end_line=2,
            content='echo "Cleaning up..."',
            metadata={}
        )
        
        safety_macro = macro_parser.parse_safety_macro(comment, target)
        assert isinstance(safety_macro, SafetyMacro)
        assert safety_macro.safety_type == "trap_cleanup"
        assert safety_macro.target == target
        assert safety_macro.signals == []  # Default signals
        assert safety_macro.options == []
    
    def test_parse_trap_cleanup_with_custom_signals(self):
        """Test parsing trap cleanup macro with custom signals."""
        comment = MacroComment(
            line_number=1,
            content="trap cleanup EXIT,ERR,INT",
            macro_type="safety",
            raw_line="# trap cleanup EXIT,ERR,INT"
        )
        
        target = MacroTarget(
            target_type="line",
            start_line=2,
            end_line=2,
            content='echo "Cleaning up..."',
            metadata={}
        )
        
        safety_macro = macro_parser.parse_safety_macro(comment, target)
        assert safety_macro.safety_type == "trap_cleanup"
        assert safety_macro.signals == ["EXIT", "ERR", "INT"]
    
    def test_parse_trap_cleanup_function_target(self):
        """Test parsing trap cleanup macro with function target."""
        comment = MacroComment(
            line_number=1,
            content="trap cleanup",
            macro_type="safety",
            raw_line="# trap cleanup"
        )
        
        target = MacroTarget(
            target_type="function",
            start_line=2,
            end_line=5,
            content='''cleanup_files() {
    rm -f /tmp/tempfile
    echo "Cleanup complete"
}''',
            metadata={"function_name": "cleanup_files"}
        )
        
        safety_macro = macro_parser.parse_safety_macro(comment, target)
        assert safety_macro.safety_type == "trap_cleanup"
        assert safety_macro.target.target_type == "function"
        assert safety_macro.target.metadata["function_name"] == "cleanup_files"
    
    def test_invalid_signals(self):
        """Test error handling for invalid signals."""
        comment = MacroComment(
            line_number=1,
            content="trap cleanup INVALID,SIGNAL",
            macro_type="safety",
            raw_line="# trap cleanup INVALID,SIGNAL"
        )
        
        target = MacroTarget(
            target_type="line",
            start_line=2,
            end_line=2,
            content='echo "cleanup"',
            metadata={}
        )
        
        with pytest.raises(ValueError, match="Invalid signal"):
            macro_parser.parse_safety_macro(comment, target)
    
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
    
    def test_trap_cleanup_line_transformation(self):
        """Test trap cleanup macro generates correct bash code for line target."""
        comment = MacroComment(
            line_number=1,
            content="trap cleanup",
            macro_type="safety",
            raw_line="# trap cleanup"
        )
        
        target = MacroTarget(
            target_type="line",
            start_line=2,
            end_line=2,
            content='echo "Cleaning up temp files"',
            metadata={}
        )
        
        safety_macro = macro_parser.parse_safety_macro(comment, target)
        transformation = safety_macro.generate_transformation()
        
        expected = '''# Trap cleanup handler
_cleanup_line_2() {
    local exit_code=$?
    echo "Cleaning up temp files"
    exit $exit_code
}

trap _cleanup_line_2 EXIT ERR INT TERM'''
        
        assert transformation == expected
    
    def test_trap_cleanup_function_transformation(self):
        """Test trap cleanup macro generates correct bash code for function target."""
        comment = MacroComment(
            line_number=1,
            content="trap cleanup",
            macro_type="safety",
            raw_line="# trap cleanup"
        )
        
        target = MacroTarget(
            target_type="function",
            start_line=2,
            end_line=5,
            content='''cleanup_files() {
    rm -f /tmp/tempfile
    echo "Cleanup complete"
}''',
            metadata={"function_name": "cleanup_files"}
        )
        
        safety_macro = macro_parser.parse_safety_macro(comment, target)
        transformation = safety_macro.generate_transformation()
        
        expected = '''# Trap cleanup from function cleanup_files
_cleanup_cleanup_files() {
    local exit_code=$?
    rm -f /tmp/tempfile
    echo "Cleanup complete"
    exit $exit_code
}

trap _cleanup_cleanup_files EXIT ERR INT TERM'''
        
        assert transformation == expected
    
    def test_trap_cleanup_custom_signals_transformation(self):
        """Test trap cleanup macro with custom signals."""
        comment = MacroComment(
            line_number=1,
            content="trap cleanup EXIT,INT",
            macro_type="safety",
            raw_line="# trap cleanup EXIT,INT"
        )
        
        target = MacroTarget(
            target_type="line",
            start_line=2,
            end_line=2,
            content='echo "Custom cleanup"',
            metadata={}
        )
        
        safety_macro = macro_parser.parse_safety_macro(comment, target)
        transformation = safety_macro.generate_transformation()
        
        expected = '''# Trap cleanup handler
_cleanup_line_2() {
    local exit_code=$?
    echo "Custom cleanup"
    exit $exit_code
}

trap _cleanup_line_2 EXIT INT'''
        
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
    
    def test_process_trap_cleanup_macro_with_line(self):
        """Test processing of trap cleanup macro with line target."""
        script = '''#!/bin/bash
# trap cleanup
echo "Cleaning up temp files"
echo "Hello $NAME!"'''
        
        result = macro_processor.process_macros(script)
        lines = result.split('\n')
        
        # Should have shebang, then echo, then trap setup replaces the cleanup line
        assert lines[0] == "#!/bin/bash"
        assert "_cleanup_line_2(" in result
        assert "trap _cleanup_line_2 EXIT ERR INT TERM" in result
        assert 'echo "Cleaning up temp files"' in result  # Should be in the trap function
        assert 'echo "Hello $NAME!"' in result
    
    def test_process_both_safety_macros(self):
        """Test processing both safety macros together."""
        script = '''#!/bin/bash
# set strict
# trap cleanup
rm -f /tmp/tempfile
echo "Hello $NAME!"'''
        
        result = macro_processor.process_macros(script)
        lines = result.split('\n')
        
        # Should have both macros processed
        assert "set -eou --pipefail" in result
        assert "_cleanup_line_3(" in result
        assert "trap _cleanup_line_3 EXIT ERR INT TERM" in result
        assert 'rm -f /tmp/tempfile' in result  # Should be in the trap function
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
# set strict
echo "Some code"
# trap cleanup
rm -f /tmp/cleanup_file
echo "More code"'''
        
        result = macro_processor.process_macros(script)
        lines = result.split('\n')
        
        # set strict should be at the top, trap should replace its target
        assert "set -eou --pipefail" in result
        assert "_cleanup_line_4(" in result
        assert "trap _cleanup_line_4 EXIT ERR INT TERM" in result
        assert 'rm -f /tmp/cleanup_file' in result
        assert 'echo "Some code"' in result
        assert 'echo "More code"' in result


class TestSafetyMacroValidation:
    """Test safety macro validation."""
    
    def test_validate_valid_safety_macros(self):
        """Test validation passes for valid safety macros."""
        script = '''#!/bin/bash
# set strict
# trap cleanup
echo "Cleanup action"
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
    
    def test_validate_trap_cleanup_without_target(self):
        """Test validation catches trap cleanup without target."""
        script = '''#!/bin/bash
# trap cleanup'''
        
        errors = macro_processor.validate_macros(script)
        assert len(errors) == 1
        assert "No target found for trap macro" in errors[0]
        assert "Line 2" in errors[0]