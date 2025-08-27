"""Tests for the new argument type system."""
import pytest
from argparse import ArgumentParser

from argorator.argument_types import (
    BaseArgumentType, StringType, IntType, FloatType, BoolType, 
    ChoiceType, FileType, get_type_handler, get_all_supported_types,
    validate_type_name, TYPE_REGISTRY
)
from argorator.models import ArgumentAnnotation


class TestTypeRegistry:
    """Test the type registry system."""
    
    def test_all_types_registered(self):
        """Test that all expected types are registered."""
        types = get_all_supported_types()
        
        # Check that basic types are present
        assert 'str' in types
        assert 'int' in types  
        assert 'float' in types
        assert 'bool' in types
        assert 'choice' in types
        assert 'file' in types
        
        # Check that aliases are present
        assert 'string' in types
        assert 'integer' in types
        assert 'boolean' in types
        assert 'decimal' in types
    
    def test_get_type_handler_case_insensitive(self):
        """Test that type handler lookup is case insensitive."""
        assert isinstance(get_type_handler('STR'), StringType)
        assert isinstance(get_type_handler('Int'), IntType)
        assert isinstance(get_type_handler('BOOL'), BoolType)
    
    def test_get_type_handler_unknown_type(self):
        """Test that unknown types raise ValueError."""
        with pytest.raises(ValueError, match="Unknown argument type 'unknown'"):
            get_type_handler('unknown')
    
    def test_validate_type_name(self):
        """Test type name validation."""
        assert validate_type_name('str') == 'str'
        assert validate_type_name('STRING') == 'string'
        assert validate_type_name('Int') == 'int'
        
        with pytest.raises(ValueError):
            validate_type_name('invalid_type')


class TestStringType:
    """Test StringType handler."""
    
    def test_type_names(self):
        """Test StringType supports expected type names."""
        handler = StringType()
        assert 'str' in handler.get_type_names()
        assert 'string' in handler.get_type_names()
        assert 'text' in handler.get_type_names()
    
    def test_validate_value(self):
        """Test string validation always succeeds."""
        handler = StringType()
        annotation = ArgumentAnnotation(type='str')
        
        assert handler.validate_value('hello', annotation) == 'hello'
        assert handler.validate_value('123', annotation) == '123'
        assert handler.validate_value('', annotation) == ''
    
    def test_argparse_type(self):
        """Test argparse type is None (default string handling)."""
        handler = StringType()
        assert handler.get_argparse_type() is None
    
    def test_argparse_kwargs(self):
        """Test argparse kwargs for strings."""
        handler = StringType()
        annotation = ArgumentAnnotation(type='str')
        kwargs = handler.get_argparse_kwargs(annotation)
        
        # String type shouldn't add any special kwargs
        assert kwargs == {}


class TestIntType:
    """Test IntType handler."""
    
    def test_type_names(self):
        """Test IntType supports expected type names."""
        handler = IntType()
        assert 'int' in handler.get_type_names()
        assert 'integer' in handler.get_type_names()
        assert 'number' in handler.get_type_names()
    
    def test_validate_value_valid(self):
        """Test integer validation succeeds for valid integers."""
        handler = IntType()
        annotation = ArgumentAnnotation(type='int')
        
        assert handler.validate_value('123', annotation) == '123'
        assert handler.validate_value('-456', annotation) == '-456'
        assert handler.validate_value('0', annotation) == '0'
    
    def test_validate_value_invalid(self):
        """Test integer validation fails for invalid integers."""
        handler = IntType()
        annotation = ArgumentAnnotation(type='int')
        
        with pytest.raises(ValueError, match="not a valid integer"):
            handler.validate_value('abc', annotation)
        
        with pytest.raises(ValueError, match="not a valid integer"):
            handler.validate_value('12.34', annotation)
    
    def test_argparse_type(self):
        """Test argparse type is int."""
        handler = IntType()
        assert handler.get_argparse_type() is int
    
    def test_argparse_kwargs(self):
        """Test argparse kwargs for integers."""
        handler = IntType()
        annotation = ArgumentAnnotation(type='int')
        kwargs = handler.get_argparse_kwargs(annotation)
        
        assert kwargs['type'] is int


