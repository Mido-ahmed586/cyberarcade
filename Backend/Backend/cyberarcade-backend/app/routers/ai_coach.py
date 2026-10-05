from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ai_coach import UserAIInsight, UserLearningMetric, UserSkillScore
from app.models.chatbot import ChatbotConversation
from app.models.course import Course
from app.models.lab import Lab, LabTask
from app.models.lab_instance import LabInstance, LabProgress
from app.models.user import User

router = APIRouter(prefix="/api/ai-coach", tags=["AI Coach"])

SKILL_CATEGORIES = [
    "Network Security",
    "Linux Commands",
    "Web Security",
    "Cryptography",
    "Malware Analysis",
    "Digital Forensics",
    "Incident Response",
    "Vulnerability Assessment",
]


def _normalize_skill(category: str | None, title: str | None = "") -> str:
    """Map course/lab labels into stable AI Coach skill buckets."""
    text = f"{category or ''} {title or ''}".lower()
    if any(k in text for k in ["forensic", "memory", "disk", "pcap"]):
        return "Digital Forensics"
    if any(k in text for k in ["web", "xss", "sql", "injection", "csrf"]):
        return "Web Security"
    if any(k in text for k in ["crypto", "hash", "cipher"]):
        return "Cryptography"
    if any(k in text for k in ["malware", "c2", "ransomware"]):
        return "Malware Analysis"
    if any(k in text for k in ["incident", "response", "siem", "log"]):
        return "Incident Response"
    if any(k in text for k in ["vulnerability", "metasploit", "nmap", "recon", "penetration"]):
        return "Vulnerability Assessment"
    if any(k in text for k in ["linux", "privilege", "ssh", "command"]):
        return "Linux Commands"
    return "Network Security"


