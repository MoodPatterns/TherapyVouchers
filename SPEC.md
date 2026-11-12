# Antigravity Handoff: Mood Patterns Therapist Voucher & Handout Generator (`mp-handouts`)

## 1. Project Objective
Build a CLI tool and Python framework that ingests a Google Play Console one-time promo code CSV export and generates print-ready, multi-page A4 PDF packets (1 page per client voucher) for psychotherapists using the Android app **Mood Patterns** (`info.moodpatterns.moodpatterns`).

In addition to rendering the PDFs, the tool must track which promo codes from a master Google Play CSV have already been assigned to which therapist so batches (e.g., 20 codes per therapist) can be sliced automatically without manual spreadsheet editing or accidental duplicate distribution.

## 2. Environment & Tooling Constraints (`uv`)
- Use **`uv`** exclusively for Python version management, virtual environments, dependency locking, and script execution.
- Pin Python to `3.12` (`uv python pin 3.12`).
- Initialize the project as an installable package with a CLI entrypoint (`mp-handouts`) in `pyproject.toml`.
- Use **pure-Python libraries** for PDF and QR generation (`reportlab`, `qrcode[pil]`, `pillow`, `typer`, `rich`) to avoid OS-level Cairo/Pango C-library dependencies on macOS.
- Include `pytest` and `pypdf` as dev dependencies (`uv add --dev pytest pypdf`) so the agent can verify PDF generation and page counts autonomously.

## 3. Core Architecture & Directory Structure
```text
mp-handouts/
├── .python-version
├── pyproject.toml
├── README.md
├── assets/
│   └── mp_icon.png               # Optional logo asset (graceful fallback if missing)
├── data/
│   ├── ledger.db                 # SQLite database tracking imported & assigned promo codes
│   └── sample_codes.csv          # Dummy Google Play promo codes for testing
├── output/                       # Generated therapist PDF packets
├── src/
│   └── mp_handouts/
│       ├── __init__.py
│       ├── cli.py                # Typer CLI commands (import, generate, status, demo)
│       ├── ledger.py             # SQLite code pool management & batch allocation
│       ├── i18n.py               # Copy strings for EN (default) and DE
│       ├── qr.py                 # High-resolution QR code image generator
│       └── pdf_renderer.py       # ReportLab A4 single-page worksheet layout engine
└── tests/
    ├── test_ledger.py
    └── test_pdf_renderer.py
```

## 4. Functional Requirements

### A. Promo Code Pool & Ledger (`ledger.py`)
1. **CSV Import (`mp-handouts import-csv <path> --campaign <name> --expiry <YYYY-MM-DD>`):**
   - Google Play Console exports one-time promo codes as a CSV (typically one code per line, with or without a header row).
   - Strip whitespace, ignore empty lines or header labels (e.g., `"Promotion code"`, `"Code"`), and insert unique codes into a local SQLite table `promo_codes`:
     - `code` (TEXT PRIMARY KEY)
     - `campaign` (TEXT)
     - `expiry_date` (TEXT)
     - `assigned_to` (TEXT, NULLABLE) — Therapist or practice name
     - `assigned_at` (TEXT, NULLABLE) — ISO-8601 timestamp
     - `batch_id` (TEXT, NULLABLE)
2. **Atomic Batch Allocation:**
   - When generating a packet for a therapist (e.g., `--therapist "Dr. Jane Smith" --count 20`), atomically select `count` unassigned codes (`WHERE assigned_to IS NULL`), mark them with `assigned_to`, `assigned_at`, and a `batch_id`, and pass them to the PDF renderer.
   - If fewer than `count` unassigned codes remain in the pool, raise a clear CLI error before modifying the database.
3. **Inventory Status (`mp-handouts status`):**
   - Print a `rich` summary table showing total codes, remaining unassigned codes per campaign/expiry, and a log of recent therapist batches.

### B. Deep Links & QR Codes (`qr.py`)
Generate crisp, print-grade QR codes (`ERROR_CORRECT_M`, border=2):
1. **Voucher Redemption QR (Dynamic per page):**
   - Target URL: `https://play.google.com/redeem?code={CODE}`
2. **App Store Install QR (Static):**
   - Target URL: `https://play.google.com/store/apps/details?id=info.moodpatterns.moodpatterns`
3. **Help Videos QR (Static, small footer):**
   - Target URL: `https://www.youtube.com/@moodpatternsapp7631`

### C. A4 Printable Client Handout Layout (`pdf_renderer.py`)
Each promo code in the batch produces **exact 1 A4 page (210mm × 297mm)** inside a single multi-page PDF file named `output/MoodPatterns_Vouchers_{sanitized_therapist}_{YYYY-MM-DD}.pdf`.
Use clean typography (Helvetica / Helvetica-Bold / Courier-Bold for the backup code), subtle rounded boxes, and clinical worksheet styling so it prints cleanly in both color and black-and-white laser printers:

