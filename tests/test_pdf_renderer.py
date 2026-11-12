"""Unit tests for A4 PDF voucher rendering, page counts, and QR generation."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from typer.testing import CliRunner

from mp_handouts.cli import app
from mp_handouts.ledger import PromoCode
from mp_handouts.pdf_renderer import build_output_filename, render_voucher_packet
from mp_handouts.qr import make_app_store_qr, make_help_videos_qr, make_redeem_qr

runner = CliRunner()


def _make_dummy_vouchers(n: int) -> list[PromoCode]:
    return [
        PromoCode(
            code=f"TEST-90PR-CODE-{i:04d}",
            campaign="UNIT-TEST",
            expiry_date="2027-09-30",
            assigned_to="Dr. Jane Smith",
            assigned_at="2026-11-12T20:00:00+00:00",
            batch_id="batch_test_01",
        )
        for i in range(1, n + 1)
    ]


@pytest.mark.parametrize("lang", ["en", "de"])
@pytest.mark.parametrize("count", [1, 3, 7])
def test_pdf_exact_page_count_and_a4_dimensions(
    tmp_path: Path, lang: str, count: int
) -> None:
    vouchers = _make_dummy_vouchers(count)
    pdf_path = tmp_path / f"vouchers_{lang}_{count}.pdf"

    result_path = render_voucher_packet(
        vouchers=vouchers,
        output_path=pdf_path,
        therapist="Dr. Jane Smith",
        lang=lang,
    )
    assert result_path.exists()

    reader = PdfReader(str(result_path))
    assert len(reader.pages) == count

    expected_w, expected_h = A4
    for idx, page in enumerate(reader.pages, start=1):
        box = page.mediabox
        assert float(box.width) == pytest.approx(expected_w, abs=0.5)
        assert float(box.height) == pytest.approx(expected_h, abs=0.5)

        text = page.extract_text()
        assert vouchers[idx - 1].code in text
        assert "2027-09-30" in text
        assert "Dr. Jane Smith" in text
        assert f"Voucher {idx} of {count}" in text


def test_pdf_graceful_fallback_without_logo(tmp_path: Path) -> None:
    vouchers = _make_dummy_vouchers(2)
    pdf_path = tmp_path / "no_icon.pdf"

    render_voucher_packet(
        vouchers=vouchers,
        output_path=pdf_path,
        therapist="Practice Without Icon",
        lang="en",
        icon_path=tmp_path / "missing_icon.png",
    )
    reader = PdfReader(str(pdf_path))
    assert len(reader.pages) == 2


def test_qr_generators_produce_valid_images() -> None:
    redeem_img = make_redeem_qr("PROMO-1234")
    app_img = make_app_store_qr()
    help_img = make_help_videos_qr()

    for img in (redeem_img, app_img, help_img):
        assert img.mode == "RGB"
        assert img.width > 100
        assert img.height == img.width


def test_build_output_filename_sanitization(tmp_path: Path) -> None:
    out = build_output_filename(
        therapist="Dr. Jane Smith / Practice & Co.",
        output_dir=tmp_path,
        date_str="2026-11-12",
    )
    assert out.name == "MoodPatterns_Vouchers_Dr_Jane_Smith_Practice_Co_2026-11-12.pdf"


def test_cli_demo_command_generates_en_and_de_pdfs(tmp_path: Path) -> None:
    res = runner.invoke(app, ["demo", "--output-dir", str(tmp_path)])
    assert res.exit_code == 0

    en_pdf = tmp_path / "demo_en.pdf"
    de_pdf = tmp_path / "demo_de.pdf"
    assert en_pdf.exists()
    assert de_pdf.exists()

    assert len(PdfReader(str(en_pdf)).pages) == 3
    assert len(PdfReader(str(de_pdf)).pages) == 3