async def _collect_user_metrics(db: AsyncSession, user_id):
    """Collect behavior data from existing progress, lab instance, course, and chat tables."""
    tasks_result = await db.execute(select(LabTask.task_id, LabTask.lab_id))
    task_rows = tasks_result.all()
    total_tasks = len(task_rows)
    tasks_by_lab = defaultdict(int)
    for task_id, lab_id in task_rows:
        tasks_by_lab[lab_id] += 1

    progress_result = await db.execute(
        select(LabProgress).where(LabProgress.user_id == user_id)
    )
    progress_rows = progress_result.scalars().all()
    completed_tasks = sum(1 for p in progress_rows if p.status in ("completed", "auto_solved") or p.is_correct)
    failed_attempts = 0
    for p in progress_rows:
        attempts = p.attempt_count or (1 if p.submitted_answer else 0)
        failed_attempts += max(attempts - (1 if p.is_correct else 0), 0)
    hints_used = sum(p.hints_used or 0 for p in progress_rows)
    retries = sum(max((p.attempt_count or (1 if p.submitted_answer else 0)) - 1, 0) for p in progress_rows)
    attempted_tasks = len(progress_rows)

    completed_by_lab = defaultdict(int)
    for p in progress_rows:
        if p.status in ("completed", "auto_solved") or p.is_correct:
            completed_by_lab[p.lab_id] += 1
    completed_lab_ids = {
        lab_id for lab_id, total in tasks_by_lab.items()
        if total > 0 and completed_by_lab.get(lab_id, 0) >= total
    }

    instance_result = await db.execute(
        select(LabInstance).where(LabInstance.user_id == user_id)
    )
    instances = instance_result.scalars().all()
    now = datetime.now(timezone.utc)
    time_spent_minutes = 0
    touched_lab_ids = set(completed_by_lab.keys())
    for inst in instances:
        touched_lab_ids.add(inst.lab_id)
        end = inst.terminated_at or min(now, inst.expires_at)
        if inst.started_at and end and end > inst.started_at:
            time_spent_minutes += int((end - inst.started_at).total_seconds() // 60)

    chat_result = await db.execute(
        select(func.count(ChatbotConversation.message_id)).where(
            ChatbotConversation.user_id == user_id,
            ChatbotConversation.role == "user",
        )
    )
    chatbot_questions = chat_result.scalar() or 0

    course_result = await db.execute(select(Course, Lab).join(Lab, Lab.course_id == Course.course_id))
    category_labs = course_result.all()
    lab_meta = {
        lab.lab_id: {
            "course_id": course.course_id,
            "course_title": course.title,
            "lab_title": lab.title,
            "skill": _normalize_skill(course.category, f"{course.title} {lab.title}"),
        }
        for course, lab in category_labs
    }

    skill_data = {
        skill: {"skill_category": skill, "score": 0, "completed": 0, "attempted": 0, "hints_used": 0}
        for skill in SKILL_CATEGORIES
    }
    for lab_id in touched_lab_ids:
        skill = lab_meta.get(lab_id, {}).get("skill", "Network Security")
        skill_data[skill]["attempted"] += 1
        if lab_id in completed_lab_ids:
            skill_data[skill]["completed"] += 1
    for p in progress_rows:
        skill = lab_meta.get(p.lab_id, {}).get("skill", "Network Security")
        skill_data[skill]["hints_used"] += p.hints_used or 0

    for item in skill_data.values():
        if item["attempted"]:
            completion_score = round((item["completed"] / item["attempted"]) * 80)
            hint_penalty = min(item["hints_used"] * 3, 25)
            item["score"] = max(10, min(100, completion_score + 20 - hint_penalty))

    total_labs = len(tasks_by_lab)
    labs_completed = len(completed_lab_ids)
    course_progress_percent = round((labs_completed / total_labs) * 100) if total_labs else 0
    average_score = round((completed_tasks / attempted_tasks) * 100) if attempted_tasks else 0

    category_performance = list(skill_data.values())

    progress_over_time = []
    weekly = defaultdict(int)
    for p in progress_rows:
        if p.completed_at:
            iso_year, iso_week, _ = p.completed_at.isocalendar()
            weekly[f"{iso_year}-W{iso_week:02d}"] += 1
    running = 0
    for week in sorted(weekly):
        running += weekly[week]
        progress_over_time.append({
            "week": week,
            "progress": round((running / max(total_tasks, 1)) * 100),
        })

    recommended_labs = []
    weakest_skill = min(skill_data.values(), key=lambda s: s["score"])["skill_category"]
    for lab_id, meta in lab_meta.items():
        if meta["skill"] == weakest_skill and lab_id not in completed_lab_ids:
            recommended_labs.append({
                "lab_id": str(lab_id),
                "title": meta["lab_title"],
                "course_title": meta["course_title"],
                "skill_category": meta["skill"],
            })
        if len(recommended_labs) >= 5:
            break

    metrics = {
        "completed_tasks": completed_tasks,
        "failed_task_attempts": failed_attempts,
        "hints_used": hints_used,
        "time_spent_minutes": time_spent_minutes,
        "retries": retries,
        "labs_completed": labs_completed,
        "total_labs": total_labs,
        "course_progress_percent": course_progress_percent,
        "chatbot_questions": chatbot_questions,
        "average_score": average_score,
        "started_labs": len(touched_lab_ids),
    }
    return metrics, list(skill_data.values()), recommended_labs, progress_over_time, category_performance


def _build_rule_based_insight(metrics, skills, recommended_labs):
    strongest = max(skills, key=lambda s: s["score"])
    weakest = min(skills, key=lambda s: s["score"])
    strengths = []
    weaknesses = []

    if metrics["labs_completed"]:
        strengths.append(f"Completed {metrics['labs_completed']} lab(s) with measurable progress.")
    if strongest["score"] > 0:
        strengths.append(f"Strongest current skill: {strongest['skill_category']}.")
    if metrics["chatbot_questions"] > 0:
        strengths.append("Uses the AI assistant to clarify lab concepts.")

    if weakest["score"] < 55:
        weaknesses.append(f"Needs more practice in {weakest['skill_category']}.")
    if metrics["hints_used"] > max(metrics["completed_tasks"], 1):
        weaknesses.append("Uses many hints compared with completed tasks.")
    if metrics["failed_task_attempts"] or metrics["retries"]:
        weaknesses.append("Some tasks required repeated attempts.")

    if not strengths:
        strengths = ["Ready to begin structured cybersecurity practice."]
    if not weaknesses:
        weaknesses = ["No major weakness detected yet; complete more labs for deeper analysis."]

    improvement_plan = [
        f"Practice one focused lab in {weakest['skill_category']} before starting a new topic.",
        "After each lab, write down the command or concept that solved the task.",
        "Retry incorrect tasks once without hints before using assistance.",
    ]
    if recommended_labs:
        improvement_plan.insert(0, f"Start with: {recommended_labs[0]['title']}.")

    summary = (
        "You are building momentum. "
        f"Your strongest area is {strongest['skill_category']}, while {weakest['skill_category']} "
        "should be your next practice focus."
    )
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvement_plan": improvement_plan,
        "recommended_labs": recommended_labs,
        "summary": summary,
    }


