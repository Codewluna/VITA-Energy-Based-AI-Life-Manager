"""
models/schemas.py
MongoDB document schemas and helper validators for VITA.
"""

from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


# ── User schema ───────────────────────────────────────────────────────────────

def user_schema(name: str, email: str, password_hash: str) -> dict:
    return {
        "name":           name,
        "email":          email.lower().strip(),
        "password_hash":  password_hash,
        "created_at":     utcnow(),
        "updated_at":     utcnow(),
    }


# ── Task schema ───────────────────────────────────────────────────────────────

def task_schema(user_id, name: str, energy: str, category: str, notes: str = "") -> dict:
    valid_energies = {"high", "medium", "low", "depleted"}
    if energy not in valid_energies:
        energy = "medium"
    return {
        "user_id":    str(user_id),
        "name":       name.strip(),
        "energy":     energy,
        "category":   category.strip() or "Work",
        "notes":      notes.strip(),
        "done":       False,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }


# ── Energy log schema ─────────────────────────────────────────────────────────

def energy_log_schema(user_id, level: str) -> dict:
    return {
        "user_id":    str(user_id),
        "level":      level,
        "logged_at":  utcnow(),
    }


# ── Wellbeing log schema ──────────────────────────────────────────────────────

def wellbeing_schema(user_id) -> dict:
    """One document per user per day. Upserted on each update."""
    today = datetime.now(timezone.utc).date().isoformat()
    return {
        "user_id":    str(user_id),
        "date":       today,
        "water":      0,
        "move_min":   0,
        "rest_min":   0,
        "last_meal":  None,
        "updated_at": utcnow(),
    }


# ── Chat message schema ───────────────────────────────────────────────────────

def chat_message_schema(user_id, role: str, content: str) -> dict:
    return {
        "user_id":    str(user_id),
        "role":       role,        # "user" or "assistant"
        "content":    content,
        "timestamp":  utcnow(),
    }