class TestFloatType:
    """Test FloatType handler."""
    
    def test_type_names(self):
        """Test FloatType supports expected type names."""
        handler = FloatType()
        assert 'float' in handler.get_type_names()
        assert 'decimal' in handler.get_type_names()
        assert 'real' in handler.get_type_names()
    
    def test_validate_value_valid(self):
        """Test float validation succeeds for valid floats."""
        handler = FloatType()
        annotation = ArgumentAnnotation(type='float')
        
        assert handler.validate_value('123.45', annotation) == '123.45'
        assert handler.validate_value('-67.89', annotation) == '-67.89'
        assert handler.validate_value('0.0', annotation) == '0.0'
        assert handler.validate_value('123', annotation) == '123'  # int is valid float
    
    def test_validate_value_invalid(self):
        """Test float validation fails for invalid floats."""
        handler = FloatType()
        annotation = ArgumentAnnotation(type='float')
        
        with pytest.raises(ValueError, match="not a valid decimal number"):
            handler.validate_value('abc', annotation)
    
    def test_argparse_type(self):
        """Test argparse type is float."""
        handler = FloatType()
        assert handler.get_argparse_type() is float


class TestBoolType:
    """Test BoolType handler."""
    
    def test_type_names(self):
        """Test BoolType supports expected type names."""
        handler = BoolType()
        assert 'bool' in handler.get_type_names()
        assert 'boolean' in handler.get_type_names()
        assert 'flag' in handler.get_type_names()
    
    def test_validate_value_true(self):
        """Test boolean validation for true values."""
        handler = BoolType()
        annotation = ArgumentAnnotation(type='bool')
        
        for value in ['true', 'True', 'TRUE', '1', 'yes', 'on']:
            assert handler.validate_value(value, annotation) == 'true'
    
    def test_validate_value_false(self):
        """Test boolean validation for false values."""
        handler = BoolType()
        annotation = ArgumentAnnotation(type='bool')
        
        for value in ['false', 'False', 'FALSE', '0', 'no', 'off']:
            assert handler.validate_value(value, annotation) == 'false'
    
    def test_validate_value_invalid(self):
        """Test boolean validation fails for invalid values."""
        handler = BoolType()
        annotation = ArgumentAnnotation(type='bool')
        
        with pytest.raises(ValueError, match="not a valid boolean"):
            handler.validate_value('maybe', annotation)
    
    def test_argparse_type(self):
        """Test argparse type is None for boolean (uses actions)."""
        handler = BoolType()
        assert handler.get_argparse_type() is None
    
    def test_argparse_kwargs(self):
        """Test argparse kwargs for boolean."""
        handler = BoolType()
        annotation = ArgumentAnnotation(type='bool')
        kwargs = handler.get_argparse_kwargs(annotation)
        
        assert kwargs['action'] == 'store_true'


class TestChoiceType:
    """Test ChoiceType handler."""
    
    def test_type_names(self):
        """Test ChoiceType supports expected type names."""
        handler = ChoiceType()
        assert 'choice' in handler.get_type_names()
        assert 'enum' in handler.get_type_names()
        assert 'select' in handler.get_type_names()
        assert 'option' in handler.get_type_names()
    
    def test_validate_value_valid(self):
        """Test choice validation succeeds for valid choices."""
        handler = ChoiceType()
        annotation = ArgumentAnnotation(type='choice', choices=['a', 'b', 'c'])
        
        assert handler.validate_value('a', annotation) == 'a'
        assert handler.validate_value('b', annotation) == 'b'
        assert handler.validate_value('c', annotation) == 'c'
    
    def test_validate_value_invalid_choice(self):
        """Test choice validation fails for invalid choices."""
        handler = ChoiceType()
        annotation = ArgumentAnnotation(type='choice', choices=['a', 'b', 'c'])
        
        with pytest.raises(ValueError, match="not a valid choice"):
            handler.validate_value('d', annotation)
    
    def test_validate_value_no_choices(self):
        """Test choice validation fails when no choices defined."""
        handler = ChoiceType()
        annotation = ArgumentAnnotation(type='choice')
        
        with pytest.raises(ValueError, match="requires 'choices' to be specified"):
            handler.validate_value('a', annotation)
    
    def test_argparse_kwargs(self):
        """Test argparse kwargs for choice."""
        handler = ChoiceType()
        annotation = ArgumentAnnotation(type='choice', choices=['a', 'b', 'c'])
        kwargs = handler.get_argparse_kwargs(annotation)
        
        assert kwargs['choices'] == ['a', 'b', 'c']


