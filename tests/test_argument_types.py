"""Tests for the new argument type class system."""
import pytest
from argorator.models import (
    BaseArgumentType, StringType, IntType, FloatType, BoolType, ChoiceType,
    get_argument_type_handler, TYPE_NAME_TO_HANDLER, TYPE_ID_TO_HANDLER,
    ArgumentAnnotation
)


class TestArgumentTypeRegistry:
    """Test the argument type registry functionality."""
    
    def test_all_types_registered(self):
        """Test that all type classes are properly registered."""
        expected_type_ids = {'str', 'int', 'float', 'bool', 'choice'}
        actual_type_ids = set(TYPE_ID_TO_HANDLER.keys())
        assert actual_type_ids == expected_type_ids
    
    def test_type_name_mapping(self):
        """Test that type names map correctly to handlers."""
        # String type names
        assert TYPE_NAME_TO_HANDLER['str'].type_id == 'str'
        assert TYPE_NAME_TO_HANDLER['string'].type_id == 'str'
        
        # Int type names
        assert TYPE_NAME_TO_HANDLER['int'].type_id == 'int'
        assert TYPE_NAME_TO_HANDLER['integer'].type_id == 'int'
        
        # Float type names
        assert TYPE_NAME_TO_HANDLER['float'].type_id == 'float'
        assert TYPE_NAME_TO_HANDLER['number'].type_id == 'float'
        assert TYPE_NAME_TO_HANDLER['decimal'].type_id == 'float'
        
        # Bool type names
        assert TYPE_NAME_TO_HANDLER['bool'].type_id == 'bool'
        assert TYPE_NAME_TO_HANDLER['boolean'].type_id == 'bool'
        
        # Choice type names
        assert TYPE_NAME_TO_HANDLER['choice'].type_id == 'choice'
        assert TYPE_NAME_TO_HANDLER['enum'].type_id == 'choice'
        assert TYPE_NAME_TO_HANDLER['select'].type_id == 'choice'
    
    def test_get_argument_type_handler(self):
        """Test the get_argument_type_handler function."""
        # Known types
        assert get_argument_type_handler('str').type_id == 'str'
        assert get_argument_type_handler('INT').type_id == 'int'  # Case insensitive
        assert get_argument_type_handler('Float').type_id == 'float'
        
        # Unknown type defaults to string
        assert get_argument_type_handler('unknown').type_id == 'str'
        assert get_argument_type_handler('').type_id == 'str'


class TestStringType:
    """Test StringType functionality."""
    
    def test_properties(self):
        """Test StringType properties."""
        string_type = StringType()
        assert string_type.type_id == 'str'
        assert string_type.argparse_type == str
        assert 'str' in string_type.type_names
        assert 'string' in string_type.type_names
    
    def test_validate_value(self):
        """Test StringType value validation."""
        string_type = StringType()
        assert string_type.validate_value('hello') == 'hello'
        assert string_type.validate_value('123') == '123'


class TestIntType:
    """Test IntType functionality."""
    
    def test_properties(self):
        """Test IntType properties."""
        int_type = IntType()
        assert int_type.type_id == 'int'
        assert int_type.argparse_type == int
        assert 'int' in int_type.type_names
        assert 'integer' in int_type.type_names
    
    def test_validate_value(self):
        """Test IntType value validation."""
        int_type = IntType()
        assert int_type.validate_value('123') == 123
        assert int_type.validate_value('-456') == -456
        
        with pytest.raises(ValueError):
            int_type.validate_value('not_a_number')


class TestFloatType:
    """Test FloatType functionality."""
    
    def test_properties(self):
        """Test FloatType properties."""
        float_type = FloatType()
        assert float_type.type_id == 'float'
        assert float_type.argparse_type == float
        assert 'float' in float_type.type_names
        assert 'number' in float_type.type_names
        assert 'decimal' in float_type.type_names
    
    def test_validate_value(self):
        """Test FloatType value validation."""
        float_type = FloatType()
        assert float_type.validate_value('123.45') == 123.45
        assert float_type.validate_value('-67.89') == -67.89
        assert float_type.validate_value('123') == 123.0
        
        with pytest.raises(ValueError):
            float_type.validate_value('not_a_number')


