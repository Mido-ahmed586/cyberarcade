import uuid
import math
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.models.certificate import Certificate
from app.models.course import Course
from app.models.lab import Lab, LabTask
from app.models.lab_instance import LabProgress

CERT_DIR = Path(__file__).resolve().parents[2] / "certificates"


def _make_serial() -> str:
    """CYAC-XXXX-XXXX-XXXX-XXXX (24 chars, UUID-based hex)."""
    h = uuid.uuid4().hex.upper()
    return f"CYAC-{h[0:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"


async def _count_course_tasks(db: AsyncSession, course_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count(LabTask.task_id))
        .join(Lab, LabTask.lab_id == Lab.lab_id)
        .where(Lab.course_id == course_id)
    )
    return result.scalar_one()


async def _count_correct_tasks(db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count(LabProgress.progress_id))
        .join(LabTask, LabProgress.task_id == LabTask.task_id)
        .join(Lab, LabTask.lab_id == Lab.lab_id)
        .where(Lab.course_id == course_id)
        .where(LabProgress.user_id == user_id)
        .where(LabProgress.is_correct == True)  # noqa: E712
    )
    return result.scalar_one()


async def check_course_completion(
    db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID
) -> tuple[bool, int, int]:
    """Return (is_complete, total_tasks, correct_tasks)."""
    total = await _count_course_tasks(db, course_id)
    if total == 0:
        return False, 0, 0
    correct = await _count_correct_tasks(db, user_id, course_id)
    return correct >= total, total, correct


async def get_existing_cert(
    db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID
) -> Certificate | None:
    result = await db.execute(
        select(Certificate)
        .where(Certificate.user_id == user_id)
        .where(Certificate.course_id == course_id)
    )
    return result.scalar_one_or_none()


async def get_cert_by_id(db: AsyncSession, cert_id: uuid.UUID) -> Certificate | None:
    result = await db.execute(
        select(Certificate).where(Certificate.certificate_id == cert_id)
    )
    return result.scalar_one_or_none()


async def get_cert_by_serial(db: AsyncSession, serial: str) -> Certificate | None:
    result = await db.execute(
        select(Certificate).where(Certificate.serial_number == serial.upper())
    )
    return result.scalar_one_or_none()


async def get_user_certs(db: AsyncSession, user_id: uuid.UUID) -> list[Certificate]:
    result = await db.execute(
        select(Certificate)
        .where(Certificate.user_id == user_id)
        .order_by(Certificate.issued_at.desc())
    )
    return list(result.scalars().all())


async def generate_certificate(
    db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID,
    student_name: str, course_name: str,
) -> Certificate:
    existing = await get_existing_cert(db, user_id, course_id)
    if existing:
        return existing

    serial = _make_serial()
    issued_at = datetime.now(timezone.utc)

    CERT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"{serial}.pdf"
    pdf_path = CERT_DIR / pdf_filename

    _render_pdf(student_name, course_name, serial, issued_at, pdf_path)

    cert = Certificate(
        serial_number=serial,
        user_id=user_id,
        course_id=course_id,
        student_name=student_name,
        course_name=course_name,
        issued_at=issued_at,
        pdf_path=str(pdf_path),
        verification_status="valid",
    )
    db.add(cert)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        return await get_existing_cert(db, user_id, course_id)
    return cert


# ── PDF generation ─────────────────────────────────────────────────────────────

