from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    difficulty_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    category: str = Field(..., min_length=2, max_length=60)
    estimated_hours: Optional[float] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    difficulty_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    category: Optional[str] = Field(None, min_length=2, max_length=60)
    estimated_hours: Optional[float] = None
    is_published: Optional[bool] = None


class ModuleCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=10)
    sort_order: int = Field(..., ge=0)


class ModuleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    content: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)


class ModuleResponse(BaseModel):
    module_id: UUID
    course_id: UUID
    title: str
    content: str
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class CourseResponse(BaseModel):
    course_id: UUID
    title: str
    description: str
    difficulty_level: str
    category: str
    estimated_hours: Optional[float]
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    modules: list[ModuleResponse] = []
    lab_count: int = 0
