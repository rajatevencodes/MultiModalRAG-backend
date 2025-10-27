from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class Project(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str = Field(..., description="The name of the project")
    description: Optional[str] = Field(None, description="Project description")
    clerk_id: str = Field(..., description="The clerk ID of the project")
    created_at: datetime
