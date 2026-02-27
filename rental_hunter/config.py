"""
config.py – Centralised configuration loaded from environment variables.
All sensitive values are read from .env (never hardcoded).
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
EMAIL_PRIMARY: str = os.getenv("EMAIL_PRIMARY", "")
EMAIL_SECONDARY: str = os.getenv("EMAIL_SECONDARY", "")
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))

# ---------------------------------------------------------------------------
# Optional API keys
# ---------------------------------------------------------------------------
GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------------
# Commute destinations
# ---------------------------------------------------------------------------
COMMUTE_DESTINATIONS: list[str] = [
    os.getenv("COMMUTE_DESTINATION_1", "1 Rue de la Réunion, 75020 Paris"),
    os.getenv("COMMUTE_DESTINATION_2", "Créteil, 94000"),
]

# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------
EMAIL_INTERVAL_HOURS: int = int(os.getenv("EMAIL_INTERVAL_HOURS", "3"))

# ---------------------------------------------------------------------------
# Property filters
# ---------------------------------------------------------------------------
MIN_SURFACE_M2: int = 30
MAX_PRICE_EUR: int = 1200
PROPERTY_TYPE: str = "apartment"

# ---------------------------------------------------------------------------
# Smart mode
# ---------------------------------------------------------------------------
SMART_MODE_MIN_LISTINGS: int = 5     # expand radius if below this
SMART_MODE_MAX_LISTINGS: int = 20    # cap email to best N

# ---------------------------------------------------------------------------
# Geographic zones (postal code prefixes → base score)
# ---------------------------------------------------------------------------
GEO_SCORES: dict[str, int] = {
    "94": 4,  # Val-de-Marne – primary
    "75": 3,  # Paris
    "93": 2,  # Seine-Saint-Denis near 94
}

# 93 cities that border 94 (for secondary bonus)
CITIES_93_NEAR_94: set[str] = {
    "saint-maur-des-fossés", "saint-maur", "noisy-le-grand",
    "fontenay-sous-bois", "vincennes", "montreuil", "bagnolet",
    "charenton-le-pont", "maisons-alfort", "alfortville",
    "ivry-sur-seine", "vitry-sur-seine",
}

# ---------------------------------------------------------------------------
# Scam detection thresholds
# ---------------------------------------------------------------------------
PRICE_PER_M2_ANOMALY_THRESHOLD: float = 7.0   # €/m² below this = suspicious
SCAM_KEYWORDS: list[str] = [
    "western union", "moneygram", "mandat cash", "virement beforehand",
    "envoyez un chèque", "send money", "je suis à l'étranger",
    "propriétaire absent", "clés par courrier", "deposit first",
]
