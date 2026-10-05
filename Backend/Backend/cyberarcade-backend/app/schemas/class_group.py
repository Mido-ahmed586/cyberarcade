from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class ClassCreate(BaseModel):
    course_id: UUID
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    max_students: Optional[int] = Field(None, ge=1, le=500)


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    max_students: Optional[int] = Field(None, ge=1, le=500)
    is_active: Optional[bool] = None


class JoinClassRequest(BaseModel):
    class_code: str = Field(..., min_length=3, max_length=20)


class ClassResponse(BaseModel):
    class_id: UUID
    class_code: str
    name: str
    description: Optional[str]
    course_id: UUID
    instructor_id: UUID
    max_students: Optional[int]
    is_active: bool
    created_at: datetime
    student_count: int = 0

    class Config:
        from_attributes = True


class EnrollmentResponse(BaseModel):
    enrollment_id: UUID
    class_id: UUID
    student_id: UUID
    enrolled_at: datetime

    class Config:
        from_attributes = True


class StudentProgressReport(BaseModel):
    student_id: UUID
    student_name: str
    tasks_completed: int
    tasks_auto_solved: int
    total_tasks_attempted: int
    total_hints_used: int
