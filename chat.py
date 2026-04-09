"""
routes/chat.py
POST /api/chat          - send a message, get VITA's response
GET  /api/chat/history  - get last 20 messages for the user
DELETE /api/chat        - clear chat history
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from models.schemas import chat_message_schema
from services.auth_utils import token_required
from services.vita_brain import generate_response

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


def get_db():
    from app import mongo
    return mongo.db


def today_str():
    return datetime.now(timezone.utc).date().isoformat()


def build_context(db, user_id: str) -> dict:
    """Assemble full user context to pass to the VITA brain."""

    # Latest energy level
    latest_energy = db.energy_logs.find_one(
        {"user_id": user_id},
        sort=[("logged_at", -1)]
    )
    energy = latest_energy["level"] if latest_energy else None

    # Pending tasks
    tasks = list(db.tasks.find(
        {"user_id": user_id},
        {"name": 1, "energy": 1, "done": 1, "category": 1, "_id": 0}
    ))

    # Today wellbeing
    today = today_str()
    wb    = db.wellbeing.find_one({"user_id": user_id, "date": today}) or {}

    return {
        "energy":   energy,
        "tasks":    tasks,
        "water":    wb.get("water", 0),
        "move_min": wb.get("move_min", 0),
        "rest_min": wb.get("rest_min", 0),
        "last_meal": wb.get("last_meal"),
    }


# ── POST send message ─────────────────────────────────────────────────────────

@chat_bp.route("", methods=["POST"])
@token_required
def send_message():
    data    = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "message field is required"}), 400

    if len(message) > 1000:
        return jsonify({"error": "Message too long (max 1000 characters)"}), 400

    db      = get_db()
    context = build_context(db, request.user_id)

    # Save user message
    user_doc = chat_message_schema(request.user_id, "user", message)
    db.chat_messages.insert_one(user_doc)

    # Generate response from VITA brain
    response_text = generate_response(message, context)

    # Save assistant message
    assistant_doc = chat_message_schema(request.user_id, "assistant", response_text)
    db.chat_messages.insert_one(assistant_doc)

    return jsonify({
        "message":  message,
        "response": response_text,
        "context":  {
            "energy": context["energy"],
            "pending_tasks": sum(1 for t in context["tasks"] if not t.get("done")),
        }
    }), 200


# ── GET chat history ──────────────────────────────────────────────────────────

@chat_bp.route("/history", methods=["GET"])
@token_required
def get_history():
    db   = get_db()
    msgs = list(
        db.chat_messages
        .find({"user_id": request.user_id})
        .sort("timestamp", -1)
        .limit(30)
    )
    msgs.reverse()
    return jsonify([
        {
            "role":      m["role"],
            "content":   m["content"],
            "timestamp": m["timestamp"].isoformat(),
        }
        for m in msgs
    ]), 200


# ── DELETE clear history ──────────────────────────────────────────────────────

@chat_bp.route("", methods=["DELETE"])
@token_required
def clear_history():
    db = get_db()
    result = db.chat_messages.delete_many({"user_id": request.user_id})
    return jsonify({"message": f"Deleted {result.deleted_count} messages"}), 200
