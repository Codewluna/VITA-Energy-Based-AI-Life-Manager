"""
services/auth_utils.py
JWT creation, decoding, and request decoration for VITA.
"""

import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify


SECRET_KEY = os.getenv("SECRET_KEY", "vita-secret")


def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp":     datetime.now(timezone.utc) + timedelta(days=7),
        "iat":     datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator: protect routes that require a valid JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or malformed"}), 401
        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Token invalid or expired"}), 401
        request.user_id = payload["user_id"]
        return f(*args, **kwargs)
    return decorated
