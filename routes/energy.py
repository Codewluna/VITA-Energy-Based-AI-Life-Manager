"""
routes/energy.py
POST /api/energy          - log current energy level + get AI insight
GET  /api/energy/history  - last 7 energy logs for the user
"""

from flask import Blueprint, request, jsonify
from models.schemas import energy_log_schema
from services.auth_utils import token_required
from services.vita_brain import get_energy_insight

energy_bp = Blueprint("energy", __name__, url_prefix="/api/energy")

VALID_LEVELS = {"high", "medium", "low", "depleted"}


def get_db():
    from app import mongo
    return mongo.db


# ── POST log energy ───────────────────────────────────────────────────────────

@energy_bp.route("", methods=["POST"])
@token_required
def log_energy():
    data  = request.get_json(silent=True) or {}
    level = (data.get("level") or "").strip().lower()

    if level not in VALID_LEVELS:
        return jsonify({"error": f"level must be one of: {', '.join(VALID_LEVELS)}"}), 400

    db  = get_db()
    doc = energy_log_schema(request.user_id, level)
    db.energy_logs.insert_one(doc)

    insight = get_energy_insight(level)

    return jsonify({
        "message": "Energy level logged",
        "level":   level,
        "insight": insight,
    }), 201


# ── GET energy history ────────────────────────────────────────────────────────

@energy_bp.route("/history", methods=["GET"])
@token_required
def energy_history():
    db   = get_db()
    logs = list(
        db.energy_logs
        .find({"user_id": request.user_id})
        .sort("logged_at", -1)
        .limit(14)
    )
    return jsonify([
        {
            "level":     l["level"],
            "logged_at": l["logged_at"].isoformat(),
        }
        for l in logs
    ]), 200
