"""
email_sender.py – HTML email digest, grouped by category.

Categories:
  1. ⭐  High Priority     (best overall score)
  2. 🏢  Agency – Unfurnished
  3. 🏢  Agency – Furnished
  4. 👤  Private – Unfurnished
  5. 👤  Private – Furnished
  6. ⚠️  Risk Listings
  7. 🌍  Good deals outside priority zone
"""

import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from rental_hunter.config import (
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_PRIMARY,
    EMAIL_SECONDARY,
    SMTP_HOST,
    SMTP_PORT,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Grouping logic
# ---------------------------------------------------------------------------

def _categorise(listings: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {
        "⭐ High Priority": [],
        "🏢 Agency – Unfurnished": [],
        "🏢 Agency – Furnished": [],
        "👤 Private – Unfurnished": [],
        "👤 Private – Furnished": [],
        "⚠️ Risk Listings": [],
        "🌍 Good deals outside priority zone": [],
    }

    for lst in listings:
        risk = lst.get("risk_level", "SAFE")
        geo = lst.get("geo_score", 0)
        total = lst.get("total_score", 0)
        furnished = bool(lst.get("furnished", 0))
        is_agency = bool(lst.get("agency", ""))

        if risk in ("HIGH RISK", "WARNING"):
            groups["⚠️ Risk Listings"].append(lst)
            continue

        # Top-scoring regardless of zone
        if total >= 7:
            groups["⭐ High Priority"].append(lst)
            continue

        if geo == 0:
            groups["🌍 Good deals outside priority zone"].append(lst)
            continue

        if is_agency:
            if furnished:
                groups["🏢 Agency – Furnished"].append(lst)
            else:
                groups["🏢 Agency – Unfurnished"].append(lst)
        else:
            if furnished:
                groups["👤 Private – Furnished"].append(lst)
            else:
                groups["👤 Private – Unfurnished"].append(lst)

    return groups


# ---------------------------------------------------------------------------
# HTML building
# ---------------------------------------------------------------------------

_CARD_STYLE = (
    "border:1px solid #ddd;border-radius:8px;padding:12px 16px;"
    "margin-bottom:12px;background:#fff;"
)
_HEADER_STYLE = (
    "background:#1a1a2e;color:#fff;padding:20px 24px;"
    "border-radius:8px 8px 0 0;margin-bottom:16px;"
)
_SECTION_STYLE = "margin-bottom:28px;"
_RISK_COLORS = {"SAFE": "#27ae60", "WARNING": "#f39c12", "HIGH RISK": "#e74c3c"}


def _render_listing_card(lst: dict) -> str:
    risk = lst.get("risk_level", "SAFE")
    risk_color = _RISK_COLORS.get(risk, "#27ae60")
    furnished_label = "Meublé" if lst.get("furnished") else "Non meublé"
    price = f"{lst['price']:.0f} €/mois" if lst.get("price") else "N/A"
    surface = f"{lst['surface']:.0f} m²" if lst.get("surface") else "N/A"
    detected = lst.get("detected_at", "")[:16].replace("T", " ")
    source = lst.get("source", "")
    transport = lst.get("transport_score", 0)
    geo = lst.get("geo_score", 0)
    total = lst.get("total_score", 0)
    agency_line = f"<small>🏢 {lst['agency']}</small><br>" if lst.get("agency") else ""

    return f"""
<div style="{_CARD_STYLE}">
  <a href="{lst.get('url','#')}" style="color:#2980b9;font-size:15px;font-weight:bold;
     text-decoration:none;">{lst.get('title','—')}</a><br>
  {agency_line}
  <span style="font-size:13px;color:#555;">
    💶 <strong>{price}</strong> &nbsp;|&nbsp;
    📐 {surface} &nbsp;|&nbsp;
    📍 {lst.get('city','?')} &nbsp;|&nbsp;
    🛋 {furnished_label}
  </span><br>
  <span style="font-size:12px;color:#777;">
    🗺 Geo: <strong>{geo}</strong> &nbsp;
    🚇 Transport: <strong>{transport}</strong> &nbsp;
    ⭐ Total: <strong>{total:.1f}</strong> &nbsp;
    <span style="color:{risk_color};">⚠ {risk}</span> &nbsp;
    🔗 {source} &nbsp;|&nbsp; 🕐 {detected}
  </span>
</div>
"""


def _build_html(groups: dict[str, list[dict]], cycle_time: str) -> str:
    sections = ""
    for label, items in groups.items():
        if not items:
            continue
        cards = "".join(_render_listing_card(i) for i in items)
        sections += f"""
<div style="{_SECTION_STYLE}">
  <h2 style="border-bottom:2px solid #eee;padding-bottom:6px;">{label} ({len(items)})</h2>
  {cards}
</div>
"""

    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8">
<style>
  body{{font-family:Arial,sans-serif;background:#f5f5f5;color:#333;}}
  .container{{max-width:720px;margin:0 auto;padding:16px;}}
</style>
</head>
<body>
<div class="container">
  <div style="{_HEADER_STYLE}">
    <h1 style="margin:0;font-size:22px;">🏠 Rental Hunter – Digest</h1>
    <p style="margin:4px 0 0;font-size:13px;opacity:.8;">{cycle_time}</p>
  </div>
  {sections}
  <p style="font-size:11px;color:#aaa;text-align:center;margin-top:24px;">
    Généré automatiquement par Rental Hunter · <a href="mailto:{EMAIL_SENDER}">Contact</a>
  </p>
</div>
</body></html>"""


# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------

def send_digest(listings: list[dict]) -> None:
    """Build and send the HTML digest email to configured recipients."""
    if not listings:
        logger.info("No new listings to send.")
        return

    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        logger.warning("Email credentials not configured – skipping send.")
        return

    cycle_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    groups = _categorise(listings)
    html = _build_html(groups, cycle_time)

    total = len(listings)
    subject = f"🏠 Rental Hunter – {total} nouvelle(s) annonce(s) [{cycle_time}]"

    recipients = [r for r in [EMAIL_PRIMARY, EMAIL_SECONDARY] if r]
    if not recipients:
        logger.warning("No email recipients configured.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipients, msg.as_string())
        logger.info("Digest sent to %s (%d listings).", recipients, total)
    except Exception as exc:
        logger.error("Failed to send email: %s", exc)