class TestFileType:
    """Test FileType handler."""
    
    def test_type_names(self):
        """Test FileType supports expected type names."""
        handler = FileType()
        assert 'file' in handler.get_type_names()
        assert 'path' in handler.get_type_names()
        assert 'filepath' in handler.get_type_names()
    
    def test_validate_value_valid(self):
        """Test file validation succeeds for valid paths."""
        handler = FileType()
        annotation = ArgumentAnnotation(type='file')
        
        assert handler.validate_value('/path/to/file.txt', annotation) == '/path/to/file.txt'
        assert handler.validate_value('relative/path.txt', annotation) == 'relative/path.txt'
        assert handler.validate_value('file.txt', annotation) == 'file.txt'
    
    def test_argparse_type(self):
        """Test argparse type is None (files handled as strings)."""
        handler = FileType()
        assert handler.get_argparse_type() is None


class TestArgumentAnnotationIntegration:
    """Test integration between ArgumentAnnotation and type system."""
    
    def test_type_validation(self):
        """Test that ArgumentAnnotation validates types using the type system."""
        # Valid types should work
        annotation = ArgumentAnnotation(type='int')
        assert annotation.type == 'int'
        
        annotation = ArgumentAnnotation(type='STRING')  # Case insensitive
        assert annotation.type == 'string'
        
        # Invalid types should raise ValueError
        with pytest.raises(ValueError):
            ArgumentAnnotation(type='invalid_type')
    
    def test_get_type_handler(self):
        """Test that ArgumentAnnotation can get its type handler."""
        annotation = ArgumentAnnotation(type='int')
        handler = annotation.get_type_handler()
        assert isinstance(handler, IntType)
        
        annotation = ArgumentAnnotation(type='choice', choices=['a', 'b'])
        handler = annotation.get_type_handler()
        assert isinstance(handler, ChoiceType)
    
    def test_choices_validation(self):
        """Test that choices validation works with type system."""
        # Choice type with choices should work
        annotation = ArgumentAnnotation(type='choice', choices=['a', 'b', 'c'])
        assert annotation.type == 'choice'
        assert annotation.choices == ['a', 'b', 'c']
        
        # Non-choice type with choices should fail
        with pytest.raises(ValueError, match="choices can only be set"):
            ArgumentAnnotation(type='int', choices=['1', '2', '3'])
    
    def test_auto_choice_type(self):
        """Test that providing choices automatically sets type to choice."""
        annotation = ArgumentAnnotation(choices=['a', 'b', 'c'])
        assert annotation.type == 'choice'
        assert annotation.choices == ['a', 'b', 'c']


class TestNewTypeAliases:
    """Test that new type aliases work correctly."""
    
    def test_string_aliases(self):
        """Test string type aliases."""
        for alias in ['string', 'text']:
            handler = get_type_handler(alias)
            assert isinstance(handler, StringType)
    
    def test_int_aliases(self):
        """Test integer type aliases.""" 
        for alias in ['integer', 'number']:
            handler = get_type_handler(alias)
            assert isinstance(handler, IntType)
    
    def test_float_aliases(self):
        """Test float type aliases."""
        for alias in ['decimal', 'real']:
            handler = get_type_handler(alias)
            assert isinstance(handler, FloatType)
    
    def test_bool_aliases(self):
        """Test boolean type aliases."""
        for alias in ['boolean', 'flag']:
            handler = get_type_handler(alias)
            assert isinstance(handler, BoolType)
    
    def test_choice_aliases(self):
        """Test choice type aliases."""
        for alias in ['enum', 'select', 'option']:
            handler = get_type_handler(alias)
            assert isinstance(handler, ChoiceType)
    
    def test_file_aliases(self):
        """Test file type aliases."""
        for alias in ['path', 'filepath']:
            handler = get_type_handler(alias)
            assert isinstance(handler, FileType)


class TestBackwardCompatibility:
    """Test that the new system maintains backward compatibility."""
    
    def test_old_type_names_still_work(self):
        """Test that all old type names from the Literal still work."""
        old_types = ['str', 'int', 'float', 'bool', 'choice', 'file']
        
        for old_type in old_types:
            # Should not raise exception
            handler = get_type_handler(old_type)
            assert handler is not None
            
            # Should work in ArgumentAnnotation
            annotation = ArgumentAnnotation(type=old_type)
            assert annotation.type == old_type
    
    def test_get_type_converter_still_works(self):
        """Test that the deprecated get_type_converter function still works."""
        from argorator.transformers import get_type_converter
        
        assert get_type_converter('int') is int
        assert get_type_converter('float') is float
        assert get_type_converter('str') is str
        assert get_type_converter('bool') is str  # bool uses actions, not type
        assert get_type_converter('invalid') is str  # fallback to str


if __name__ == '__main__':
    pytest.main([__file__])