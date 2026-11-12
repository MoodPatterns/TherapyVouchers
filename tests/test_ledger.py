"""Unit tests for SQLite promo code ledger, CSV deduplication, and atomic batch allocation."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from mp_handouts.cli import app
from mp_handouts.ledger import (
    InsufficientCodesError,
    allocate_batch,
    get_status,
    import_csv,
)

runner = CliRunner()


def test_import_csv_deduplication_and_header_ignoring(tmp_path: Path) -> None:
    db_file = tmp_path / "ledger.db"
    csv_file = tmp_path / "codes.csv"
    csv_file.write_text(
        "Promotion code\n"
        "  CODE-AAA-111  \n"
        "\n"
        "Code\n"
        "CODE-BBB-222\n"
        "CODE-AAA-111\n"
        "CODE-CCC-333\n",
        encoding="utf-8",
    )

    summary1 = import_csv(
        csv_path=csv_file,
        campaign="Q4-2026",
        expiry_date="2027-03-31",
        db_path=db_file,
    )
    assert summary1.total_valid == 4
    assert summary1.inserted == 3
    assert summary1.duplicates_skipped == 1

    # Re-importing the same file plus one new code should skip existing 3 codes
    csv_file_2 = tmp_path / "codes2.csv"
    csv_file_2.write_text(
        "Promo Code\n"
        "CODE-BBB-222\n"
        "CODE-DDD-444\n",
        encoding="utf-8",
    )
    summary2 = import_csv(
        csv_path=csv_file_2,
        campaign="Q4-2026",
        expiry_date="2027-03-31",
        db_path=db_file,
    )
    assert summary2.total_valid == 2
    assert summary2.inserted == 1
    assert summary2.duplicates_skipped == 1

    status = get_status(db_path=db_file)
    assert status.total_codes == 4
    assert status.total_unassigned == 4
    assert status.total_assigned == 0


def test_atomic_batch_allocation_no_duplicates(tmp_path: Path) -> None:
    db_file = tmp_path / "ledger.db"
    csv_file = tmp_path / "codes.csv"
    codes = [f"MP-CODE-{i:03d}" for i in range(1, 11)]
    csv_file.write_text("Promotion code\n" + "\n".join(codes), encoding="utf-8")

    import_csv(csv_file, campaign="CampA", expiry_date="2027-12-31", db_path=db_file)

    batch1 = allocate_batch("Dr. Alice", count=4, db_path=db_file)
    batch2 = allocate_batch("Dr. Bob", count=6, db_path=db_file)

    assert len(batch1) == 4
    assert len(batch2) == 6

    codes1 = {c.code for c in batch1}
    codes2 = {c.code for c in batch2}
    assert codes1.isdisjoint(codes2)
    assert codes1 | codes2 == set(codes)

    for item in batch1:
        assert item.assigned_to == "Dr. Alice"
        assert item.assigned_at is not None
        assert item.batch_id is not None

    status = get_status(db_path=db_file)
    assert status.total_codes == 10
    assert status.total_assigned == 10
    assert status.total_unassigned == 0
    assert len(status.recent_batches) == 2


def test_atomic_allocation_insufficient_codes_rolls_back(tmp_path: Path) -> None:
    db_file = tmp_path / "ledger.db"
    csv_file = tmp_path / "codes.csv"
    csv_file.write_text("Promotion code\nONLY-ONE-1\nONLY-TWO-2\n", encoding="utf-8")

    import_csv(csv_file, campaign="CampA", expiry_date="2027-12-31", db_path=db_file)

    with pytest.raises(InsufficientCodesError, match="only 2 unassigned"):
        allocate_batch("Dr. Jane", count=5, db_path=db_file)

    # Ensure database was not modified when allocation failed
    status = get_status(db_path=db_file)
    assert status.total_unassigned == 2
    assert status.total_assigned == 0
    assert status.recent_batches == []


def test_cli_workflow_import_status_and_generate(tmp_path: Path) -> None:
    db_file = tmp_path / "cli_ledger.db"
    out_dir = tmp_path / "out"
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "Promotion code\nCLI-CODE-1\nCLI-CODE-2\nCLI-CODE-3\n",
        encoding="utf-8",
    )

    res_import = runner.invoke(
        app,
        [
            "import-csv",
            str(csv_file),
            "--campaign",
            "CLI-CAMP",
            "--expiry",
            "2027-05-01",
            "--db",
            str(db_file),
        ],
    )
    assert res_import.exit_code == 0

    res_gen = runner.invoke(
        app,
        [
            "generate",
            "--therapist",
            "Dr. Clara Oswald",
            "--count",
            "2",
            "--lang",
            "en",
            "--output-dir",
            str(out_dir),
            "--db",
            str(db_file),
        ],
    )
    assert res_gen.exit_code == 0

    generated_pdfs = list(out_dir.glob("MoodPatterns_Vouchers_Dr_Clara_Oswald_*.pdf"))
    assert len(generated_pdfs) == 1

    # Requesting 2 more should fail cleanly with exit_code == 1 since only 1 remains
    res_fail = runner.invoke(
        app,
        [
            "generate",
            "--therapist",
            "Dr. Clara Oswald",
            "--count",
            "2",
            "--output-dir",
            str(out_dir),
            "--db",
            str(db_file),
        ],
    )
    assert res_fail.exit_code == 1

    res_status = runner.invoke(app, ["status", "--db", str(db_file)])
    assert res_status.exit_code == 0
    assert "Dr. Clara Oswald" in res_status.stdout

