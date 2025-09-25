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


class ScriptMetadata(BaseModel):
    """Model for script-level metadata."""
    
    description: Optional[str] = Field(
        default=None,
        description="Script description from # Description: comment"
    )


class ArgumentInfo(BaseModel):
    """Model for a single named argument (flag) in the explain command output."""
    
    name: str = Field(description="The argument name (e.g., 'name', 'age')")
    type: str = Field(description="The argument type (str, int, float, bool, choice)")
    help: str = Field(description="Help text for the argument")
    default: Optional[str] = Field(default=None, description="Default value for the argument")
    required: bool = Field(description="Whether the argument is required")
    alias: Optional[str] = Field(default=None, description="Short alias for the argument (e.g., '-v')")
    choices: Optional[List[str]] = Field(default=None, description="Valid choices for choice type arguments")


class PositionalInfo(BaseModel):
    """Model for a positional argument in the explain command output."""
    
    name: str = Field(description="The positional argument name (e.g., 'ARG1', 'ARG2')")
    index: int = Field(description="The positional argument index (1, 2, etc.)")


class ScriptInterface(BaseModel):
    """Top-level model for the explain command JSON output."""
    
    description: Optional[str] = Field(default=None, description="Script description from metadata")
    arguments: List[ArgumentInfo] = Field(default_factory=list, description="List of named arguments")
    positionals: List[PositionalInfo] = Field(default_factory=list, description="List of positional arguments")
    varargs: bool = Field(default=False, description="Whether script uses varargs ($@ or $*)")