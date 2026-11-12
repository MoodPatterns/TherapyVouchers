"""Typer CLI commands for Mood Patterns Therapist Voucher & Handout Generator."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mp_handouts.i18n import SUPPORTED_LANGUAGES
from mp_handouts.ledger import (
    DEFAULT_DB_PATH,
    InsufficientCodesError,
    PromoCode,
    allocate_batch,
    get_status,
    import_csv,
)
from mp_handouts.pdf_renderer import (
    DEFAULT_OUTPUT_DIR,
    build_output_filename,
    render_voucher_packet,
)

app = typer.Typer(
    name="mp-handouts",
    help="Mood Patterns Therapist Voucher & Handout Generator.",
    no_args_is_help=True,
)
console = Console()


@app.command("import-csv")
def cmd_import_csv(
    csv_path: Annotated[
        Path,
        typer.Argument(help="Path to the Google Play Console promo codes CSV export."),
    ],
    campaign: Annotated[
        str,
        typer.Option("--campaign", "-c", help="Campaign label (e.g. 'Q4-2026')."),
    ],
    expiry: Annotated[
        str,
        typer.Option("--expiry", "-e", help="Promo code expiry date in YYYY-MM-DD format."),
    ],
    db_path: Annotated[
        Path,
        typer.Option("--db", help="Path to SQLite ledger database."),
    ] = DEFAULT_DB_PATH,
) -> None:
    """Import promo codes from a CSV file into the SQLite ledger."""
    try:
        summary = import_csv(
            csv_path=csv_path,
            campaign=campaign,
            expiry_date=expiry,
            db_path=db_path,
        )
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(
        Panel.fit(
            f"[bold green]CSV Import Complete[/bold green]\n"
            f"• Campaign: [cyan]{campaign}[/cyan]\n"
            f"• Expiry Date: [cyan]{expiry}[/cyan]\n"
            f"• Valid codes read: [bold]{summary.total_valid}[/bold]\n"
            f"• Newly inserted: [bold green]{summary.inserted}[/bold green]\n"
            f"• Duplicates skipped: [yellow]{summary.duplicates_skipped}[/yellow]",
            title="mp-handouts Ledger",
        )
    )


@app.command("generate")
def cmd_generate(
    therapist: Annotated[
        str,
        typer.Option("--therapist", "-t", help="Therapist or practice name."),
    ],
    count: Annotated[
        int,
        typer.Option("--count", "-n", help="Number of voucher pages to allocate and render."),
    ],
    lang: Annotated[
        str,
        typer.Option("--lang", "-l", help="Handout language ('en' or 'de')."),
    ] = "en",
    campaign: Annotated[
        Optional[str],
        typer.Option("--campaign", "-c", help="Optional campaign filter."),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Directory for generated PDF packets."),
    ] = DEFAULT_OUTPUT_DIR,
    db_path: Annotated[
        Path,
        typer.Option("--db", help="Path to SQLite ledger database."),
    ] = DEFAULT_DB_PATH,
) -> None:
    """Allocate unused promo codes to a therapist and generate their A4 PDF packet."""
    lang_clean = lang.strip().lower()
    if lang_clean not in SUPPORTED_LANGUAGES:
        console.print(
            f"[bold red]Error:[/bold red] Unsupported language '{lang}'. "
            f"Choose from: {', '.join(SUPPORTED_LANGUAGES)}"
        )
        raise typer.Exit(code=1)

    try:
        vouchers = allocate_batch(
            therapist=therapist,
            count=count,
            campaign=campaign,
            db_path=db_path,
        )
    except (InsufficientCodesError, ValueError) as exc:
        console.print(f"[bold red]Allocation Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    output_path = build_output_filename(therapist=therapist, output_dir=output_dir)
    render_voucher_packet(
        vouchers=vouchers,
        output_path=output_path,
        therapist=therapist,
        lang=lang_clean,
    )

    batch_id = vouchers[0].batch_id if vouchers else "N/A"
    console.print(
        Panel.fit(
            f"[bold green]PDF Handout Packet Generated[/bold green]\n"
            f"• Therapist: [cyan]{therapist}[/cyan]\n"
            f"• Codes Allocated: [bold]{len(vouchers)}[/bold]\n"
            f"• Language: [bold]{lang_clean.upper()}[/bold]\n"
            f"• Batch ID: [dim]{batch_id}[/dim]\n"
            f"• Output PDF: [bold underline]{output_path}[/bold underline]",
            title="mp-handouts Generator",
        )
    )


@app.command("status")
def cmd_status(
    db_path: Annotated[
        Path,
        typer.Option("--db", help="Path to SQLite ledger database."),
    ] = DEFAULT_DB_PATH,
) -> None:
    """Display remaining unassigned promo codes and recent therapist allocations."""
    status = get_status(db_path=db_path)

    console.print(
        Panel.fit(
            f"Total Codes: [bold]{status.total_codes}[/bold]   |   "
            f"Assigned: [yellow]{status.total_assigned}[/yellow]   |   "
            f"Unassigned (Available): [bold green]{status.total_unassigned}[/bold green]",
            title="Promo Code Pool Summary",
        )
    )

    camp_table = Table(title="Inventory by Campaign & Expiry")
    camp_table.add_column("Campaign", style="cyan")
    camp_table.add_column("Expiry Date", style="magenta")
    camp_table.add_column("Total", justify="right")
    camp_table.add_column("Assigned", justify="right", style="yellow")
    camp_table.add_column("Remaining", justify="right", style="bold green")

    if status.campaigns:
        for c in status.campaigns:
            camp_table.add_row(
                c.campaign,
                c.expiry_date,
                str(c.total),
                str(c.assigned),
                str(c.unassigned),
            )
    else:
        camp_table.add_row("—", "—", "0", "0", "0")
    console.print(camp_table)

    batch_table = Table(title="Recent Therapist Batch Allocations")
    batch_table.add_column("Batch ID", style="dim")
    batch_table.add_column("Therapist", style="cyan")
    batch_table.add_column("Campaign")
    batch_table.add_column("Count", justify="right", style="bold")
    batch_table.add_column("Assigned At (UTC)", style="green")

    if status.recent_batches:
        for b in status.recent_batches:
            batch_table.add_row(
                b.batch_id,
                b.assigned_to,
                b.campaign,
                str(b.count),
                b.assigned_at,
            )
    else:
        batch_table.add_row("—", "No batches allocated yet", "—", "0", "—")
    console.print(batch_table)


@app.command("demo")
def cmd_demo(
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Directory for demo PDF files."),
    ] = DEFAULT_OUTPUT_DIR,
) -> None:
    """Generate 3-page sample PDFs in English and German without touching the SQLite ledger."""
    demo_vouchers_en = [
        PromoCode(
            code=f"DEMO-90PR-EN0{i}-XXXX",
            campaign="DEMO-CAMPAIGN",
            expiry_date="2027-06-30",
            assigned_to="Dr. Jane Smith, Clinical Psychology",
            batch_id="demo_en",
        )
        for i in range(1, 4)
    ]
    demo_vouchers_de = [
        PromoCode(
            code=f"DEMO-90PR-DE0{i}-XXXX",
            campaign="DEMO-CAMPAIGN",
            expiry_date="2027-06-30",
            assigned_to="Praxis Dr. Anna Müller",
            batch_id="demo_de",
        )
        for i in range(1, 4)
    ]

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    en_path = out_dir / "demo_en.pdf"
    de_path = out_dir / "demo_de.pdf"

    render_voucher_packet(
        vouchers=demo_vouchers_en,
        output_path=en_path,
        therapist="Dr. Jane Smith, Clinical Psychology",
        lang="en",
    )
    render_voucher_packet(
        vouchers=demo_vouchers_de,
        output_path=de_path,
        therapist="Praxis Dr. Anna Müller",
        lang="de",
    )

    console.print(
        Panel.fit(
            f"[bold green]Demo Handouts Generated Successfully[/bold green]\n"
            f"• English (3 pages): [bold underline]{en_path}[/bold underline]\n"
            f"• German  (3 pages): [bold underline]{de_path}[/bold underline]",
            title="mp-handouts Demo",
        )
    )


if __name__ == "__main__":
    app()

