from datetime import datetime
from pydantic import BaseModel, Field


# PUBLIC_INTERFACE
class ClassCreate(BaseModel):
    """Create a class type."""
    title: str = Field(..., description="Class title")
    description: str | None = Field(default=None, description="Class description")
    capacity: int = Field(default=20, ge=0, description="Default capacity")


# PUBLIC_INTERFACE
class ClassUpdate(BaseModel):
    """Update fields for a class type."""
    title: str | None = None
    description: str | None = None
    capacity: int | None = None


# PUBLIC_INTERFACE
class ClassOut(BaseModel):
    """Response model for a class."""
    id: int
    title: str
    description: str | None
    capacity: int

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE
class ClassSessionCreate(BaseModel):
    """Create a class session."""
    class_id: int
    start_time: datetime
    end_time: datetime
    capacity: int


# PUBLIC_INTERFACE
class ClassSessionOut(BaseModel):
    """Response for a class session."""
    id: int
    class_id: int
    start_time: datetime
    end_time: datetime
    capacity: int
    spots_remaining: int

    class Config:
        from_attributes = True
