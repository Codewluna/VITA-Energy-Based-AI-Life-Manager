"""
routes/auth.py
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
"""

import bcrypt
from flask import Blueprint, request, jsonify
from bson import ObjectId
from models.schemas import user_schema
from services.auth_utils import create_token, token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def get_db():
    from app import mongo
    return mongo.db


# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_db()
    if db.users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    doc     = user_schema(name, email, pw_hash)
    result  = db.users.insert_one(doc)
    token   = create_token(str(result.inserted_id))

    return jsonify({
        "message": "Account created successfully",
        "token":   token,
        "user": {
            "id":    str(result.inserted_id),
            "name":  name,
            "email": email,
        }
    }), 201


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    db   = get_db()
    user = db.users.find_one({"email": email})

    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(str(user["_id"]))

    return jsonify({
        "message": "Login successful",
        "token":   token,
        "user": {
            "id":    str(user["_id"]),
            "name":  user["name"],
            "email": user["email"],
        }
    }), 200


# ── Profile ───────────────────────────────────────────────────────────────────

@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    db   = get_db()
    user = db.users.find_one({"_id": ObjectId(request.user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id":         str(user["_id"]),
        "name":       user["name"],
        "email":      user["email"],
        "created_at": user["created_at"].isoformat(),
    }), 200
