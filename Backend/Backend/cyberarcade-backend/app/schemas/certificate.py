from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional


class CertificateOut(BaseModel):
    certificate_id: uuid.UUID
    serial_number: str
    student_name: str
    course_name: str
    course_id: uuid.UUID
    issued_at: datetime
    verification_status: str

    model_config = {"from_attributes": True}


class CertificateVerifyResponse(BaseModel):
    valid: bool
    student_name: Optional[str] = None
    course_name: Optional[str] = None
    issued_at: Optional[datetime] = None
    serial_number: Optional[str] = None
    certificate_id: Optional[str] = None
    message: Optional[str] = None


class CourseCompletionStatus(BaseModel):
    course_id: uuid.UUID
    course_name: str
    total_tasks: int
    completed_tasks: int
    is_complete: bool
    certificate: Optional[CertificateOut] = None
