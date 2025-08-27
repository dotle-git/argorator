"""Argument type classes for handling different CLI argument types.

This module provides an object-oriented system for handling argument types,
replacing the previous string-based approach with extensible type classes.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from .models import ArgumentAnnotation


class BaseArgumentType(ABC):
    """Abstract base class for argument type handlers.
    
    Each argument type defines:
    - Type names/aliases it handles (e.g., "str", "string")
    - How to validate values
    - How to configure argparse for this type
    """
    
    type_names: List[str] = []  # Type names this handler supports
    
    @abstractmethod
    def validate_value(self, value: str, annotation: ArgumentAnnotation) -> str:
        """Validate and potentially transform a value.
        
        Args:
            value: The raw string value to validate
            annotation: The argument annotation containing additional constraints
            
        Returns:
            The validated/transformed value as a string
            
        Raises:
            ValueError: If the value is invalid for this type
        """
        pass
    
    @abstractmethod
    def get_argparse_type(self) -> Optional[Type]:
        """Get the Python type to use for argparse's 'type' parameter.
        
        Returns:
            Python type (int, float, str, etc.) or None for no conversion
        """
        pass
    
    def get_argparse_kwargs(self, annotation: ArgumentAnnotation) -> Dict[str, Any]:
        """Get argparse-specific configuration for this type.
        
        Args:
            annotation: The argument annotation
            
        Returns:
            Dictionary of kwargs for argparse.add_argument()
        """
        kwargs = {}
        
        # Set the type converter
        argparse_type = self.get_argparse_type()
        if argparse_type is not None:
            kwargs['type'] = argparse_type
            
        return kwargs
    
    @classmethod
    def get_type_names(cls) -> List[str]:
        """Get all type names/aliases this handler supports."""
        return cls.type_names.copy()


class StringType(BaseArgumentType):
    """Handler for string arguments."""
    
    type_names = ['str', 'string', 'text']
    
    def validate_value(self, value: str, annotation: ArgumentAnnotation) -> str:
        """String values are always valid, just return as-is."""
        return value
    
    def get_argparse_type(self) -> Optional[Type]:
        """Strings don't need type conversion in argparse."""
        return None  # argparse defaults to str


class IntType(BaseArgumentType):
    """Handler for integer arguments."""
    
    type_names = ['int', 'integer', 'number']
    
    def validate_value(self, value: str, annotation: ArgumentAnnotation) -> str:
        """Validate that the value can be converted to an integer."""
        try:
            int(value)
            return value
        except ValueError:
            raise ValueError(f"'{value}' is not a valid integer")
    
    def get_argparse_type(self) -> Optional[Type]:
        """Use int type for argparse conversion."""
        return int


class FloatType(BaseArgumentType):
    """Handler for float/decimal arguments."""
    
    type_names = ['float', 'decimal', 'real']
    
    def validate_value(self, value: str, annotation: ArgumentAnnotation) -> str:
        """Validate that the value can be converted to a float."""
        try:
            float(value)
            return value
        except ValueError:
            raise ValueError(f"'{value}' is not a valid decimal number")
    
    def get_argparse_type(self) -> Optional[Type]:
        """Use float type for argparse conversion."""
        return float


class BoolType(BaseArgumentType):
    """Handler for boolean arguments."""
    
    type_names = ['bool', 'boolean', 'flag']
    
    def validate_value(self, value: str, annotation: ArgumentAnnotation) -> str:
        """Validate and normalize boolean values."""
        value_lower = value.lower()
        if value_lower in ('true', '1', 'yes', 'on'):
            return 'true'
        elif value_lower in ('false', '0', 'no', 'off'):
            return 'false'
        else:
            raise ValueError(f"'{value}' is not a valid boolean (use true/false, yes/no, 1/0, on/off)")
    
    def get_argparse_type(self) -> Optional[Type]:
        """Boolean arguments use store_true/store_false actions, not type conversion."""
        return None
    
    def get_argparse_kwargs(self, annotation: ArgumentAnnotation) -> Dict[str, Any]:
        """Configure boolean argument with store_true/store_false action."""
        kwargs = super().get_argparse_kwargs(annotation)
        
        # Boolean arguments use action instead of type
        # Default to store_true (setting the flag enables it)
        kwargs['action'] = 'store_true'
        
        return kwargs


class ChoiceType(BaseArgumentType):
    """Handler for choice/enum arguments."""
    
    type_names = ['choice', 'enum', 'select', 'option']
    
    def validate_value(self, value: str, annotation: ArgumentAnnotation) -> str:
        """Validate that the value is one of the allowed choices."""
        if not annotation.choices:
            raise ValueError("Choice type requires 'choices' to be specified in annotation")
        
        if value not in annotation.choices:
            choices_str = ', '.join(annotation.choices)
            raise ValueError(f"'{value}' is not a valid choice. Options: {choices_str}")
        
        return value
    
    def get_argparse_type(self) -> Optional[Type]:
        """Choice arguments don't need type conversion."""
        return None
    
    def get_argparse_kwargs(self, annotation: ArgumentAnnotation) -> Dict[str, Any]:
        """Configure choice argument with choices constraint."""
        kwargs = super().get_argparse_kwargs(annotation)
        
        if annotation.choices:
            kwargs['choices'] = annotation.choices
            
        return kwargs


class FileType(BaseArgumentType):
    """Handler for file path arguments."""
    
    type_names = ['file', 'path', 'filepath']
    
    def validate_value(self, value: str, annotation: ArgumentAnnotation) -> str:
        """Validate that the value is a valid file path format."""
        try:
            # Just validate it's a valid path format, don't check existence
            # since the file might not exist yet (e.g., output files)
            Path(value)
            return value
        except (ValueError, OSError) as e:
            raise ValueError(f"'{value}' is not a valid file path: {e}")
    
    def get_argparse_type(self) -> Optional[Type]:
        """File paths are handled as strings."""
        return None


# Registry mapping type names to their handlers
TYPE_REGISTRY: Dict[str, BaseArgumentType] = {}


def _register_type_handler(handler: BaseArgumentType) -> None:
    """Register a type handler for all its type names."""
    for type_name in handler.get_type_names():
        TYPE_REGISTRY[type_name.lower()] = handler


def get_type_handler(type_name: str) -> BaseArgumentType:
    """Get the type handler for a given type name.
    
    Args:
        type_name: The type name (case-insensitive)
        
    Returns:
        The appropriate type handler
        
    Raises:
        ValueError: If the type name is not recognized
    """
    handler = TYPE_REGISTRY.get(type_name.lower())
    if handler is None:
        available_types = sorted(TYPE_REGISTRY.keys())
        raise ValueError(f"Unknown argument type '{type_name}'. Available types: {', '.join(available_types)}")
    return handler


def get_all_supported_types() -> List[str]:
    """Get a list of all supported type names."""
    return sorted(TYPE_REGISTRY.keys())


def validate_type_name(type_name: str) -> str:
    """Validate and normalize a type name.
    
    Args:
        type_name: The type name to validate
        
    Returns:
        The normalized type name
        
    Raises:
        ValueError: If the type name is not recognized
    """
    normalized = type_name.lower()
    if normalized not in TYPE_REGISTRY:
        available_types = sorted(TYPE_REGISTRY.keys())
        raise ValueError(f"Unknown argument type '{type_name}'. Available types: {', '.join(available_types)}")
    return normalized


# Initialize the registry with all built-in types
_register_type_handler(StringType())
_register_type_handler(IntType())
_register_type_handler(FloatType())
_register_type_handler(BoolType())
_register_type_handler(ChoiceType())
_register_type_handler(FileType())