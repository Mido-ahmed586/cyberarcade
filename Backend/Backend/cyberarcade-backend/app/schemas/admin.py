from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_courses: int
    published_courses: int
    total_labs: int
    active_lab_instances: int
    total_classes: int
    total_enrollments: int


class UserAdminResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    role: str
    is_active: bool
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern="^(student|instructor|admin|system_admin)$")


class StatusUpdateRequest(BaseModel):
    is_active: bool


class AuditLogResponse(BaseModel):
    log_id: int
    user_id: Optional[UUID]
    action: str
    target_type: Optional[str]
    target_id: Optional[UUID]
    metadata_: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True