1. **Header Banner:**
   - Title: **Mood Patterns — Between-Session Therapy Companion**
   - Subtitle: *Ecological Momentary Assessment (EMA) & Mood Tracking with 100% Local Privacy*
   - Optional practice badge on the right if `--therapist` is provided (e.g., *"Provided by: [Therapist Name]"*).

2. **Section 1: Your Therapeutic Privacy Guarantee (Highlighted Box):**
   - Bullet 1: **100% Offline & Strictly Yours:** *Mood Patterns requests zero internet permission. Neither your therapist nor the app developer can access your entries remotely. All data is 256-bit AES encrypted locally on your smartphone—you decide what to share in session.*
   - Bullet 2: **App Lock Protection:** *Enable the built-in PIN/biometric App Lock in the settings menu so your entries remain private on your phone.*

3. **Section 2: Agreed Focus for Your Next Sessions (Therapist Fill-In Worksheet Box):**
   - Draw clean form lines and checkboxes (`[  ]`) meant to be filled in by hand with a pen during the session:
   - **Recommended daily check-in prompts:** `[  ] 2x/day    [  ] 3x/day    [  ] 4x/day    [  ] Custom: ________`
   - **Key scales / symptoms to observe:** `____________________________________________________________`
   - **Contexts, periods, or volatility alerts:** `____________________________________________________________`

4. **Section 3: Getting Started in 3 Steps + Android EMA Checklist:**
   - **Step 1 — Install the App:** Scan the *Google Play App QR* (or search for **Mood Patterns** on Google Play).
   - **Step 2 — Android EMA Reliability Check:**
     - `[  ]` **Allow Notifications** when prompted so daily check-in reminders arrive on time.
     - `[  ]` **Disable Battery Optimization** for *Mood Patterns* in Android Settings if notifications are delayed.
   - **Step 3 — Redeem Your 90-Day Free Pro Voucher:** Scan your personal *Voucher QR Code* below (or open *Mood Patterns* → *Pro* → *Payment methods* → *Redeem code*).
   - *Transparency Note:* *Your first 90 days of Mood Patterns Pro are 100% free (€0.00). Google Play requires a payment method on file to start the 90-day free trial. You can cancel auto-renewal anytime with two taps in Google Play under "Subscriptions" without losing your remaining free 90 days.*

5. **Section 4: Personal 90-Day Pro Voucher Card (Bottom Cut-Off / Box):**
   - Left column: **App Store QR** (smaller) + **Help Videos QR** (`youtube.com/@moodpatternsapp7631` & `moodpatterns.info/moodpatterns/therapy.html`).
   - Right column (prominent bordered box):
     - Large **Personal Voucher QR Code** (`https://play.google.com/redeem?code={CODE}`)
     - **One-Time Backup Code (Monospace):** `{CODE}`
     - **Please redeem by:** `{EXPIRY_DATE}`
     - Page/Voucher counter in small muted text at bottom corner: `Voucher {i} of {N}`

### D. Localization Support (`i18n.py`)
- Store all heading and body strings in a clean dictionary in `i18n.py` supporting `--lang en` (default) and `--lang de` so handouts can be generated in either English or German via a CLI flag.

### E. CLI Interface (`cli.py`)
Provide the following commands via `uv run mp-handouts`:
- `uv run mp-handouts demo` — Generates a 3-page sample PDF in English and German (`output/demo_en.pdf`, `output/demo_de.pdf`) using dummy codes without touching the production SQLite ledger.
- `uv run mp-handouts import-csv <csv_path> --campaign <str> --expiry <YYYY-MM-DD>` — Imports codes into `data/ledger.db`.
- `uv run mp-handouts generate --therapist <str> --count <int> [--lang en|de] [--campaign <str>]` — Allocates `<count>` unused codes and renders the multi-page PDF.
- `uv run mp-handouts status` — Displays remaining unassigned codes and past allocations.

## 5. Verification & Definition of Done
After implementing the project:
1. Run `uv run pytest` and verify that all unit tests pass:
   - CSV import deduplication & header ignoring.
   - Atomic allocation preventing double-assignment of codes.
   - PDF rendering producing an exact `N`-page valid PDF verified via `pypdf.PdfReader`.
2. Run `uv run mp-handouts demo` and confirm both `output/demo_en.pdf` and `output/demo_de.pdf` render cleanly with zero text overlaps and fit strictly onto 1 A4 page per voucher.