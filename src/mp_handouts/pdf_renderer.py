"""ReportLab A4 single-page worksheet & voucher layout engine."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from mp_handouts.i18n import get_strings
from mp_handouts.ledger import PromoCode
from mp_handouts.qr import make_app_store_qr, make_help_videos_qr, make_redeem_qr

PAGE_W, PAGE_H = A4
MARGIN_X = 13 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X

DEFAULT_ASSETS_ICON = Path("assets/mp_icon.png")
DEFAULT_OUTPUT_DIR = Path("output")

# Clinical & laser-printer friendly palette
COLOR_NAVY = colors.HexColor("#102A43")
COLOR_SLATE_DARK = colors.HexColor("#243B53")
COLOR_SLATE = colors.HexColor("#486581")
COLOR_MUTED = colors.HexColor("#627D98")
COLOR_BORDER = colors.HexColor("#9FB3C8")
COLOR_BORDER_STRONG = colors.HexColor("#243B53")
COLOR_BG_TINT = colors.HexColor("#F0F4F8")
COLOR_BG_SOFT = colors.HexColor("#F8FAFC")
COLOR_WHITE = colors.HexColor("#FFFFFF")


def sanitize_therapist_name(therapist: str) -> str:
    """Convert a therapist name into a safe filename slug."""
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", therapist.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "Therapist"


def build_output_filename(
    therapist: str,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    date_str: str | None = None,
) -> Path:
    """Return `output/MoodPatterns_Vouchers_{sanitized_therapist}_{YYYY-MM-DD}.pdf`."""
    slug = sanitize_therapist_name(therapist)
    day = date_str or date.today().isoformat()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"MoodPatterns_Vouchers_{slug}_{day}.pdf"


def _draw_paragraph(
    c: canvas.Canvas,
    text: str,
    style: ParagraphStyle,
    x: float,
    y_top: float,
    max_width: float,
    max_height: float,
) -> float:
    """Wrap and draw a Paragraph whose top edge is at `y_top`. Returns bottom `y`."""
    para = Paragraph(text, style)
    _, h = para.wrapOn(c, max_width, max_height)
    if h > max_height:
        raise ValueError(
            f"Paragraph overflow: required height {h:.1f}pt exceeds max {max_height:.1f}pt "
            f"for text: {text[:60]}..."
        )
    y_bottom = y_top - h
    para.drawOn(c, x, y_bottom)
    return y_bottom


def _draw_checkbox(c: canvas.Canvas, x: float, y: float, size: float = 3.4 * mm) -> None:
    """Draw a crisp printable square checkbox at `(x, y)`."""
    c.saveState()
    c.setStrokeColor(COLOR_SLATE_DARK)
    c.setFillColor(COLOR_WHITE)
    c.setLineWidth(0.9)
    c.roundRect(x, y, size, size, radius=0.6 * mm, stroke=1, fill=1)
    c.restoreState()


def _render_voucher_page(
    c: canvas.Canvas,
    voucher: PromoCode,
    index: int,
    total: int,
    strings: dict[str, str],
    therapist: str | None,
    app_qr_reader: ImageReader,
    help_qr_reader: ImageReader,
    icon_path: Path | None,
) -> None:
    """Render a single A4 therapist handout & voucher page onto `c`."""
    body_style = ParagraphStyle(
        name="Body",
        fontName="Helvetica",
        fontSize=8.4,
        leading=11.0,
        alignment=TA_LEFT,
        textColor=COLOR_NAVY,
    )
    transparency_style = ParagraphStyle(
        name="Transparency",
        fontName="Helvetica",
        fontSize=7.7,
        leading=9.8,
        alignment=TA_LEFT,
        textColor=COLOR_SLATE_DARK,
    )

    # =========================================================================
    # 1. HEADER BANNER (y = 264mm .. 286mm, height = 22mm)
    # =========================================================================
    header_y = 264 * mm
    header_h = 22 * mm
    c.saveState()
    c.setFillColor(COLOR_BG_TINT)
    c.setStrokeColor(COLOR_BORDER_STRONG)
    c.setLineWidth(1.1)
    c.roundRect(MARGIN_X, header_y, CONTENT_W, header_h, radius=2.5 * mm, stroke=1, fill=1)
    c.restoreState()

    text_x = MARGIN_X + 4 * mm
    if icon_path and icon_path.exists():
        try:
            c.drawImage(
                str(icon_path),
                MARGIN_X + 3.5 * mm,
                header_y + 4 * mm,
                width=14 * mm,
                height=14 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
            text_x = MARGIN_X + 20 * mm
        except Exception:
            text_x = MARGIN_X + 4 * mm

    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 12.2)
    c.drawString(text_x, header_y + 15.2 * mm, strings["header_title"])

    c.setFillColor(COLOR_SLATE_DARK)
    c.setFont("Helvetica-Oblique", 8.2)
    c.drawString(text_x, header_y + 10.3 * mm, strings["header_subtitle"])

    effective_therapist = (therapist or voucher.assigned_to or "").strip()
    if effective_therapist:
        badge_text = strings["provided_by"].format(therapist=effective_therapist)
        c.setFont("Helvetica-Bold", 8.0)
        c.setFillColor(COLOR_SLATE_DARK)
        c.drawString(text_x, header_y + 4.2 * mm, badge_text)

    # =========================================================================
    # 2. SECTION 1: PRIVACY GUARANTEE BOX (y = 224mm .. 260.5mm, height = 36.5mm)
    # =========================================================================
    sec1_y = 224 * mm
    sec1_h = 36.5 * mm
    c.saveState()
    c.setFillColor(COLOR_BG_SOFT)
    c.setStrokeColor(COLOR_BORDER_STRONG)
    c.setLineWidth(0.9)
    c.roundRect(MARGIN_X, sec1_y, CONTENT_W, sec1_h, radius=2.2 * mm, stroke=1, fill=1)
    c.restoreState()

    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 9.8)
    c.drawString(MARGIN_X + 4 * mm, sec1_y + sec1_h - 5.5 * mm, strings["sec1_title"])

    bullet_x = MARGIN_X + 8 * mm
    bullet_w = CONTENT_W - 12 * mm

    # Bullet 1
    c.setFont("Helvetica-Bold", 9.0)
    c.drawString(MARGIN_X + 4.5 * mm, sec1_y + sec1_h - 10.2 * mm, "•")
    b1_bottom = _draw_paragraph(
        c,
        strings["sec1_bullet1"],
        body_style,
        bullet_x,
        sec1_y + sec1_h - 7.3 * mm,
        bullet_w,
        18 * mm,
    )

    # Bullet 2
    b2_top = b1_bottom - 1.5 * mm
    c.setFont("Helvetica-Bold", 9.0)
    c.drawString(MARGIN_X + 4.5 * mm, b2_top - 2.9 * mm, "•")
    _draw_paragraph(
        c,
        strings["sec1_bullet2"],
        body_style,
        bullet_x,
        b2_top,
        bullet_w,
        12 * mm,
    )

    # =========================================================================
    # 3. SECTION 2: THERAPIST FILL-IN WORKSHEET (y = 167.5mm .. 220.5mm, height = 53mm)
    # =========================================================================
    sec2_y = 167.5 * mm
    sec2_h = 53 * mm
    c.saveState()
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.9)
    c.roundRect(MARGIN_X, sec2_y, CONTENT_W, sec2_h, radius=2.2 * mm, stroke=1, fill=1)
    c.restoreState()

    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 9.8)
    c.drawString(MARGIN_X + 4 * mm, sec2_y + sec2_h - 5.5 * mm, strings["sec2_title"])

    title_w = c.stringWidth(strings["sec2_title"], "Helvetica-Bold", 9.8)
    c.setFillColor(COLOR_MUTED)
    c.setFont("Helvetica-Oblique", 7.8)
    c.drawString(
        MARGIN_X + 6 * mm + title_w,
        sec2_y + sec2_h - 5.5 * mm,
        strings["sec2_subtitle"],
    )

    # Check-in prompts row
    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(MARGIN_X + 4 * mm, sec2_y + 40.5 * mm, strings["sec2_prompts_label"])

    opt_y = sec2_y + 34.0 * mm
    options = [
        (MARGIN_X + 6 * mm, strings["sec2_opt_2x"]),
        (MARGIN_X + 38 * mm, strings["sec2_opt_3x"]),
        (MARGIN_X + 70 * mm, strings["sec2_opt_4x"]),
        (MARGIN_X + 102 * mm, strings["sec2_opt_custom"]),
    ]
    c.setFont("Helvetica", 8.5)
    for ox, label in options:
        _draw_checkbox(c, ox, opt_y - 0.5 * mm)
        c.drawString(ox + 5 * mm, opt_y, label)

    # Custom write-in line
    c.saveState()
    c.setStrokeColor(COLOR_SLATE)
    c.setLineWidth(0.6)
    c.line(MARGIN_X + 132 * mm, opt_y - 0.5 * mm, MARGIN_X + CONTENT_W - 5 * mm, opt_y - 0.5 * mm)
    c.restoreState()

    # Key scales / symptoms to observe
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(MARGIN_X + 4 * mm, sec2_y + 26.0 * mm, strings["sec2_scales_label"])
    c.saveState()
    c.setStrokeColor(COLOR_SLATE)
    c.setLineWidth(0.6)
    c.line(MARGIN_X + 4 * mm, sec2_y + 19.5 * mm, MARGIN_X + CONTENT_W - 5 * mm, sec2_y + 19.5 * mm)
    c.restoreState()

    # Contexts, periods, or volatility alerts
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(MARGIN_X + 4 * mm, sec2_y + 12.0 * mm, strings["sec2_contexts_label"])
    c.saveState()
    c.setStrokeColor(COLOR_SLATE)
    c.setLineWidth(0.6)
    c.line(MARGIN_X + 4 * mm, sec2_y + 5.5 * mm, MARGIN_X + CONTENT_W - 5 * mm, sec2_y + 5.5 * mm)
    c.restoreState()

    # =========================================================================
    # 4. SECTION 3: GETTING STARTED IN 3 STEPS + ANDROID EMA CHECKLIST
    #    (y = 96.5mm .. 164mm, height = 67.5mm)
    # =========================================================================
    sec3_y = 96.5 * mm
    sec3_h = 67.5 * mm
    c.saveState()
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.9)
    c.roundRect(MARGIN_X, sec3_y, CONTENT_W, sec3_h, radius=2.2 * mm, stroke=1, fill=1)
    c.restoreState()

    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 9.8)
    c.drawString(MARGIN_X + 4 * mm, sec3_y + sec3_h - 5.5 * mm, strings["sec3_title"])

    s3_x = MARGIN_X + 4 * mm
    s3_w = CONTENT_W - 8 * mm

    # Step 1
    y_cursor = _draw_paragraph(
        c,
        strings["sec3_step1"],
        body_style,
        s3_x,
        sec3_y + sec3_h - 7.5 * mm,
        s3_w,
        10 * mm,
    )

    # Step 2 header
    y_cursor = _draw_paragraph(
        c,
        strings["sec3_step2_header"],
        body_style,
        s3_x,
        y_cursor - 1.5 * mm,
        s3_w,
        6 * mm,
    )

    # Step 2 Check 1
    chk1_top = y_cursor - 1.2 * mm
    _draw_checkbox(c, s3_x + 2 * mm, chk1_top - 3.4 * mm)
    y_cursor = _draw_paragraph(
        c,
        strings["sec3_step2_check1"],
        body_style,
        s3_x + 7.5 * mm,
        chk1_top,
        s3_w - 7.5 * mm,
        9 * mm,
    )

    # Step 2 Check 2
    chk2_top = y_cursor - 1.2 * mm
    _draw_checkbox(c, s3_x + 2 * mm, chk2_top - 3.4 * mm)
    y_cursor = _draw_paragraph(
        c,
        strings["sec3_step2_check2"],
        body_style,
        s3_x + 7.5 * mm,
        chk2_top,
        s3_w - 7.5 * mm,
        9 * mm,
    )

    # Step 3
    y_cursor = _draw_paragraph(
        c,
        strings["sec3_step3"],
        body_style,
        s3_x,
        y_cursor - 1.8 * mm,
        s3_w,
        10 * mm,
    )

    # Transparency Note Box inside bottom of Section 3
    trans_box_y = sec3_y + 2.5 * mm
    trans_box_h = 15.0 * mm
    c.saveState()
    c.setFillColor(COLOR_BG_SOFT)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.6)
    c.roundRect(
        MARGIN_X + 3.5 * mm,
        trans_box_y,
        CONTENT_W - 7 * mm,
        trans_box_h,
        radius=1.5 * mm,
        stroke=1,
        fill=1,
    )
    c.restoreState()

    _draw_paragraph(
        c,
        strings["sec3_transparency"],
        transparency_style,
        MARGIN_X + 6 * mm,
        trans_box_y + trans_box_h - 1.6 * mm,
        CONTENT_W - 12 * mm,
        trans_box_h - 2 * mm,
    )

    # =========================================================================
    # 5. DASHED CUT-OFF LINE (y = 93mm)
    # =========================================================================
    cut_y = 93 * mm
    c.saveState()
    c.setStrokeColor(COLOR_MUTED)
    c.setLineWidth(0.7)
    c.setDash(3, 3)
    c.line(MARGIN_X, cut_y, MARGIN_X + CONTENT_W, cut_y)
    c.restoreState()

    cut_label = f"✂  {strings['cut_line_label']}  ✂"
    label_w = c.stringWidth(cut_label, "Helvetica", 7.2) + 6 * mm
    c.saveState()
    c.setFillColor(COLOR_WHITE)
    c.rect((PAGE_W - label_w) / 2, cut_y - 1.5 * mm, label_w, 3.2 * mm, stroke=0, fill=1)
    c.setFillColor(COLOR_MUTED)
    c.setFont("Helvetica", 7.2)
    c.drawCentredString(PAGE_W / 2, cut_y - 0.8 * mm, cut_label)
    c.restoreState()

    # =========================================================================
    # 6. SECTION 4: PERSONAL 90-DAY PRO VOUCHER CARD (y = 11mm .. 89.5mm)
    # =========================================================================
    sec4_y = 11 * mm
    sec4_h = 78.5 * mm
    left_w = 80 * mm
    right_w = CONTENT_W - left_w - 4 * mm
    right_x = MARGIN_X + left_w + 4 * mm

    # --- Left Column: App Store QR + Help Videos QR ---
    c.saveState()
    c.setFillColor(COLOR_BG_SOFT)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.9)
    c.roundRect(MARGIN_X, sec4_y, left_w, sec4_h, radius=2.2 * mm, stroke=1, fill=1)
    c.restoreState()

    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 9.0)
    c.drawString(MARGIN_X + 3.5 * mm, sec4_y + sec4_h - 5.2 * mm, strings["sec4_left_title"])

    # Top QR: App Store Install QR
    qr_small = 24.5 * mm
    app_qr_y = sec4_y + 43.0 * mm
    c.drawImage(
        app_qr_reader,
        MARGIN_X + 2.5 * mm,
        app_qr_y,
        width=qr_small,
        height=qr_small,
        preserveAspectRatio=True,
    )
    info_x = MARGIN_X + 28.5 * mm
    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 8.0)
    c.drawString(info_x, app_qr_y + 17.5 * mm, strings["sec4_app_qr_label"])
    c.setFillColor(COLOR_SLATE_DARK)
    c.setFont("Helvetica", 6.8)
    c.drawString(info_x, app_qr_y + 12.5 * mm, strings["sec4_app_qr_sub"])
    c.setFillColor(COLOR_MUTED)
    c.setFont("Helvetica-Oblique", 6.8)
    c.drawString(info_x, app_qr_y + 7.5 * mm, "Google Play Store")

    # Divider between left column QRs
    c.saveState()
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.5)
    c.line(MARGIN_X + 3.5 * mm, sec4_y + 39.5 * mm, MARGIN_X + left_w - 3.5 * mm, sec4_y + 39.5 * mm)
    c.restoreState()

    # Bottom QR: Help Videos QR
    help_qr_y = sec4_y + 11.0 * mm
    c.drawImage(
        help_qr_reader,
        MARGIN_X + 2.5 * mm,
        help_qr_y,
        width=qr_small,
        height=qr_small,
        preserveAspectRatio=True,
    )
    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 8.0)
    c.drawString(info_x, help_qr_y + 17.5 * mm, strings["sec4_help_qr_label"])
    c.setFillColor(COLOR_SLATE_DARK)
    c.setFont("Helvetica", 6.4)
    c.drawString(info_x, help_qr_y + 12.0 * mm, strings["sec4_help_qr_sub1"])
    c.drawString(info_x, help_qr_y + 7.0 * mm, strings["sec4_help_qr_sub2"])

    # --- Right Column: Prominent Personal Voucher Box ---
    c.saveState()
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(COLOR_BORDER_STRONG)
    c.setLineWidth(1.5)
    c.roundRect(right_x, sec4_y, right_w, sec4_h, radius=2.5 * mm, stroke=1, fill=1)
    c.restoreState()

    right_center_x = right_x + right_w / 2

    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawCentredString(right_center_x, sec4_y + sec4_h - 5.8 * mm, strings["sec4_right_title"])

    c.setFillColor(COLOR_SLATE_DARK)
    c.setFont("Helvetica", 7.3)
    c.drawCentredString(right_center_x, sec4_y + sec4_h - 10.2 * mm, strings["sec4_right_subtitle"])

    # Dynamic Voucher Redemption QR
    redeem_img = make_redeem_qr(voucher.code)
    redeem_reader = ImageReader(redeem_img)
    qr_large = 37 * mm
    c.drawImage(
        redeem_reader,
        right_center_x - qr_large / 2,
        sec4_y + 29.5 * mm,
        width=qr_large,
        height=qr_large,
        preserveAspectRatio=True,
    )

    # Backup Code Label
    c.setFillColor(COLOR_SLATE_DARK)
    c.setFont("Helvetica", 7.8)
    c.drawCentredString(right_center_x, sec4_y + 25.2 * mm, strings["sec4_backup_label"])

    # Monospace Backup Code Frame
    pill_w = 76 * mm
    pill_h = 7.5 * mm
    pill_x = right_center_x - pill_w / 2
    pill_y = sec4_y + 16.2 * mm
    c.saveState()
    c.setFillColor(COLOR_BG_TINT)
    c.setStrokeColor(COLOR_BORDER_STRONG)
    c.setLineWidth(0.8)
    c.roundRect(pill_x, pill_y, pill_w, pill_h, radius=1.5 * mm, stroke=1, fill=1)
    c.restoreState()

    c.setFillColor(COLOR_NAVY)
    c.setFont("Courier-Bold", 11.5)
    c.drawCentredString(right_center_x, pill_y + 2.1 * mm, voucher.code)

    # Expiry Date
    expiry_text = strings["sec4_expiry_label"].format(expiry=voucher.expiry_date)
    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(right_center_x, sec4_y + 10.2 * mm, expiry_text)

    # Page/Voucher Counter in small muted text at bottom corner
    counter_text = strings["sec4_counter"].format(i=index, n=total)
    c.setFillColor(COLOR_MUTED)
    c.setFont("Helvetica", 7.2)
    c.drawRightString(right_x + right_w - 3.5 * mm, sec4_y + 3.0 * mm, counter_text)


def render_voucher_packet(
    vouchers: Sequence[PromoCode],
    output_path: Path | str,
    therapist: str | None = None,
    lang: str = "en",
    icon_path: Path | str | None = DEFAULT_ASSETS_ICON,
) -> Path:
    """Render a multi-page A4 PDF handout packet (exact 1 page per promo code)."""
    if not vouchers:
        raise ValueError("Cannot render PDF packet for an empty voucher list.")

    strings = get_strings(lang)
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Pre-generate static QR codes once per batch
    app_qr_reader = ImageReader(make_app_store_qr())
    help_qr_reader = ImageReader(make_help_videos_qr())
    resolved_icon = Path(icon_path) if icon_path else None

    c = canvas.Canvas(str(out_file), pagesize=A4)
    c.setTitle(f"Mood Patterns Vouchers ({lang.upper()})")
    c.setAuthor("Mood Patterns (info.moodpatterns.moodpatterns)")

    total = len(vouchers)
    for idx, voucher in enumerate(vouchers, start=1):
        _render_voucher_page(
            c=c,
            voucher=voucher,
            index=idx,
            total=total,
            strings=strings,
            therapist=therapist,
            app_qr_reader=app_qr_reader,
            help_qr_reader=help_qr_reader,
            icon_path=resolved_icon,
        )
        c.showPage()

    c.save()
    return out_file
