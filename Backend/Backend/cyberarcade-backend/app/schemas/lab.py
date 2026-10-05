from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class LabCreate(BaseModel):
    course_id: UUID
    module_id: Optional[UUID] = None
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    difficulty: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    docker_compose_config: dict
    has_auto_solve: bool = False
    max_duration_minutes: int = Field(120, ge=10, le=480)
    sort_order: int = Field(0, ge=0)


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    instructions: str = Field(..., min_length=10)
    expected_answer: Optional[str] = None
    autosolve_commands: list[str] = Field(default_factory=list)
    sort_order: int = Field(..., ge=0)


class HintCreate(BaseModel):
    hint_text: str = Field(..., min_length=5)
    hint_order: int = Field(..., ge=1)
    delay_minutes: int = Field(0, ge=0, le=60)


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=500)


class HintResponse(BaseModel):
    hint_id: UUID
    hint_order: int
    hint_text: str
    delay_minutes: int

    class Config:
        from_attributes = True


class HintAvailability(BaseModel):
    is_available: bool
    hint: Optional[HintResponse] = None
    seconds_remaining: int = 0
    total_hints: int
    hints_used: int
    global_cooldown_ends_at: Optional[str] = None  # ISO-8601 UTC — shared across all tasks in the lab


class RevealedHintsResponse(BaseModel):
    hints: list[HintResponse]
    hints_used: int
    total_hints: int


class GlobalCooldownResponse(BaseModel):
    seconds_remaining: int = 0
    global_cooldown_ends_at: Optional[str] = None  # ISO-8601 UTC


class TaskResponse(BaseModel):
    task_id: UUID
    lab_id: UUID
    title: str
    instructions: str
    sort_order: int
    hint_count: int = 0
    has_autosolve: bool = False

    class Config:
        from_attributes = True


class TaskProgressResponse(BaseModel):
    task_id: UUID
    status: str
    submitted_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    hints_used: int = 0
    auto_solve_used: bool = False


class LabProgressResponse(BaseModel):
    lab_id: UUID
    tasks: list[TaskProgressResponse]
    completed_count: int
    total_count: int
    percent: int


class CourseProgressResponse(BaseModel):
    course_id: UUID
    completed_labs: int
    total_labs: int
    percent: int
    lab_statuses: dict  # lab_id -> "completed" | "in_progress" | "not_started"


class LabResponse(BaseModel):
    lab_id: UUID
    course_id: UUID
    title: str
    description: str
    difficulty: str
    has_auto_solve: bool
    max_duration_minutes: int
    sort_order: int
    is_published: bool
    docker_compose_config: dict
    created_at: datetime

    class Config:
        from_attributes = True


class LabDetailResponse(LabResponse):
    runtime: dict | None = None
    terminal_type: str | None = None
    tasks: list[TaskResponse] = []


class LabInstanceResponse(BaseModel):
    instance_id: UUID
    lab_id: UUID
    status: str
    guacamole_connection_id: Optional[str]
    started_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    status: str
    message: str
    xp_gained: int = 0
    level_up: bool = False
    new_level: Optional[int] = None
    new_level_title: Optional[str] = None
    new_badges: list = []
