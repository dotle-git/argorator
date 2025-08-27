"""Pydantic models for argument annotations."""
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from .argument_types import BaseArgumentType


class ArgumentAnnotation(BaseModel):
    """Model for a single argument annotation."""
    
    type: str = Field(
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
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate that the type is supported."""
        from .argument_types import validate_type_name
        return validate_type_name(v)
    
    @field_validator('choices')
    @classmethod
    def validate_choices(cls, v: Optional[List[str]], info) -> Optional[List[str]]:
        """Validate that choices are only set for choice type."""
        if v is not None:
            type_value = info.data.get('type', 'str').lower()
            # Import here to avoid circular imports
            from .argument_types import get_type_handler
            try:
                handler = get_type_handler(type_value)
                # Check if this handler supports choices
                choice_type_names = ['choice', 'enum', 'select', 'option']
                
                # Allow choices if type is 'str' (will be auto-converted to 'choice' in post_init)
                # or if type is already a choice type
                if (type_value != 'str' and 
                    not any(name in handler.get_type_names() for name in choice_type_names)):
                    raise ValueError("choices can only be set for choice-type arguments")
            except ValueError as e:
                # If it's an unknown type error, let the type validator handle it
                if "Unknown argument type" in str(e):
                    pass
                else:
                    raise
        return v
    
    def model_post_init(self, __context) -> None:
        """Post-initialization validation."""
        # If choices are provided but type is str (the default), auto-convert to 'choice'
        # But don't auto-convert if user explicitly set a non-choice type
        if self.choices and self.type == 'str':
            # Only auto-convert from the default 'str' type, not explicitly set types
            self.type = 'choice'
    
    def get_type_handler(self) -> 'BaseArgumentType':
        """Get the type handler for this annotation."""
        from .argument_types import get_type_handler
        return get_type_handler(self.type)


class ScriptMetadata(BaseModel):
    """Model for script-level metadata."""
    
    description: Optional[str] = Field(
        default=None,
        description="Script description from # Description: comment"
    )