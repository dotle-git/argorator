"""Pydantic models for argument annotations."""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


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
        """Validate short alias formatting and reserved names.

        Rules:
        - If provided without a dash, prepend a single '-'
        - Must be exactly a single-dash followed by one non-whitespace character
        - '-h' is reserved for help and cannot be used
        """
        if v is None:
            return v
        alias = v if v.startswith('-') else f'-{v}'
        # Disallow whitespace and multi-character long-style forms
        if len(alias) != 2 or not alias.startswith('-') or alias[1].isspace():
            raise ValueError("alias must be a short option like '-v'")
        if alias == '-h':
            raise ValueError("alias '-h' is reserved for help")
        return alias
    
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