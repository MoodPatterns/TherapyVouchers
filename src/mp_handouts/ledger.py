"""SQLite promo code pool management and atomic batch allocation."""

from __future__ import annotations

import csv
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path("data/ledger.db")

HEADER_LABELS = {
    "promotion code",
    "promo code",
    "promocode",
    "code",
    "codes",
    "voucher",
    "voucher code",
}


class InsufficientCodesError(ValueError):
    """Raised when the unassigned promo code pool has fewer codes than requested."""


@dataclass(frozen=True)
class PromoCode:
    code: str
    campaign: str
    expiry_date: str
    assigned_to: str | None = None
    assigned_at: str | None = None
    batch_id: str | None = None


@dataclass(frozen=True)
class ImportSummary:
    total_valid: int
    inserted: int
    duplicates_skipped: int


@dataclass(frozen=True)
class CampaignStats:
    campaign: str
    expiry_date: str
    total: int
    assigned: int
    unassigned: int


@dataclass(frozen=True)
class BatchRecord:
    batch_id: str
    assigned_to: str
    campaign: str
    expiry_date: str
    assigned_at: str
    count: int


@dataclass(frozen=True)
class LedgerStatus:
    total_codes: int
    total_assigned: int
    total_unassigned: int
    campaigns: list[CampaignStats]
    recent_batches: list[BatchRecord]


def _connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Create the promo_codes table if it does not exist."""
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                campaign TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                assigned_to TEXT,
                assigned_at TEXT,
                batch_id TEXT
            )
            """
        )
    finally:
        conn.close()


def _parse_csv_codes(csv_path: Path | str) -> list[str]:
    """Read codes from a Google Play CSV export, stripping whitespace and ignoring headers/blanks."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    codes: list[str] = []
    content = path.read_text(encoding="utf-8-sig")
    reader = csv.reader(content.splitlines())
    for row in reader:
        if not row:
            continue
        candidate = row[0].strip()
        if not candidate:
            continue
        if candidate.lower() in HEADER_LABELS:
            continue
        codes.append(candidate)
    return codes


def import_csv(
    csv_path: Path | str,
    campaign: str,
    expiry_date: str,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> ImportSummary:
    """Import promo codes from a CSV file into the SQLite ledger with deduplication."""
    campaign_clean = campaign.strip()
    expiry_clean = expiry_date.strip()
    if not campaign_clean:
        raise ValueError("Campaign name must not be empty.")
    if not expiry_clean:
        raise ValueError("Expiry date must not be empty.")

    init_db(db_path)
    raw_codes = _parse_csv_codes(csv_path)

    inserted = 0
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        for code in raw_codes:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO promo_codes (code, campaign, expiry_date)
                VALUES (?, ?, ?)
                """,
                (code, campaign_clean, expiry_clean),
            )
            if cursor.rowcount == 1:
                inserted += 1
        conn.execute("COMMIT")
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()

    return ImportSummary(
        total_valid=len(raw_codes),
        inserted=inserted,
        duplicates_skipped=len(raw_codes) - inserted,
    )


def allocate_batch(
    therapist: str,
    count: int,
    campaign: str | None = None,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> list[PromoCode]:
    """Atomically allocate `count` unassigned codes to `therapist`."""
    therapist_clean = therapist.strip()
    if not therapist_clean:
        raise ValueError("Therapist name must not be empty.")
    if count <= 0:
        raise ValueError("Batch count must be a positive integer.")

    init_db(db_path)
    conn = _connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        if campaign:
            rows = conn.execute(
                """
                SELECT code, campaign, expiry_date
                FROM promo_codes
                WHERE assigned_to IS NULL AND campaign = ?
                ORDER BY rowid ASC
                LIMIT ?
                """,
                (campaign.strip(), count),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT code, campaign, expiry_date
                FROM promo_codes
                WHERE assigned_to IS NULL
                ORDER BY rowid ASC
                LIMIT ?
                """,
                (count,),
            ).fetchall()

        if len(rows) < count:
            available = len(rows)
            conn.execute("ROLLBACK")
            campaign_msg = f" for campaign '{campaign}'" if campaign else ""
            raise InsufficientCodesError(
                f"Requested {count} promo codes{campaign_msg}, "
                f"but only {available} unassigned code(s) remain in the pool."
            )

        now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:6]}"
        selected_codes = [row["code"] for row in rows]

        placeholders = ",".join("?" for _ in selected_codes)
        conn.execute(
            f"""
            UPDATE promo_codes
            SET assigned_to = ?, assigned_at = ?, batch_id = ?
            WHERE code IN ({placeholders})
            """,
            [therapist_clean, now_iso, batch_id, *selected_codes],
        )
        conn.execute("COMMIT")

        return [
            PromoCode(
                code=row["code"],
                campaign=row["campaign"],
                expiry_date=row["expiry_date"],
                assigned_to=therapist_clean,
                assigned_at=now_iso,
                batch_id=batch_id,
            )
            for row in rows
        ]
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def get_status(db_path: Path | str = DEFAULT_DB_PATH) -> LedgerStatus:
    """Return inventory statistics and recent therapist batch allocations."""
    init_db(db_path)
    conn = _connect(db_path)
    try:
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN assigned_to IS NOT NULL THEN 1 ELSE 0 END) AS assigned,
                SUM(CASE WHEN assigned_to IS NULL THEN 1 ELSE 0 END) AS unassigned
            FROM promo_codes
            """
        ).fetchone()

        total_codes = int(totals["total"] or 0)
        total_assigned = int(totals["assigned"] or 0)
        total_unassigned = int(totals["unassigned"] or 0)

        campaign_rows = conn.execute(
            """
            SELECT
                campaign,
                expiry_date,
                COUNT(*) AS total,
                SUM(CASE WHEN assigned_to IS NOT NULL THEN 1 ELSE 0 END) AS assigned,
                SUM(CASE WHEN assigned_to IS NULL THEN 1 ELSE 0 END) AS unassigned
            FROM promo_codes
            GROUP BY campaign, expiry_date
            ORDER BY expiry_date ASC, campaign ASC
            """
        ).fetchall()

        campaigns = [
            CampaignStats(
                campaign=row["campaign"],
                expiry_date=row["expiry_date"],
                total=int(row["total"] or 0),
                assigned=int(row["assigned"] or 0),
                unassigned=int(row["unassigned"] or 0),
            )
            for row in campaign_rows
        ]

        batch_rows = conn.execute(
            """
            SELECT
                batch_id,
                assigned_to,
                campaign,
                expiry_date,
                assigned_at,
                COUNT(*) AS count
            FROM promo_codes
            WHERE batch_id IS NOT NULL
            GROUP BY batch_id, assigned_to, campaign, expiry_date, assigned_at
            ORDER BY assigned_at DESC
            LIMIT 20
            """
        ).fetchall()

        recent_batches = [
            BatchRecord(
                batch_id=row["batch_id"],
                assigned_to=row["assigned_to"],
                campaign=row["campaign"],
                expiry_date=row["expiry_date"],
                assigned_at=row["assigned_at"],
                count=int(row["count"] or 0),
            )
            for row in batch_rows
        ]

        return LedgerStatus(
            total_codes=total_codes,
            total_assigned=total_assigned,
            total_unassigned=total_unassigned,
            campaigns=campaigns,
            recent_batches=recent_batches,
        )
    finally:
        conn.close()

