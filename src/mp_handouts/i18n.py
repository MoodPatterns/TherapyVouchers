"""Localization strings (EN and DE) for Mood Patterns therapist handouts."""

from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "de")

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "header_title": "Mood Patterns — Between-Session Therapy Companion",
        "header_subtitle": (
            "Ecological Momentary Assessment (EMA) & Mood Tracking with 100% Local Privacy"
        ),
        "provided_by": "Provided by: {therapist}",
        "sec1_title": "1. Your Therapeutic Privacy Guarantee",
        "sec1_bullet1": (
            "<b>100% Offline &amp; Strictly Yours:</b> <i>Mood Patterns requests zero internet "
            "permission. Neither your therapist nor the app developer can access your entries "
            "remotely. All data is 256-bit AES encrypted locally on your smartphone—you decide "
            "what to share in session.</i>"
        ),
        "sec1_bullet2": (
            "<b>App Lock Protection:</b> <i>Enable the built-in PIN/biometric App Lock in the "
            "settings menu so your entries remain private on your phone.</i>"
        ),
        "sec2_title": "2. Agreed Focus for Your Next Sessions",
        "sec2_subtitle": "(Therapist fill-in worksheet — complete together during session)",
        "sec2_prompts_label": "Recommended daily check-in prompts:",
        "sec2_opt_2x": "2x/day",
        "sec2_opt_3x": "3x/day",
        "sec2_opt_4x": "4x/day",
        "sec2_opt_custom": "Custom:",
        "sec2_scales_label": "Key scales / symptoms to observe:",
        "sec2_contexts_label": "Contexts, periods, or volatility alerts:",
        "sec3_title": "3. Getting Started in 3 Steps + Android EMA Checklist",
        "sec3_step1": (
            "<b>Step 1 — Install the App:</b> Scan the <i>Google Play App QR</i> below "
            "(or search for <b>Mood Patterns</b> on Google Play)."
        ),
        "sec3_step2_header": "<b>Step 2 — Android EMA Reliability Check:</b>",
        "sec3_step2_check1": (
            "<b>Allow Notifications</b> when prompted so daily check-in reminders arrive on time."
        ),
        "sec3_step2_check2": (
            "<b>Disable Battery Optimization</b> for <i>Mood Patterns</i> in Android Settings "
            "if notifications are delayed."
        ),
        "sec3_step3": (
            "<b>Step 3 — Redeem Your 90-Day Free Pro Voucher:</b> Scan your personal "
            "<i>Voucher QR Code</i> below (or open <i>Mood Patterns</i> &#8594; <i>Pro</i> "
            "&#8594; <i>Payment methods</i> &#8594; <i>Redeem code</i>)."
        ),
        "sec3_transparency": (
            "<b>Transparency Note:</b> <i>Your first 90 days of Mood Patterns Pro are 100% free "
            "(&euro;0.00). Google Play requires a payment method on file to start the 90-day free "
            "trial. You can cancel auto-renewal anytime with two taps in Google Play under "
            "&ldquo;Subscriptions&rdquo; without losing your remaining free 90 days.</i>"
        ),
        "cut_line_label": "Keep or detach your personal voucher below",
        "sec4_left_title": "App & Video Guides",
        "sec4_app_qr_label": "Google Play App QR",
        "sec4_app_qr_sub": "info.moodpatterns.moodpatterns",
        "sec4_help_qr_label": "Help Videos & Therapy Info",
        "sec4_help_qr_sub1": "youtube.com/@moodpatternsapp7631",
        "sec4_help_qr_sub2": "moodpatterns.info/moodpatterns/therapy.html",
        "sec4_right_title": "Personal 90-Day Free Pro Voucher",
        "sec4_right_subtitle": "Scan with your Android camera or QR scanner to redeem on Google Play",
        "sec4_backup_label": "One-Time Backup Code:",
        "sec4_expiry_label": "Please redeem by: {expiry}",
        "sec4_counter": "Voucher {i} of {n}",
    },
    "de": {
        "header_title": "Mood Patterns — Therapiebegleiter zwischen den Sitzungen",
        "header_subtitle": (
            "Ecological Momentary Assessment (EMA) & Stimmungstagebuch mit 100 % lokalem Datenschutz"
        ),
        "provided_by": "Überreicht durch: {therapist}",
        "sec1_title": "1. Ihre therapeutische Datenschutz-Garantie",
        "sec1_bullet1": (
            "<b>100 % Offline &amp; strikt privat:</b> <i>Mood Patterns benötigt keinerlei "
            "Internet-Berechtigung. Weder Ihre Therapeutin / Ihr Therapeut noch die App-Entwickler "
            "können aus der Ferne auf Ihre Einträge zugreifen. Alle Daten werden lokal auf Ihrem "
            "Smartphone mit 256-Bit-AES verschlüsselt – Sie allein entscheiden, was Sie in der "
            "Sitzung teilen.</i>"
        ),
        "sec1_bullet2": (
            "<b>App-Sperre (PIN / Biometrie):</b> <i>Aktivieren Sie die integrierte App-Sperre "
            "in den Einstellungen, damit Ihre Einträge auch auf Ihrem Smartphone geschützt bleiben.</i>"
        ),
        "sec2_title": "2. Vereinbarter Fokus für Ihre nächsten Sitzungen",
        "sec2_subtitle": "(Therapie-Arbeitsblatt — gemeinsam in der Sitzung auszufüllen)",
        "sec2_prompts_label": "Empfohlene tägliche Check-in-Impulse:",
        "sec2_opt_2x": "2x/Tag",
        "sec2_opt_3x": "3x/Tag",
        "sec2_opt_4x": "4x/Tag",
        "sec2_opt_custom": "Individuell:",
        "sec2_scales_label": "Wichtige Skalen / zu beobachtende Symptome:",
        "sec2_contexts_label": "Kontexte, Zeiträume oder Schwankungs-Hinweise:",
        "sec3_title": "3. Start in 3 Schritten + Android-EMA-Checkliste",
        "sec3_step1": (
            "<b>Schritt 1 — App installieren:</b> Scannen Sie unten den <i>Google Play App-QR-Code</i> "
            "(oder suchen Sie bei Google Play nach <b>Mood Patterns</b>)."
        ),
        "sec3_step2_header": "<b>Schritt 2 — Android-EMA-Zuverlässigkeits-Check:</b>",
        "sec3_step2_check1": (
            "<b>Benachrichtigungen erlauben</b>, damit tägliche Check-in-Erinnerungen pünktlich eintreffen."
        ),
        "sec3_step2_check2": (
            "<b>Akku-Optimierung deaktivieren</b> für <i>Mood Patterns</i> in den Android-Einstellungen, "
            "falls Erinnerungen verzögert ankommen."
        ),
        "sec3_step3": (
            "<b>Schritt 3 — 90-Tage-Pro-Gutschein kostenlos einlösen:</b> Scannen Sie unten Ihren "
            "persönlichen <i>Gutschein-QR-Code</i> (oder öffnen Sie <i>Mood Patterns</i> &#8594; "
            "<i>Pro</i> &#8594; <i>Zahlungsmethoden</i> &#8594; <i>Code einlösen</i>)."
        ),
        "sec3_transparency": (
            "<b>Transparenz-Hinweis:</b> <i>Ihre ersten 90 Tage Mood Patterns Pro sind zu 100 % "
            "kostenlos (0,00 &euro;). Google Play erfordert zum Start des 90-tägigen Gratiszeitraums "
            "ein hinterlegtes Zahlungsmittel. Sie können die automatische Verlängerung jederzeit mit "
            "zwei Tipps in Google Play unter &bdquo;Abos&ldquo; kündigen, ohne Ihre verbleibenden "
            "90 Gratistage zu verlieren.</i>"
        ),
        "cut_line_label": "Persönlicher Gutschein-Abschnitt",
        "sec4_left_title": "App & Video-Anleitungen",
        "sec4_app_qr_label": "Google Play App-QR",
        "sec4_app_qr_sub": "info.moodpatterns.moodpatterns",
        "sec4_help_qr_label": "Hilfe-Videos & Therapie-Info",
        "sec4_help_qr_sub1": "youtube.com/@moodpatternsapp7631",
        "sec4_help_qr_sub2": "moodpatterns.info/moodpatterns/therapy.html",
        "sec4_right_title": "Persönlicher 90-Tage-Pro-Gutschein",
        "sec4_right_subtitle": "Mit Kamera oder QR-Scanner scannen, um den Code bei Google Play einzulösen",
        "sec4_backup_label": "Einmal-Ersatzcode (Manuelle Eingabe):",
        "sec4_expiry_label": "Bitte einlösen bis: {expiry}",
        "sec4_counter": "Voucher {i} of {n}",
    },
}


def get_strings(lang: str = "en") -> dict[str, str]:
    """Retrieve localization strings for `lang` ('en' or 'de')."""
    normalized = lang.strip().lower()
    if normalized not in TRANSLATIONS:
        raise ValueError(
            f"Unsupported language '{lang}'. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    return TRANSLATIONS[normalized]