def _draw_hex_logo(c, cx: float, cy: float, S: float) -> None:
    """
    Draw the CyberArcade hexagonal lock logo centred at PDF point (cx, cy).
    S = scale factor: 1 SVG unit (28×28 viewbox) → S PDF points.
    """
    from reportlab.lib.colors import HexColor as _HC

    C_GREEN        = _HC("#00ff66")
    C_GREEN_BRIGHT = _HC("#66ffaa")
    C_CREAM_DIM    = _HC("#7a8f7a")   # cream @ ~0.4 opacity on dark bg
    C_CREAM        = _HC("#eef2ee")

    # SVG origin is top-left (y down); PDF origin is bottom-left (y up).
    def tx(sx): return cx + (sx - 14) * S
    def ty(sy): return cy - (sy - 14) * S

    # Outer hexagon: fill=#00ff66, stroke=#66ffaa, sw=1.5
    outer = [(14,1),(25,7),(25,21),(14,27),(3,21),(3,7)]
    p = c.beginPath()
    p.moveTo(tx(outer[0][0]), ty(outer[0][1]))
    for sx, sy in outer[1:]:
        p.lineTo(tx(sx), ty(sy))
    p.close()
    c.setFillColor(C_GREEN)
    c.setStrokeColor(C_GREEN_BRIGHT)
    c.setLineWidth(1.5 * S)
    c.drawPath(p, fill=1, stroke=1)

    # Inner hexagon outline (faint): stroke=cream-dim, sw=0.8
    inner = [(14,5),(22,9.5),(22,18.5),(14,23),(6,18.5),(6,9.5)]
    p2 = c.beginPath()
    p2.moveTo(tx(inner[0][0]), ty(inner[0][1]))
    for sx, sy in inner[1:]:
        p2.lineTo(tx(sx), ty(sy))
    p2.close()
    c.setStrokeColor(C_CREAM_DIM)
    c.setLineWidth(0.8 * S)
    c.drawPath(p2, fill=0, stroke=1)

    # Lock body: rect x=10, y=14, w=8, h=6, rx=1 — fill=cream
    c.setFillColor(C_CREAM)
    c.roundRect(tx(10), ty(20), 8 * S, 6 * S, 1 * S, fill=1, stroke=0)

    # Lock shackle via two quarter-circle Béziers (r=2.5, kappa≈0.5523)
    k = 2.5 * 0.5523
    p3 = c.beginPath()
    p3.moveTo(tx(11.5), ty(14))
    p3.lineTo(tx(11.5), ty(11.5))
    p3.curveTo(tx(11.5), ty(11.5 - k), tx(14 - k), ty(9), tx(14), ty(9))
    p3.curveTo(tx(14 + k), ty(9), tx(16.5), ty(11.5 - k), tx(16.5), ty(11.5))
    p3.lineTo(tx(16.5), ty(14))
    c.setStrokeColor(C_CREAM)
    c.setLineWidth(1.4 * S)
    c.drawPath(p3, fill=0, stroke=1)

    # Keyhole circle: cx=14, cy=16.8, r=1 — fill=green
    c.setFillColor(C_GREEN)
    c.circle(tx(14), ty(16.8), 1 * S, fill=1, stroke=0)

    # Keyhole slot: rect x=13.4, y=17.5, w=1.2, h=1.5, rx=0.4 — fill=green
    c.setFillColor(C_GREEN)
    c.roundRect(tx(13.4), ty(19), 1.2 * S, 1.5 * S, 0.4 * S, fill=1, stroke=0)


