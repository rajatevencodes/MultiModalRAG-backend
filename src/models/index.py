from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class ProjectCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(..., description="The name of the project")
    description: Optional[str] = Field(None, description="Project description")
