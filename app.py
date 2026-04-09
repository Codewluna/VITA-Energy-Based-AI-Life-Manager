"""
app.py
VITA Backend - Flask entry point.
Run: python app.py
"""

import os
from flask import Flask, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ── App setup ────────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder="static", template_folder="templates")

app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/vitadb")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "vita-secret")

CORS(app, resources={r"/api/*": {"origins": "*"}})

mongo = PyMongo(app)

# ── Register blueprints ──────────────────────────────────────────────────────

from routes.auth      import auth_bp
from routes.tasks     import tasks_bp
from routes.energy    import energy_bp
from routes.wellbeing import wellbeing_bp
from routes.chat      import chat_bp

app.register_blueprint(auth_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(energy_bp)
app.register_blueprint(wellbeing_bp)
app.register_blueprint(chat_bp)

# ── FRONTEND ROUTE (IMPORTANT) ───────────────────────────────────────────────

@app.route("/")
def home():
    return app.send_static_file("index.html")

# ── Health check ─────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    try:
        mongo.db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return jsonify({
        "status":   "VITA backend online",
        "database": db_status,
        "version":  "1.0.0",
    }), 200

# ── Error handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n  VITA backend starting on http://localhost:{port}")
    print(f"  MongoDB URI: {app.config['MONGO_URI']}\n")
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1", port=port, host="0.0.0.0")