"""
database.py – SQLite persistence layer.
Stores listings, prevents duplicates via SHA-256 hash.
"""

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "rental_hunter.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS listings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                hash        TEXT    UNIQUE NOT NULL,
                url         TEXT    NOT NULL,
                title       TEXT,
                price       REAL,
                surface     REAL,
                city        TEXT,
                postal_code TEXT,
                furnished   INTEGER DEFAULT 0,
                source      TEXT,
                agency      TEXT,
                description TEXT,
                image_count INTEGER DEFAULT 0,
                geo_score   INTEGER DEFAULT 0,
                transport_score INTEGER DEFAULT 0,
                total_score REAL    DEFAULT 0,
                risk_level  TEXT    DEFAULT 'SAFE',
                detected_at TEXT    NOT NULL
            )
            """
        )
        conn.commit()


def _make_hash(url: str, title: str, price: Optional[float]) -> str:
    raw = f"{url}|{title}|{price}"
    return hashlib.sha256(raw.encode()).hexdigest()


def listing_exists(url: str, title: str, price: Optional[float]) -> bool:
    h = _make_hash(url, title, price)
    with _connect() as conn:
        row = conn.execute("SELECT id FROM listings WHERE hash=?", (h,)).fetchone()
    return row is not None


def save_listing(listing: dict) -> bool:
    """
    Persist a listing.  Returns True if inserted, False if already present.
    The ``listing`` dict is mutated in-place with the assigned ``id`` on insert.
    """
    h = _make_hash(
        listing.get("url", ""),
        listing.get("title", ""),
        listing.get("price"),
    )
    if listing_exists(listing.get("url", ""), listing.get("title", ""), listing.get("price")):
        return False

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO listings
                (hash, url, title, price, surface, city, postal_code,
                 furnished, source, agency, description, image_count,
                 geo_score, transport_score, total_score, risk_level, detected_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                h,
                listing.get("url", ""),
                listing.get("title", ""),
                listing.get("price"),
                listing.get("surface"),
                listing.get("city", ""),
                listing.get("postal_code", ""),
                int(listing.get("furnished", False)),
                listing.get("source", ""),
                listing.get("agency", ""),
                listing.get("description", ""),
                listing.get("image_count", 0),
                listing.get("geo_score", 0),
                listing.get("transport_score", 0),
                listing.get("total_score", 0),
                listing.get("risk_level", "SAFE"),
                listing.get("detected_at", datetime.now(timezone.utc).isoformat()),
            ),
        )
        conn.commit()
        listing["id"] = cursor.lastrowid
    return True


def get_unsent_listings(limit: int = 100) -> list[dict]:
    """Return all listings not yet included in an email digest."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM listings
            WHERE id NOT IN (SELECT listing_id FROM sent_listings)
            ORDER BY total_score DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def init_sent_table() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_listings (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                sent_at    TEXT    NOT NULL
            )
            """
        )
        conn.commit()


def mark_sent(listing_ids: list[int]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.executemany(
            "INSERT INTO sent_listings (listing_id, sent_at) VALUES (?,?)",
            [(lid, now) for lid in listing_ids],
        )
        conn.commit()
