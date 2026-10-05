import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.course import Course
from app.schemas.certificate import CertificateOut, CertificateVerifyResponse, CourseCompletionStatus
from app.services import certificate_service as svc

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


# ── Admin-only verification ───────────────────────────────────────────────────

@router.get("/verify/{serial}", response_model=CertificateVerifyResponse)
async def verify_certificate(
    serial: str,
    _: User = Depends(require_role("admin", "system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: verify a certificate by serial number."""
    cert = await svc.get_cert_by_serial(db, serial)
    if not cert or cert.verification_status != "valid":
        return CertificateVerifyResponse(
            valid=False,
            message="Certificate not found or has been revoked.",
        )
    return CertificateVerifyResponse(
        valid=True,
        student_name=cert.student_name,
        course_name=cert.course_name,
        issued_at=cert.issued_at,
        serial_number=cert.serial_number,
        certificate_id=str(cert.certificate_id),
    )


# ── Authenticated user endpoints ──────────────────────────────────────────────

@router.get("/me", response_model=list[CertificateOut])
async def my_certificates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all certificates belonging to the authenticated user."""
    return await svc.get_user_certs(db, current_user.user_id)


@router.get("/completion/{course_id}", response_model=CourseCompletionStatus)
async def course_completion_status(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check whether the user has completed all tasks in a course."""
    result = await db.execute(select(Course).where(Course.course_id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    is_complete, total, correct = await svc.check_course_completion(
        db, current_user.user_id, course_id
    )
    existing = await svc.get_existing_cert(db, current_user.user_id, course_id)

    cert_out = None
    if existing:
        cert_out = CertificateOut.model_validate(existing)

    return CourseCompletionStatus(
        course_id=course_id,
        course_name=course.title,
        total_tasks=total,
        completed_tasks=correct,
        is_complete=is_complete,
        certificate=cert_out,
    )


@router.post("/generate/{course_id}", response_model=CertificateOut, status_code=201)
async def generate_certificate(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate (or retrieve existing) certificate for a completed course."""
    result = await db.execute(select(Course).where(Course.course_id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    is_complete, total, correct = await svc.check_course_completion(
        db, current_user.user_id, course_id
    )
    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This course has no tasks — certificate cannot be issued.",
        )
    if not is_complete:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Course not fully completed ({correct}/{total} tasks correct).",
        )

    cert = await svc.generate_certificate(
        db=db,
        user_id=current_user.user_id,
        course_id=course_id,
        student_name=current_user.full_name,
        course_name=course.title,
    )
    return CertificateOut.model_validate(cert)


@router.get("/{cert_id}/download")
async def download_certificate(
    cert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream the PDF for a certificate the user owns."""
    cert = await svc.get_cert_by_id(db, cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found.")
    if cert.user_id != current_user.user_id and current_user.role not in ("admin", "system_admin"):
        raise HTTPException(status_code=403, detail="Access denied.")

    pdf_path = Path(cert.pdf_path) if cert.pdf_path else None
    if not pdf_path or not pdf_path.exists():
        # Regenerate if file was lost
        from app.services.certificate_service import CERT_DIR, _render_pdf
        CERT_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = CERT_DIR / f"{cert.serial_number}.pdf"
        _render_pdf(cert.student_name, cert.course_name, cert.serial_number, cert.issued_at, pdf_path)
        cert.pdf_path = str(pdf_path)
        await db.flush()

    filename = f"CyberArcade_Certificate_{cert.serial_number}.pdf"
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.get("/admin/all", response_model=list[CertificateOut])
async def admin_list_certificates(
    _: User = Depends(require_role("admin", "system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin: list all certificates across all users."""
    from app.models.certificate import Certificate
    result = await db.execute(
        select(Certificate).order_by(Certificate.issued_at.desc()).limit(500)
    )
    return list(result.scalars().all())


@router.put("/admin/{cert_id}/revoke", response_model=CertificateOut)
async def admin_revoke_certificate(
    cert_id: uuid.UUID,
    _: User = Depends(require_role("admin", "system_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin: revoke a certificate (sets verification_status = 'revoked')."""
    cert = await svc.get_cert_by_id(db, cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found.")
    cert.verification_status = "revoked"
    await db.flush()
    return CertificateOut.model_validate(cert)
