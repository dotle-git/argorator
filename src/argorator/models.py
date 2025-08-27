"""Pydantic models for argument annotations."""
from abc import ABC, abstractmethod
from typing import Any, List, Literal, Optional, Set, Type
from pydantic import BaseModel, Field, field_validator


class BaseArgumentType(ABC):
    """Base class for argument types defining the interface for type handling."""
    
    @property
    @abstractmethod
    def type_names(self) -> Set[str]:
        """Return the set of strings that identify this type in annotations."""
        pass
    
    @property
    @abstractmethod
    def argparse_type(self) -> Optional[Type]:
        """Return the type converter function for argparse."""
        pass
    
    @property
    @abstractmethod
    def type_id(self) -> str:
        """Return the canonical type identifier."""
        pass
    
    def validate_value(self, value: str) -> Any:
        """Validate and convert a string value. Override for custom validation."""
        if self.argparse_type is None:
            return value
        return self.argparse_type(value)
    
    def validate_annotation_data(self, annotation_data: dict) -> None:
        """Validate annotation-specific data. Override for type-specific validation."""
        pass


class StringType(BaseArgumentType):
    """Handler for string/text arguments."""
    
    @property
    def type_names(self) -> Set[str]:
        return {'str', 'string'}
    
    @property
    def argparse_type(self) -> Optional[Type]:
        return str
    
    @property
    def type_id(self) -> str:
        return 'str'


class IntType(BaseArgumentType):
    """Handler for integer arguments."""
    
    @property
    def type_names(self) -> Set[str]:
        return {'int', 'integer'}
    
    @property
    def argparse_type(self) -> Optional[Type]:
        return int
    
    @property
    def type_id(self) -> str:
        return 'int'


class FloatType(BaseArgumentType):
    """Handler for float arguments."""
    
    @property
    def type_names(self) -> Set[str]:
        return {'float', 'number', 'decimal'}
    
    @property
    def argparse_type(self) -> Optional[Type]:
        return float
    
    @property
    def type_id(self) -> str:
        return 'float'


class BoolType(BaseArgumentType):
    """Handler for boolean arguments."""
    
    @property
    def type_names(self) -> Set[str]:
        return {'bool', 'boolean'}
    
    @property
    def argparse_type(self) -> Optional[Type]:
        return None  # Booleans use store_true/store_false actions
    
    @property
    def type_id(self) -> str:
        return 'bool'
    
    def validate_value(self, value: str) -> bool:
        """Convert string to boolean."""
        return value.lower() in ('true', '1', 'yes', 'y')


class ChoiceType(BaseArgumentType):
    """Handler for choice arguments."""
    
    @property
    def type_names(self) -> Set[str]:
        return {'choice', 'enum', 'select'}
    
    @property
    def argparse_type(self) -> Optional[Type]:
        return str
    
    @property
    def type_id(self) -> str:
        return 'choice'
    
    def validate_annotation_data(self, annotation_data: dict) -> None:
        """Validate that choices are provided for choice type."""
        if not annotation_data.get('choices'):
            raise ValueError("choices must be provided for choice type")


# Registry of all argument types
ARGUMENT_TYPES = [
    StringType(),
    IntType(),
    FloatType(),
    BoolType(),
    ChoiceType(),
]

# Mapping from type name to handler
TYPE_NAME_TO_HANDLER = {}
for handler in ARGUMENT_TYPES:
    for name in handler.type_names:
        TYPE_NAME_TO_HANDLER[name.lower()] = handler

# Mapping from type_id to handler
TYPE_ID_TO_HANDLER = {handler.type_id: handler for handler in ARGUMENT_TYPES}


def get_argument_type_handler(type_name: str) -> BaseArgumentType:
    """Get the argument type handler for a given type name."""
    handler = TYPE_NAME_TO_HANDLER.get(type_name.lower())
    if handler is None:
        # Default to string type for unknown types
        return TYPE_ID_TO_HANDLER['str']
    return handler


class ArgumentAnnotation(BaseModel):
    """Model for a single argument annotation."""
    
    type: Literal['str', 'int', 'float', 'bool', 'choice'] = Field(
        default='str',
        description="The argument type"
    )
    help: str = Field(
        default='',
        description="Help text for the argument"
    )
    default: Optional[str] = Field(
        default=None,
        description="Default value for the argument"
    )
    alias: Optional[str] = Field(
        default=None,
        description="Short alias for the argument (e.g., '-v')"
    )
    choices: Optional[List[str]] = Field(
        default=None,
        description="Valid choices for choice type arguments"
    )
    
    @field_validator('alias')
    @classmethod
    def validate_alias(cls, v: Optional[str]) -> Optional[str]:
        """Validate that alias starts with a single dash."""
        if v is not None and not v.startswith('-'):
            # Prepend dash if not present
            return f'-{v}'
        return v
    
    @field_validator('choices')
    @classmethod
    def validate_choices(cls, v: Optional[List[str]], info) -> Optional[List[str]]:
        """Validate that choices are only set for choice type."""
        if v is not None and info.data.get('type') != 'choice':
            raise ValueError("choices can only be set for type='choice'")
        return v
    
    def model_post_init(self, __context) -> None:
        """Post-initialization validation."""
        # If choices are provided but type is not set, set type to 'choice'
        if self.choices and self.type != 'choice':
            self.type = 'choice'
    
    def get_type_handler(self) -> BaseArgumentType:
        """Get the appropriate type handler for this annotation."""
        return get_argument_type_handler(self.type)