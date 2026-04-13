"""
routes/tasks.py
GET    /api/tasks          - get all tasks for user
POST   /api/tasks          - create a task
PATCH  /api/tasks/<id>     - update task (name, energy, done, etc.)
DELETE /api/tasks/<id>     - delete a task
POST   /api/tasks/<id>/toggle - toggle done status
"""

from flask import Blueprint, request, jsonify
from bson import ObjectId
from bson.errors import InvalidId
from models.schemas import task_schema
from services.auth_utils import token_required

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


def get_db():
    from app import mongo
    return mongo.db


def serialize_task(doc: dict) -> dict:
    return {
        "id":         str(doc["_id"]),
        "user_id":    doc.get("user_id"),
        "name":       doc.get("name"),
        "energy":     doc.get("energy"),
        "category":   doc.get("category"),
        "notes":      doc.get("notes", ""),
        "done":       doc.get("done", False),
        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
        "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
    }


# ── GET all tasks ─────────────────────────────────────────────────────────────

@tasks_bp.route("", methods=["GET"])
@token_required
def get_tasks():
    db    = get_db()
    docs  = list(db.tasks.find({"user_id": request.user_id}).sort("created_at", -1))
    return jsonify([serialize_task(d) for d in docs]), 200


# ── POST create task ──────────────────────────────────────────────────────────

@tasks_bp.route("", methods=["POST"])
@token_required
def create_task():
    data = request.get_json(silent=True) or {}

    name     = (data.get("name") or "").strip()
    energy   = (data.get("energy") or "medium").strip().lower()
    category = (data.get("category") or "Work").strip()
    notes    = (data.get("notes") or "").strip()

    if not name:
        return jsonify({"error": "Task name is required"}), 400

    doc    = task_schema(request.user_id, name, energy, category, notes)
    result = get_db().tasks.insert_one(doc)
    doc["_id"] = result.inserted_id

    return jsonify({"message": "Task created", "task": serialize_task(doc)}), 201


# ── PATCH update task ─────────────────────────────────────────────────────────

@tasks_bp.route("/<task_id>", methods=["PATCH"])
@token_required
def update_task(task_id):
    try:
        oid = ObjectId(task_id)
    except InvalidId:
        return jsonify({"error": "Invalid task ID"}), 400

    db   = get_db()
    task = db.tasks.find_one({"_id": oid, "user_id": request.user_id})
    if not task:
        return jsonify({"error": "Task not found"}), 404

    data    = request.get_json(silent=True) or {}
    allowed = {"name", "energy", "category", "notes", "done"}
    updates = {k: v for k, v in data.items() if k in allowed}

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    from models.schemas import utcnow
    updates["updated_at"] = utcnow()

    db.tasks.update_one({"_id": oid}, {"$set": updates})
    updated = db.tasks.find_one({"_id": oid})
    return jsonify({"message": "Task updated", "task": serialize_task(updated)}), 200


# ── POST toggle done ──────────────────────────────────────────────────────────

@tasks_bp.route("/<task_id>/toggle", methods=["POST"])
@token_required
def toggle_task(task_id):
    try:
        oid = ObjectId(task_id)
    except InvalidId:
        return jsonify({"error": "Invalid task ID"}), 400

    db   = get_db()
    task = db.tasks.find_one({"_id": oid, "user_id": request.user_id})
    if not task:
        return jsonify({"error": "Task not found"}), 404

    from models.schemas import utcnow
    new_done = not task.get("done", False)
    db.tasks.update_one({"_id": oid}, {"$set": {"done": new_done, "updated_at": utcnow()}})
    updated = db.tasks.find_one({"_id": oid})
    return jsonify({"message": "Task toggled", "task": serialize_task(updated)}), 200


# ── DELETE task ───────────────────────────────────────────────────────────────

@tasks_bp.route("/<task_id>", methods=["DELETE"])
@token_required
def delete_task(task_id):
    try:
        oid = ObjectId(task_id)
    except InvalidId:
        return jsonify({"error": "Invalid task ID"}), 400

    db     = get_db()
    result = db.tasks.delete_one({"_id": oid, "user_id": request.user_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task deleted"}), 200