def _render_pdf(
    student_name: str,
    course_name: str,
    serial_number: str,
    issued_at: datetime,
    output_path: Path,
) -> None:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.colors import HexColor

    W, H = landscape(A4)  # 841.89 × 595.28 pt

    # ── Colour palette ──────────────────────────────────────────────────────
    C_BG        = HexColor("#07080c")
    C_CARD      = HexColor("#0d1117")
    C_BORDER    = HexColor("#1a1d2e")
    C_GREEN     = HexColor("#00ff66")
    C_GREEN_DIM = HexColor("#00cc52")
    C_GREEN_MID = HexColor("#007733")
    C_GREEN_DEEP = HexColor("#041a0c")
    C_WHITE     = HexColor("#f0f4f0")
    C_GRAY      = HexColor("#8899aa")
    C_DARK      = HexColor("#2a3344")
    C_RULE      = HexColor("#0e1f14")

    c = rl_canvas.Canvas(str(output_path), pagesize=(W, H))

    # ── Background ──────────────────────────────────────────────────────────
    c.setFillColor(C_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Inner card
    c.setFillColor(C_CARD)
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.roundRect(24, 24, W - 48, H - 48, 10, fill=1, stroke=1)

    # Glowing border (three layers, decreasing opacity)
    for inset, alpha in [(26, 0.06), (27, 0.12), (28, 0.20)]:
        color = HexColor(f"#00ff66")
        color.alpha = alpha
        c.setStrokeColor(HexColor("#004422") if inset == 26 else
                         HexColor("#006633") if inset == 27 else
                         HexColor("#00aa44"))
        c.setLineWidth(0.4 if inset < 28 else 0.75)
        c.roundRect(inset, inset, W - inset * 2, H - inset * 2, 9, fill=0, stroke=1)

    # ── Corner L-brackets ───────────────────────────────────────────────────
    BL = 30        # bracket arm length
    BO = 34        # bracket offset from page edge
    c.setStrokeColor(C_GREEN)
    c.setLineWidth(1.5)
    for (x, y, dx, dy) in [
        (BO, H - BO,  1,  -1),   # top-left
        (W - BO, H - BO, -1, -1), # top-right
        (BO, BO,       1,   1),   # bottom-left
        (W - BO, BO,  -1,   1),   # bottom-right
    ]:
        c.line(x, y, x + dx * BL, y)
        c.line(x, y, x, y + dy * BL)

    # ── Hex dot clusters (decorative corners) ───────────────────────────────
    def hex_dot(cx, cy, r=4.5):
        path = c.beginPath()
        for i in range(6):
            angle = math.pi / 3 * i - math.pi / 6
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            if i == 0: path.moveTo(px, py)
            else: path.lineTo(px, py)
        path.close()
        c.drawPath(path, fill=1, stroke=0)

    # Dim cluster behind each corner bracket
    c.setFillColor(HexColor("#0a1f10"))
    for (bx, by) in [(BO + 18, H - BO - 18), (W - BO - 18, H - BO - 18),
                     (BO + 18, BO + 18), (W - BO - 18, BO + 18)]:
        for (ox, oy) in [(0, 0), (13, 7), (-13, 7), (0, 14), (13, -7), (-13, -7)]:
            hex_dot(bx + ox, by + oy, 4)

    c.setFillColor(HexColor("#003311"))
    for (bx, by) in [(BO + 18, H - BO - 18), (W - BO - 18, H - BO - 18),
                     (BO + 18, BO + 18), (W - BO - 18, BO + 18)]:
        hex_dot(bx, by, 4)
        hex_dot(bx + 13, by + 7, 2.5)
        hex_dot(bx - 13, by + 7, 2.5)

    # ── Logo / header ────────────────────────────────────────────────────────
    _draw_hex_logo(c, 84, H - 78, 1.3)

    _cf, _cs = "Helvetica-Bold", 13
    c.setFont(_cf, _cs)
    _cw = c.stringWidth("CYBER", _cf, _cs)
    c.setFillColor(C_GREEN)
    c.drawString(106, H - 73, "CYBER")
    c.setFillColor(C_WHITE)
    c.drawString(106 + _cw, H - 73, "ARCADE")

    c.setFont("Helvetica", 7.5)
    c.setFillColor(C_DARK)
    c.drawString(106, H - 86, "CYBERSECURITY TRAINING PLATFORM")

    c.setFont("Helvetica", 8)
    c.setFillColor(C_DARK)
    c.drawRightString(W - 68, H - 72, "VERIFIED DIGITAL CERTIFICATE")
    c.drawRightString(W - 68, H - 84, "cyberarcade.io")

    # Header rule
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.5)
    c.line(68, H - 100, W - 68, H - 100)
    c.setStrokeColor(C_GREEN_DIM)
    c.setLineWidth(0.6)
    c.line(68, H - 100, 260, H - 100)

    # ── "CERTIFICATE OF COMPLETION" ──────────────────────────────────────────
    c.setFont("Helvetica-Bold", 44)
    c.setFillColor(C_WHITE)
    c.drawCentredString(W / 2, H - 168, "CERTIFICATE OF COMPLETION")

    # Accent line under heading
    c.setStrokeColor(C_GREEN)
    c.setLineWidth(1.5)
    c.line(W / 2 - 200, H - 178, W / 2 + 200, H - 178)

    # Sub-label
    c.setFont("Helvetica", 8)
    c.setFillColor(C_GREEN_MID)
    c.drawCentredString(W / 2, H - 193, "C Y B E R S E C U R I T Y   E X C E L L E N C E")

    # ── "This is to certify that" ─────────────────────────────────────────────
    c.setFont("Helvetica-Oblique", 12)
    c.setFillColor(C_GRAY)
    c.drawCentredString(W / 2, H - 232, "This is to certify that")

    # ── Student name ──────────────────────────────────────────────────────────
    name_len = len(student_name)
    name_size = 40 if name_len <= 18 else (34 if name_len <= 26 else (28 if name_len <= 36 else 22))
    c.setFont("Helvetica-Bold", name_size)
    c.setFillColor(C_WHITE)
    c.drawCentredString(W / 2, H - 274, student_name)

    # Name underline (faint)
    name_w = c.stringWidth(student_name, "Helvetica-Bold", name_size)
    c.setStrokeColor(HexColor("#1a3a22"))
    c.setLineWidth(0.5)
    c.line(W / 2 - name_w / 2, H - 282, W / 2 + name_w / 2, H - 282)

    # ── "has successfully completed" ──────────────────────────────────────────
    c.setFont("Helvetica", 12)
    c.setFillColor(C_GRAY)
    c.drawCentredString(W / 2, H - 306, "has successfully completed the course:")

    # ── Course name ───────────────────────────────────────────────────────────
    cname_len = len(course_name)
    cname_size = 24 if cname_len <= 38 else (19 if cname_len <= 55 else 15)
    c.setFont("Helvetica-Bold", cname_size)
    c.setFillColor(C_GREEN)
    c.drawCentredString(W / 2, H - 340, course_name)

    # Separator
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.5)
    c.line(W / 2 - 220, H - 358, W / 2 + 220, H - 358)

    # ── Issue date ────────────────────────────────────────────────────────────
    date_str = issued_at.strftime("%B %d, %Y")
    c.setFont("Helvetica", 11)
    c.setFillColor(C_GRAY)
    c.drawCentredString(W / 2, H - 375, f"Issued on  {date_str}")

    # ── Bottom section ────────────────────────────────────────────────────────
    BY = 104   # base Y for signature lines

    # Left – CyberArcade signature
    c.setStrokeColor(C_DARK)
    c.setLineWidth(0.5)
    c.line(72, BY, 248, BY)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#aabbaa"))
    c.drawString(72, BY - 16, "CyberArcade Platform")
    c.setFont("Helvetica", 8)
    c.setFillColor(C_DARK)
    c.drawString(72, BY - 28, "AUTHORIZED ISSUER")

    # Center – circular seal
    CX, CY = W / 2, BY
    R = 34
    c.setFillColor(C_GREEN_DEEP)
    c.setStrokeColor(C_GREEN_MID)
    c.setLineWidth(0.8)
    c.circle(CX, CY + 10, R, fill=1, stroke=1)
    c.setStrokeColor(C_GREEN)
    c.setLineWidth(0.4)
    c.circle(CX, CY + 10, R - 5, fill=0, stroke=1)

    _draw_hex_logo(c, CX, CY + 24, 0.7)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(C_GREEN)
    c.drawCentredString(CX, CY + 5, "✓ VERIFIED")
    c.setFont("Helvetica", 5.5)
    c.setFillColor(C_GREEN_MID)
    c.drawCentredString(CX, CY - 3, serial_number[:12])
    c.drawCentredString(CX, CY - 10, serial_number[12:])

    # Right – certificate ID / verification
    c.setStrokeColor(C_DARK)
    c.setLineWidth(0.5)
    c.line(W - 248, BY, W - 72, BY)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(HexColor("#aabbaa"))
    c.drawRightString(W - 72, BY - 16, "Certificate of Achievement")
    c.setFont("Helvetica", 8)
    c.setFillColor(C_DARK)
    c.drawRightString(W - 72, BY - 28, "VERIFICATION AUTHORITY")

    # ── Serial watermark (bottom strip) ───────────────────────────────────────
    c.setFont("Helvetica", 6.5)
    c.setFillColor(HexColor("#1a2a1a"))
    c.drawCentredString(
        W / 2, 42,
        f"SERIAL: {serial_number}   •   VERIFY AT: cyberarcade.io/verify/{serial_number}",
    )

    c.save()
