from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List, Any


class LevelResponse(BaseModel):
    level_id: int
    min_xp: int
    title: str

    class Config:
        from_attributes = True


class XPLogResponse(BaseModel):
    log_id: UUID
    amount: int
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class BadgeResponse(BaseModel):
    badge_id: UUID
    slug: str
    name: str
    description: str
    icon: str
    rarity: str
    category: str
    xp_reward: int

    class Config:
        from_attributes = True


class UserBadgeResponse(BaseModel):
    badge: BadgeResponse
    awarded_at: datetime
    seen: bool

    class Config:
        from_attributes = True


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_active_date: Optional[str] = None
    total_active_days: int


class UserXPResponse(BaseModel):
    total_xp: int
    current_level: int
    level_title: str
    xp_to_next_level: int
    progress_pct: int


class GamificationProfileResponse(BaseModel):
    xp: UserXPResponse
    streak: StreakResponse
    badges: List[Any]
    labs_completed: int
    courses_completed: int
    tasks_completed: int


class TaskRewardResponse(BaseModel):
    xp_gained: int = 0
    level_up: bool = False
    new_level: Optional[int] = None
    new_level_title: Optional[str] = None
    new_badges: List[Any] = []


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    full_name: str
    total_xp: int
    current_level: int
    level_title: str
    labs_completed: int
    current_streak: int


class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total: int
    my_rank: Optional[int] = None


class ActivityDay(BaseModel):
    date: str
    count: int