class TestBoolType:
    """Test BoolType functionality."""
    
    def test_properties(self):
        """Test BoolType properties."""
        bool_type = BoolType()
        assert bool_type.type_id == 'bool'
        assert bool_type.argparse_type is None  # Booleans use store_true/false
        assert 'bool' in bool_type.type_names
        assert 'boolean' in bool_type.type_names
    
    def test_validate_value(self):
        """Test BoolType value validation."""
        bool_type = BoolType()
        
        # True values
        assert bool_type.validate_value('true') is True
        assert bool_type.validate_value('TRUE') is True
        assert bool_type.validate_value('1') is True
        assert bool_type.validate_value('yes') is True
        assert bool_type.validate_value('y') is True
        
        # False values
        assert bool_type.validate_value('false') is False
        assert bool_type.validate_value('FALSE') is False
        assert bool_type.validate_value('0') is False
        assert bool_type.validate_value('no') is False
        assert bool_type.validate_value('anything_else') is False


class TestChoiceType:
    """Test ChoiceType functionality."""
    
    def test_properties(self):
        """Test ChoiceType properties."""
        choice_type = ChoiceType()
        assert choice_type.type_id == 'choice'
        assert choice_type.argparse_type == str
        assert 'choice' in choice_type.type_names
        assert 'enum' in choice_type.type_names
        assert 'select' in choice_type.type_names
    
    def test_validate_annotation_data(self):
        """Test ChoiceType annotation validation."""
        choice_type = ChoiceType()
        
        # Valid choice data
        valid_data = {'choices': ['option1', 'option2']}
        choice_type.validate_annotation_data(valid_data)  # Should not raise
        
        # Invalid choice data (no choices)
        invalid_data = {}
        with pytest.raises(ValueError, match="choices must be provided"):
            choice_type.validate_annotation_data(invalid_data)
        
        # Invalid choice data (empty choices)
        invalid_data2 = {'choices': []}
        with pytest.raises(ValueError, match="choices must be provided"):
            choice_type.validate_annotation_data(invalid_data2)


class TestArgumentAnnotationIntegration:
    """Test integration of ArgumentAnnotation with the new type system."""
    
    def test_get_type_handler(self):
        """Test ArgumentAnnotation.get_type_handler() method."""
        # String annotation
        str_annotation = ArgumentAnnotation(type='str', help='String param')
        assert str_annotation.get_type_handler().type_id == 'str'
        
        # Int annotation
        int_annotation = ArgumentAnnotation(type='int', help='Int param')
        assert int_annotation.get_type_handler().type_id == 'int'
        
        # Bool annotation
        bool_annotation = ArgumentAnnotation(type='bool', help='Bool param')
        assert bool_annotation.get_type_handler().type_id == 'bool'
        
        # Choice annotation
        choice_annotation = ArgumentAnnotation(
            type='choice', 
            help='Choice param',
            choices=['opt1', 'opt2']
        )
        assert choice_annotation.get_type_handler().type_id == 'choice'
    
    def test_backward_compatibility(self):
        """Test that existing annotation creation still works."""
        # This should work exactly as before
        annotation = ArgumentAnnotation(
            type='int',
            help='Port number',
            default='8080'
        )
        assert annotation.type == 'int'
        assert annotation.help == 'Port number'
        assert annotation.default == '8080'
        assert annotation.get_type_handler().type_id == 'int'


class TestNewTypeNameSupport:
    """Test that new type names are supported."""
    
    def test_integer_alias(self):
        """Test that 'integer' is recognized as int type."""
        handler = get_argument_type_handler('integer')
        assert handler.type_id == 'int'
        assert handler.argparse_type == int
    
    def test_number_alias(self):
        """Test that 'number' is recognized as float type."""
        handler = get_argument_type_handler('number')
        assert handler.type_id == 'float'
        assert handler.argparse_type == float
    
    def test_decimal_alias(self):
        """Test that 'decimal' is recognized as float type."""
        handler = get_argument_type_handler('decimal')
        assert handler.type_id == 'float'
        assert handler.argparse_type == float
    
    def test_boolean_alias(self):
        """Test that 'boolean' is recognized as bool type."""
        handler = get_argument_type_handler('boolean')
        assert handler.type_id == 'bool'
        assert handler.argparse_type is None
    
    def test_enum_alias(self):
        """Test that 'enum' is recognized as choice type."""
        handler = get_argument_type_handler('enum')
        assert handler.type_id == 'choice'
        assert handler.argparse_type == str
    
    def test_select_alias(self):
        """Test that 'select' is recognized as choice type."""
        handler = get_argument_type_handler('select')
        assert handler.type_id == 'choice'
        assert handler.argparse_type == str