"""
routes/wellbeing.py
GET   /api/wellbeing        - get today's wellbeing data
PATCH /api/wellbeing        - update water / move_min / rest_min / last_meal
GET   /api/wellbeing/tip    - get a random wellness tip from VITA brain
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from models.schemas import wellbeing_schema, utcnow
from services.auth_utils import token_required
from services.vita_brain import get_wellness_tip

wellbeing_bp = Blueprint("wellbeing", __name__, url_prefix="/api/wellbeing")


def get_db():
    from app import mongo
    return mongo.db


def today_str():
    return datetime.now(timezone.utc).date().isoformat()


def get_or_create_today(db, user_id: str) -> dict:
    today = today_str()
    doc   = db.wellbeing.find_one({"user_id": user_id, "date": today})
    if not doc:
        new_doc = wellbeing_schema(user_id)
        result  = db.wellbeing.insert_one(new_doc)
        doc     = db.wellbeing.find_one({"_id": result.inserted_id})
    return doc


def serialize(doc: dict) -> dict:
    return {
        "date":      doc.get("date"),
        "water":     doc.get("water", 0),
        "move_min":  doc.get("move_min", 0),
        "rest_min":  doc.get("rest_min", 0),
        "last_meal": doc["last_meal"].isoformat() if doc.get("last_meal") else None,
    }


# ── GET today ─────────────────────────────────────────────────────────────────

@wellbeing_bp.route("", methods=["GET"])
@token_required
def get_wellbeing():
    db  = get_db()
    doc = get_or_create_today(db, request.user_id)
    return jsonify(serialize(doc)), 200


# ── PATCH update ──────────────────────────────────────────────────────────────

@wellbeing_bp.route("", methods=["PATCH"])
@token_required
def update_wellbeing():
    data = request.get_json(silent=True) or {}
    db   = get_db()
    doc  = get_or_create_today(db, request.user_id)
    today = today_str()

    updates = {}

    if "water" in data:
        val = int(data["water"])
        updates["water"] = max(0, min(20, val))

    if "add_water" in data:
        current = doc.get("water", 0)
        updates["water"] = max(0, min(20, current + int(data["add_water"])))

    if "move_min" in data:
        updates["move_min"] = max(0, int(data["move_min"]))

    if "add_move" in data:
        updates["move_min"] = doc.get("move_min", 0) + max(0, int(data["add_move"]))

    if "rest_min" in data:
        updates["rest_min"] = max(0, int(data["rest_min"]))

    if "add_rest" in data:
        updates["rest_min"] = doc.get("rest_min", 0) + max(0, int(data["add_rest"]))

    if "log_meal" in data and data["log_meal"]:
        updates["last_meal"] = utcnow()

    if not updates:
        return jsonify({"error": "No valid fields provided"}), 400

    updates["updated_at"] = utcnow()
    db.wellbeing.update_one(
        {"user_id": request.user_id, "date": today},
        {"$set": updates}
    )
    updated = db.wellbeing.find_one({"user_id": request.user_id, "date": today})
    return jsonify({"message": "Wellbeing updated", "data": serialize(updated)}), 200


# ── GET wellness tip ──────────────────────────────────────────────────────────

@wellbeing_bp.route("/tip", methods=["GET"])
@token_required
def wellness_tip():
    return jsonify({"tip": get_wellness_tip()}), 200
