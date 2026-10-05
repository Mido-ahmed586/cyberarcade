"""
seeds/seed_gamification.py — Seed badge definitions and level thresholds.

Idempotent: skips records that already exist (matched by slug / level_id).
Run from the cyberarcade-backend/ directory.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, delete
from app.core.database import engine, async_session, Base
from app.models.gamification import Level, Badge

# ─── Level thresholds ─────────────────────────────────────────────────────────
LEVELS = [
    (1,      0,      "Recruit"),
    (2,      100,    "Apprentice"),
    (3,      300,    "Analyst"),
    (4,      600,    "Specialist"),
    (5,      1000,   "Expert"),
    (6,      1600,   "Elite"),
    (7,      2500,   "Veteran"),
    (8,      4000,   "Master"),
    (9,      6000,   "Grand Master"),
    (10,     10000,  "Legend"),
    (11,     15000,  "Cyber Knight"),
    (12,     22000,  "Cyber Sentinel"),
    (13,     31000,  "Cyber Warrior"),
    (14,     42000,  "Shadow Operative"),
    (15,     55000,  "Phantom"),
    (16,     70000,  "Ghost Protocol"),
    (17,     88000,  "Zero Day"),
    (18,     110000, "Apex Hacker"),
    (19,     140000, "Cyber Overlord"),
    (20,     175000, "Transcendent"),
]

# ─── Badge catalogue ──────────────────────────────────────────────────────────
BADGES = [
    # ── EASY / Entry-level ────────────────────────────────────────────────────
    {
        "slug": "welcome",
        "name": "Welcome Aboard",
        "description": "Created your CyberArcade account",
        "icon": "👋",
        "rarity": "common",
        "category": "milestone",
        "criteria": {"type": "account_created"},
        "xp_reward": 5,
    },
    {
        "slug": "enrolled_class",
        "name": "Squad Up",
        "description": "Enrolled in your first class",
        "icon": "🏫",
        "rarity": "common",
        "category": "milestone",
        "criteria": {"type": "class_enrolled", "threshold": 1},
        "xp_reward": 10,
    },
    {
        "slug": "tasks_3",
        "name": "Getting Started",
        "description": "Solved 3 tasks",
        "icon": "🟢",
        "rarity": "common",
        "category": "progress",
        "criteria": {"type": "task_count", "threshold": 3},
        "xp_reward": 10,
    },
    {
        "slug": "tasks_5",
        "name": "Problem Solver",
        "description": "Solved 5 tasks",
        "icon": "🔧",
        "rarity": "common",
        "category": "progress",
        "criteria": {"type": "task_count", "threshold": 5},
        "xp_reward": 15,
    },
    {
        "slug": "xp_100",
        "name": "First Steps",
        "description": "Earned your first 100 XP",
        "icon": "✨",
        "rarity": "common",
        "category": "xp",
        "criteria": {"type": "xp_total", "amount": 100},
        "xp_reward": 0,
    },
    {
        "slug": "xp_250",
        "name": "Rising Star",
        "description": "Earned 250 XP",
        "icon": "🌱",
        "rarity": "common",
        "category": "xp",
        "criteria": {"type": "xp_total", "amount": 250},
        "xp_reward": 0,
    },
    {
        "slug": "labs_2",
        "name": "Lab Novice",
        "description": "Completed 2 labs",
        "icon": "🔬",
        "rarity": "common",
        "category": "progress",
        "criteria": {"type": "lab_count", "threshold": 2},
        "xp_reward": 15,
    },

    # Milestone — first actions
    {
        "slug": "first_blood",
        "name": "First Blood",
        "description": "Solved your very first task",
        "icon": "🩸",
        "rarity": "common",
        "category": "milestone",
        "criteria": {"type": "task_count", "threshold": 1},
        "xp_reward": 10,
    },
    {
        "slug": "first_lab",
        "name": "Lab Rat",
        "description": "Completed your first lab",
        "icon": "🧪",
        "rarity": "common",
        "category": "milestone",
        "criteria": {"type": "lab_count", "threshold": 1},
        "xp_reward": 25,
    },
    {
        "slug": "first_course",
        "name": "Graduate",
        "description": "Completed your first full course",
        "icon": "🎓",
        "rarity": "rare",
        "category": "milestone",
        "criteria": {"type": "course_count", "threshold": 1},
        "xp_reward": 100,
    },

    # Progress — task counts
    {
        "slug": "tasks_10",
        "name": "Persistent",
        "description": "Solved 10 tasks",
        "icon": "💪",
        "rarity": "common",
        "category": "progress",
        "criteria": {"type": "task_count", "threshold": 10},
        "xp_reward": 20,
    },
    {
        "slug": "tasks_25",
        "name": "Dedicated",
        "description": "Solved 25 tasks",
        "icon": "⚡",
        "rarity": "rare",
        "category": "progress",
        "criteria": {"type": "task_count", "threshold": 25},
        "xp_reward": 50,
    },
    {
        "slug": "tasks_50",
        "name": "Task Master",
        "description": "Solved 50 tasks",
        "icon": "🎯",
        "rarity": "epic",
        "category": "progress",
        "criteria": {"type": "task_count", "threshold": 50},
        "xp_reward": 100,
    },

    # Progress — lab counts
    {
        "slug": "labs_5",
        "name": "Lab Veteran",
        "description": "Completed 5 labs",
        "icon": "🔬",
        "rarity": "common",
        "category": "progress",
        "criteria": {"type": "lab_count", "threshold": 5},
        "xp_reward": 30,
    },
    {
        "slug": "labs_10",
        "name": "Lab Expert",
        "description": "Completed 10 labs",
        "icon": "🔭",
        "rarity": "rare",
        "category": "progress",
        "criteria": {"type": "lab_count", "threshold": 10},
        "xp_reward": 75,
    },
    {
        "slug": "labs_20",
        "name": "Lab Legend",
        "description": "Completed 20 labs",
        "icon": "🏆",
        "rarity": "epic",
        "category": "progress",
        "criteria": {"type": "lab_count", "threshold": 20},
        "xp_reward": 150,
    },

    # Skill — hint-free
    {
        "slug": "no_hints_task",
        "name": "Self-Reliant",
        "description": "Solved a task without using any hints",
        "icon": "🧠",
        "rarity": "common",
        "category": "skill",
        "criteria": {"type": "no_hints_task"},
        "xp_reward": 15,
    },
    {
        "slug": "no_hints_lab",
        "name": "Ghost Mode",
        "description": "Completed a full lab without using any hints",
        "icon": "👻",
        "rarity": "rare",
        "category": "skill",
        "criteria": {"type": "no_hints_lab"},
        "xp_reward": 50,
    },
    {
        "slug": "perfectionist",
        "name": "Perfectionist",
        "description": "Completed a full course without using any hints",
        "icon": "💎",
        "rarity": "legendary",
        "category": "skill",
        "criteria": {"type": "no_hints_course"},
        "xp_reward": 500,
    },

    # Skill — first try
    {
        "slug": "first_try_5",
        "name": "Sharp Mind",
        "description": "Solved 5 tasks correctly on the first attempt",
        "icon": "🎯",
        "rarity": "rare",
        "category": "skill",
        "criteria": {"type": "first_try_count", "threshold": 5},
        "xp_reward": 40,
    },

    # XP milestones
    {
        "slug": "xp_500",
        "name": "XP Earner",
        "description": "Earned 500 XP",
        "icon": "⚡",
        "rarity": "common",
        "category": "xp",
        "criteria": {"type": "xp_total", "amount": 500},
        "xp_reward": 0,
    },
    {
        "slug": "xp_1000",
        "name": "1000 XP Club",
        "description": "Earned 1000 XP — you're in the club",
        "icon": "🌟",
        "rarity": "rare",
        "category": "xp",
        "criteria": {"type": "xp_total", "amount": 1000},
        "xp_reward": 50,
    },
    {
        "slug": "xp_5000",
        "name": "XP Elite",
        "description": "Earned 5000 XP — true elite status",
        "icon": "💫",
        "rarity": "epic",
        "category": "xp",
        "criteria": {"type": "xp_total", "amount": 5000},
        "xp_reward": 100,
    },

    # Streak badges
    {
        "slug": "streak_3",
        "name": "3 Days Streak",
        "description": "You have completed a 3 days streak!",
        "icon": "3",
        "rarity": "common",
        "category": "streak",
        "criteria": {"type": "streak_days", "days": 3},
        "xp_reward": 20,
    },
    {
        "slug": "streak_7",
        "name": "7 Days Streak",
        "description": "You have completed a 7 days streak!",
        "icon": "7",
        "rarity": "common",
        "category": "streak",
        "criteria": {"type": "streak_days", "days": 7},
        "xp_reward": 50,
    },
    {
        "slug": "streak_30",
        "name": "1 Month Streak",
        "description": "You have completed a 1 month streak!",
        "icon": "1",
        "rarity": "rare",
        "category": "streak",
        "criteria": {"type": "streak_days", "days": 30},
        "xp_reward": 100,
    },
    {
        "slug": "streak_90",
        "name": "3 Months Streak",
        "description": "You have completed a 3 months streak!",
        "icon": "3",
        "rarity": "rare",
        "category": "streak",
        "criteria": {"type": "streak_days", "days": 90},
        "xp_reward": 200,
    },
    {
        "slug": "streak_180",
        "name": "6 Months Streak",
        "description": "You have completed a 6 months streak!",
        "icon": "6",
        "rarity": "epic",
        "category": "streak",
        "criteria": {"type": "streak_days", "days": 180},
        "xp_reward": 350,
    },
    {
        "slug": "streak_365",
        "name": "12 Months Streak",
        "description": "You have completed a 12 months streak!",
        "icon": "12",
        "rarity": "epic",
        "category": "streak",
        "criteria": {"type": "streak_days", "days": 365},
        "xp_reward": 600,
    },
    {
        "slug": "streak_545",
        "name": "18 Months Streak",
        "description": "You have completed an 18 months streak!",
        "icon": "18",
        "rarity": "legendary",
        "category": "streak",
        "criteria": {"type": "streak_days", "days": 545},
        "xp_reward": 900,
    },
    {
        "slug": "streak_730",
        "name": "24 Months Streak",
        "description": "You have completed a 24 months streak!",
        "icon": "24",
        "rarity": "legendary",
        "category": "streak",
        "criteria": {"type": "streak_days", "days": 730},
        "xp_reward": 1500,
    },

    # Course-specific
    {
        "slug": "web_security",
        "name": "Web Security Explorer",
        "description": "Completed the Web Application Security course",
        "icon": "🌐",
        "rarity": "rare",
        "category": "course",
        "criteria": {"type": "course_complete", "course_title": "Web Application Security"},
        "xp_reward": 100,
    },
    {
        "slug": "network_ninja",
        "name": "Network Ninja",
        "description": "Completed the Network Penetration Testing course",
        "icon": "📡",
        "rarity": "rare",
        "category": "course",
        "criteria": {"type": "course_complete", "course_title": "Network Penetration Testing"},
        "xp_reward": 100,
    },
    {
        "slug": "linux_master",
        "name": "Linux Master",
        "description": "Completed the Linux Privilege Escalation course",
        "icon": "🐧",
        "rarity": "epic",
        "category": "course",
        "criteria": {"type": "course_complete", "course_title": "Linux Privilege Escalation"},
        "xp_reward": 150,
    },
    {
        "slug": "dfir_specialist",
        "name": "DFIR Specialist",
        "description": "Completed the full Digital Forensics course",
        "icon": "🔍",
        "rarity": "epic",
        "category": "course",
        "criteria": {"type": "course_complete", "course_title": "Digital Forensics"},
        "xp_reward": 200,
    },

    # Lab-specific
    {
        "slug": "malware_hunter",
        "name": "Malware Hunter",
        "description": "Completed the Malware Persistence Analysis lab",
        "icon": "🦠",
        "rarity": "rare",
        "category": "skill",
        "criteria": {"type": "lab_complete", "lab_title": "Malware Persistence Analysis"},
        "xp_reward": 75,
    },
    {
        "slug": "memory_analyst",
        "name": "Memory Analyst",
        "description": "Completed the Memory Forensics Basics lab",
        "icon": "💾",
        "rarity": "rare",
        "category": "skill",
        "criteria": {"type": "lab_complete", "lab_title": "Memory Forensics Basics"},
        "xp_reward": 75,
    },
    {
        "slug": "stego_master",
        "name": "Stego Master",
        "description": "Completed the Steganography and Metadata Analysis lab",
        "icon": "🖼️",
        "rarity": "rare",
        "category": "skill",
        "criteria": {"type": "lab_complete", "lab_title": "Steganography and Metadata Analysis"},
        "xp_reward": 75,
    },
    {
        "slug": "soc_analyst",
        "name": "SOC Analyst",
        "description": "Completed 3 or more courses — building a security operations mindset",
        "icon": "🛡️",
        "rarity": "epic",
        "category": "milestone",
        "criteria": {"type": "course_count", "threshold": 3},
        "xp_reward": 200,
    },

    # ── MEDIUM ────────────────────────────────────────────────────────────────
    {
        "slug": "tasks_75",
        "name": "Relentless",
        "description": "Solved 75 tasks",
        "icon": "🏹",
        "rarity": "rare",
        "category": "progress",
        "criteria": {"type": "task_count", "threshold": 75},
        "xp_reward": 75,
    },
    {
        "slug": "labs_15",
        "name": "Lab Conqueror",
        "description": "Completed 15 labs",
        "icon": "🧬",
        "rarity": "rare",
        "category": "progress",
        "criteria": {"type": "lab_count", "threshold": 15},
        "xp_reward": 100,
    },
    {
        "slug": "xp_2500",
        "name": "XP Hunter",
        "description": "Earned 2500 XP",
        "icon": "⚡",
        "rarity": "rare",
        "category": "xp",
        "criteria": {"type": "xp_total", "amount": 2500},
        "xp_reward": 75,
    },
    {
        "slug": "courses_2",
        "name": "Double Threat",
        "description": "Completed 2 courses",
        "icon": "📚",
        "rarity": "rare",
        "category": "milestone",
        "criteria": {"type": "course_count", "threshold": 2},
        "xp_reward": 150,
    },
    {
        "slug": "first_try_10",
        "name": "Precision",
        "description": "Solved 10 tasks correctly on the first attempt",
        "icon": "🎯",
        "rarity": "rare",
        "category": "skill",
        "criteria": {"type": "first_try_count", "threshold": 10},
        "xp_reward": 60,
    },

    # ── HARD / Epic ───────────────────────────────────────────────────────────
    {
        "slug": "tasks_100",
        "name": "Centurion",
        "description": "Solved 100 tasks — nothing stops you",
        "icon": "💯",
        "rarity": "epic",
        "category": "progress",
        "criteria": {"type": "task_count", "threshold": 100},
        "xp_reward": 200,
    },
    {
        "slug": "labs_30",
        "name": "Lab Overlord",
        "description": "Completed 30 labs",
        "icon": "🏛️",
        "rarity": "epic",
        "category": "progress",
        "criteria": {"type": "lab_count", "threshold": 30},
        "xp_reward": 250,
    },
    {
        "slug": "xp_10000",
        "name": "XP Titan",
        "description": "Earned 10,000 XP",
        "icon": "🌠",
        "rarity": "epic",
        "category": "xp",
        "criteria": {"type": "xp_total", "amount": 10000},
        "xp_reward": 200,
    },
    {
        "slug": "courses_5",
        "name": "Polymath",
        "description": "Completed 5 different courses",
        "icon": "🎓",
        "rarity": "epic",
        "category": "milestone",
        "criteria": {"type": "course_count", "threshold": 5},
        "xp_reward": 400,
    },
    {
        "slug": "first_try_25",
        "name": "Eagle Eye",
        "description": "Solved 25 tasks correctly on the first attempt",
        "icon": "🦅",
        "rarity": "epic",
        "category": "skill",
        "criteria": {"type": "first_try_count", "threshold": 25},
        "xp_reward": 150,
    },

    # ── LEGENDARY ─────────────────────────────────────────────────────────────
    {
        "slug": "tasks_200",
        "name": "The Grinder",
        "description": "Solved 200 tasks — you never rest",
        "icon": "⚙️",
        "rarity": "legendary",
        "category": "progress",
        "criteria": {"type": "task_count", "threshold": 200},
        "xp_reward": 500,
    },
    {
        "slug": "labs_50",
        "name": "Lab God",
        "description": "Completed 50 labs — absolute mastery",
        "icon": "👑",
        "rarity": "legendary",
        "category": "progress",
        "criteria": {"type": "lab_count", "threshold": 50},
        "xp_reward": 600,
    },
    {
        "slug": "xp_25000",
        "name": "XP Transcendent",
        "description": "Earned 25,000 XP — you have ascended",
        "icon": "🌌",
        "rarity": "legendary",
        "category": "xp",
        "criteria": {"type": "xp_total", "amount": 25000},
        "xp_reward": 500,
    },
    {
        "slug": "courses_10",
        "name": "Omniscient",
        "description": "Completed 10 courses — all knowledge absorbed",
        "icon": "🧿",
        "rarity": "legendary",
        "category": "milestone",
        "criteria": {"type": "course_count", "threshold": 10},
        "xp_reward": 1000,
    },
    {
        "slug": "first_try_50",
        "name": "Infallible",
        "description": "Solved 50 tasks correctly on the first attempt — flawless execution",
        "icon": "🔮",
        "rarity": "legendary",
        "category": "skill",
        "criteria": {"type": "first_try_count", "threshold": 50},
        "xp_reward": 400,
    },
    {
        "slug": "xp_50000",
        "name": "The Architect",
        "description": "Earned 50,000 XP — a true architect of the cyber world",
        "icon": "🏰",
        "rarity": "legendary",
        "category": "xp",
        "criteria": {"type": "xp_total", "amount": 50000},
        "xp_reward": 1000,
    },

    # ── First Blood series ────────────────────────────────────────────────────
    {
        "slug": "first_blood_1",
        "name": "First Blood",
        "description": "You got first blood in one lab!",
        "icon": "🩸",
        "rarity": "common",
        "category": "skill",
        "criteria": {"type": "first_blood_count", "threshold": 1},
        "xp_reward": 15,
    },
    {
        "slug": "first_blood_2",
        "name": "First Blood II",
        "description": "You got first blood in 5 labs!",
        "icon": "🩸",
        "rarity": "common",
        "category": "skill",
        "criteria": {"type": "first_blood_count", "threshold": 5},
        "xp_reward": 30,
    },
    {
        "slug": "first_blood_3",
        "name": "First Blood III",
        "description": "You got first blood in 10 labs!",
        "icon": "🩸",
        "rarity": "rare",
        "category": "skill",
        "criteria": {"type": "first_blood_count", "threshold": 10},
        "xp_reward": 60,
    },
    {
        "slug": "first_blood_4",
        "name": "First Blood IV",
        "description": "You got first blood in 15 labs!",
        "icon": "🩸",
        "rarity": "rare",
        "category": "skill",
        "criteria": {"type": "first_blood_count", "threshold": 15},
        "xp_reward": 90,
    },
    {
        "slug": "first_blood_5",
        "name": "First Blood V",
        "description": "You got first blood in 20 labs!",
        "icon": "🩸",
        "rarity": "rare",
        "category": "skill",
        "criteria": {"type": "first_blood_count", "threshold": 20},
        "xp_reward": 120,
    },
    {
        "slug": "first_blood_6",
        "name": "First Blood VI",
        "description": "You got first blood in 30 labs!",
        "icon": "🩸",
        "rarity": "epic",
        "category": "skill",
        "criteria": {"type": "first_blood_count", "threshold": 30},
        "xp_reward": 200,
    },
    {
        "slug": "first_blood_7",
        "name": "First Blood VII",
        "description": "You got first blood in 40 labs!",
        "icon": "🩸",
        "rarity": "epic",
        "category": "skill",
        "criteria": {"type": "first_blood_count", "threshold": 40},
        "xp_reward": 280,
    },
    {
        "slug": "first_blood_8",
        "name": "First Blood VIII",
        "description": "You got first blood in 50 labs!",
        "icon": "🩸",
        "rarity": "epic",
        "category": "skill",
        "criteria": {"type": "first_blood_count", "threshold": 50},
        "xp_reward": 400,
    },
    {
        "slug": "first_blood_9",
        "name": "First Blood IX",
        "description": "You got first blood in 75 labs!",
        "icon": "🩸",
        "rarity": "legendary",
        "category": "skill",
        "criteria": {"type": "first_blood_count", "threshold": 75},
        "xp_reward": 600,
    },
    {
        "slug": "first_blood_10",
        "name": "First Blood X",
        "description": "You got first blood in 100 labs!",
        "icon": "🩸",
        "rarity": "legendary",
        "category": "skill",
        "criteria": {"type": "first_blood_count", "threshold": 100},
        "xp_reward": 1000,
    },
]


async def ensure_tables() -> None:
    import app.models  # ensure all models registered
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    await ensure_tables()
    async with async_session() as db:
        # ── Levels ────────────────────────────────────────────────────────────
        for level_id, min_xp, title in LEVELS:
            existing = await db.execute(select(Level).where(Level.level_id == level_id))
            if existing.scalar_one_or_none():
                continue
            db.add(Level(level_id=level_id, min_xp=min_xp, title=title))
        await db.commit()
        print(f"[gamification] {len(LEVELS)} levels seeded.")

        # ── Delete old streak badges that were renamed ────────────────────────
        old_streak_slugs = [
            "streak_1", "streak_3", "streak_7", "streak_14",
            "streak_30", "streak_60", "streak_100",
        ]
        await db.execute(delete(Badge).where(Badge.slug.in_(old_streak_slugs)))
        await db.commit()

        # ── Badges ────────────────────────────────────────────────────────────
        added = 0
        for b in BADGES:
            existing = await db.execute(select(Badge).where(Badge.slug == b["slug"]))
            if existing.scalar_one_or_none():
                continue
            db.add(Badge(**b))
            added += 1
        await db.commit()
        print(f"[gamification] {added} badges seeded ({len(BADGES) - added} already existed).")


if __name__ == "__main__":
    asyncio.run(main())
