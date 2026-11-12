"""High-resolution QR code image generator for Mood Patterns handouts."""

from __future__ import annotations

import qrcode
from PIL import Image
from qrcode.constants import ERROR_CORRECT_M

REDEEM_URL_TEMPLATE = "https://play.google.com/redeem?code={code}"
APP_STORE_URL = "https://play.google.com/store/apps/details?id=info.moodpatterns.moodpatterns"
HELP_VIDEOS_URL = "https://www.youtube.com/@moodpatternsapp7631"
THERAPY_WEB_URL = "https://moodpatterns.info/moodpatterns/therapy.html"


def make_qr_image(url: str, box_size: int = 10, border: int = 2) -> Image.Image:
    """Generate a high-resolution black-on-white QR code PIL Image."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img.convert("RGB")


def make_redeem_qr(code: str) -> Image.Image:
    """Generate a dynamic Google Play voucher redemption QR code."""
    clean_code = code.strip()
    url = REDEEM_URL_TEMPLATE.format(code=clean_code)
    return make_qr_image(url, box_size=12, border=2)


def make_app_store_qr() -> Image.Image:
    """Generate a static Google Play Store listing QR code for Mood Patterns."""
    return make_qr_image(APP_STORE_URL, box_size=10, border=2)


def make_help_videos_qr() -> Image.Image:
    """Generate a static QR code linking to Mood Patterns help videos."""
    return make_qr_image(HELP_VIDEOS_URL, box_size=10, border=2)

