"""Pydantic models for argument annotations."""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ArgumentAnnotation(BaseModel):
    """Model for a single argument annotation."""
    
    type: Literal['str', 'int', 'float', 'bool', 'choice', 'file'] = Field(
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