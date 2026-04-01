import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── App factory ──────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# Fail fast if SECRET_KEY is still the insecure default
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    logger.warning(
        "SECRET_KEY is not set in environment variables. "
        "Using an insecure default — DO NOT use this in production."
    )
    SECRET_KEY = "your-secret-key-change-in-production"

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/topranker")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Force a connection check
    client.admin.command("ping")
    db = client["topranker"]
    logger.info("Connected to MongoDB Atlas successfully.")
except Exception as exc:
    logger.error("MongoDB connection failed: %s", exc)
    db = None

# ── Blueprints ────────────────────────────────────────────────────────────────
try:
    from auth import auth_bp
    from problems import problems_bp
    from contests import contests_bp
    from statistics import statistics_bp
    from leaderboard import leaderboard_bp

    app.register_blueprint(auth_bp,        url_prefix="/api/auth")
    app.register_blueprint(problems_bp,    url_prefix="/api/problems")
    app.register_blueprint(contests_bp,    url_prefix="/api/contests")
    app.register_blueprint(statistics_bp,  url_prefix="/api/statistics")
    app.register_blueprint(leaderboard_bp, url_prefix="/api/leaderboard")
    logger.info("All blueprints registered successfully.")
except Exception as exc:
    logger.error("Blueprint registration failed: %s", exc)
    raise

# ── Global error handlers ─────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(exc):
    return jsonify({"message": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(exc):
    return jsonify({"message": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(exc):
    logger.exception("Unhandled server error")
    return jsonify({"message": "Internal server error"}), 500


# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health_check():
    mongo_status = "connected" if db is not None else "disconnected"
    return jsonify(status="ok", mongodb=mongo_status), 200


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Read debug flag from environment; default OFF for safety
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=3999, debug=debug)