@router.get("/overview")
async def get_ai_coach_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    metrics, skills, recommended_labs, progress_over_time, category_performance = await _collect_user_metrics(db, current_user.user_id)
    insight_result = await db.execute(
        select(UserAIInsight)
        .where(UserAIInsight.user_id == current_user.user_id)
        .order_by(UserAIInsight.created_at.desc())
        .limit(1)
    )
    latest = insight_result.scalar_one_or_none()
    insight = latest and {
        "strengths": latest.strengths,
        "weaknesses": latest.weaknesses,
        "improvement_plan": latest.improvement_plan,
        "recommended_labs": latest.recommended_labs,
        "summary": latest.summary,
    } or _build_rule_based_insight(metrics, skills, recommended_labs)
    return {
        "metrics": metrics,
        "insight": insight,
        "progress_over_time": progress_over_time,
        "category_performance": category_performance,
    }


@router.get("/skills")
async def get_ai_coach_skills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _, skills, _, _, _ = await _collect_user_metrics(db, current_user.user_id)
    return {"skills": skills}


@router.get("/recommendations")
async def get_ai_coach_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    metrics, skills, recommended_labs, _, _ = await _collect_user_metrics(db, current_user.user_id)
    insight = _build_rule_based_insight(metrics, skills, recommended_labs)
    return {"recommended_labs": recommended_labs, "improvement_plan": insight["improvement_plan"]}


@router.post("/generate-insight")
async def generate_ai_coach_insight(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    metrics, skills, recommended_labs, progress_over_time, category_performance = await _collect_user_metrics(db, current_user.user_id)
    insight = _build_rule_based_insight(metrics, skills, recommended_labs)

    db.add(UserLearningMetric(user_id=current_user.user_id, metadata_={
        "progress_over_time": progress_over_time,
        "category_performance": category_performance,
    }, **{k: metrics[k] for k in [
        "completed_tasks", "failed_task_attempts", "hints_used", "time_spent_minutes",
        "retries", "labs_completed", "course_progress_percent", "chatbot_questions",
    ]}))

    for skill in skills:
        existing_result = await db.execute(
            select(UserSkillScore).where(
                UserSkillScore.user_id == current_user.user_id,
                UserSkillScore.skill_category == skill["skill_category"],
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            existing.score = skill["score"]
            existing.evidence = skill
            existing.updated_at = datetime.now(timezone.utc)
        else:
            db.add(UserSkillScore(
                user_id=current_user.user_id,
                skill_category=skill["skill_category"],
                score=skill["score"],
                evidence=skill,
            ))

    stored = UserAIInsight(
        user_id=current_user.user_id,
        summary=insight["summary"],
        strengths=insight["strengths"],
        weaknesses=insight["weaknesses"],
        improvement_plan=insight["improvement_plan"],
        recommended_labs=insight["recommended_labs"],
        generated_by="rules",
    )
    db.add(stored)
    await db.flush()
    return insight
