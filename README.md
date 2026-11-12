# Mood Patterns Therapist Voucher & Handout Generator (`mp-handouts`)

A CLI tool and Python framework that ingests Google Play Console one-time promo code CSV exports and generates print-ready, multi-page A4 PDF packets (1 page per client voucher) for psychotherapists using the Android app **Mood Patterns** (`info.moodpatterns.moodpatterns`).

## Quick Start (`uv`)

```bash
# Run demo (generates output/demo_en.pdf and output/demo_de.pdf)
uv run mp-handouts demo

# Import Google Play promo codes CSV
uv run mp-handouts import-csv data/sample_codes.csv --campaign "Q4-2026" --expiry "2027-03-31"

# Check code pool inventory and batch allocations
uv run mp-handouts status

# Generate a therapist handout packet
uv run mp-handouts generate --therapist "Dr. Jane Smith" --count 5 --lang en

# Run unit tests
uv run pytest
```

