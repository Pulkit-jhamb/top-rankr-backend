import os
import re
from datetime import datetime, timezone, timedelta
from functools import wraps

import jwt
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from models import Student, Admin

auth_bp = Blueprint("auth", __name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")

# Minimum password length enforced on registration
_MIN_PASSWORD_LENGTH = 8
# Simple email format check
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_token(user, role: str) -> str:
    """Encode a JWT for *user* (a MongoDB document dict)."""
    return jwt.encode(
        {
            "user_id": str(user["_id"]),
            "email":   user["email"],
            "name":    user.get("name", user["email"]),
            "role":    role,
            # timezone-aware UTC — datetime.utcnow() is deprecated in Python 3.12+
            "exp":     datetime.now(timezone.utc) + timedelta(days=7),
        },
        SECRET_KEY,
        algorithm="HS256",
    )


def _user_payload(user, role: str) -> dict:
    """Serialise a MongoDB user document to a safe response dict."""
    return {
        "id":    str(user["_id"]),
        "name":  user["name"],
        "email": user["email"],
        "role":  role,
    }


def _validate_password(password: str):
    """
    Return an error string if the password fails policy, else None.
    Policy: at least 8 characters, at least one digit.
    """
    if len(password) < _MIN_PASSWORD_LENGTH:
        return f"Password must be at least {_MIN_PASSWORD_LENGTH} characters long."
    if not any(ch.isdigit() for ch in password):
        return "Password must contain at least one digit."
    return None


# ── Decorator ─────────────────────────────────────────────────────────────────

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            return jsonify({"message": "Token is missing"}), 401

        token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else auth_header

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return f(current_user, *args, **kwargs)

    return decorated


# ── Routes ────────────────────────────────────────────────────────────────────

@auth_bp.route("/signup", methods=["POST"])
def signup():
    from app import db

    if db is None:
        return jsonify({"message": "Database connection failed"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()   # normalise to lowercase
    password = data.get("password") or ""
    role     = data.get("role", "student")

    if not all([name, email, password]):
        return jsonify({"message": "Name, email, and password are required"}), 400

    if not _EMAIL_RE.match(email):
        return jsonify({"message": "Invalid email address"}), 400

    if role not in ("student", "admin"):
        return jsonify({"message": "Invalid role. Must be student or admin"}), 400

    pwd_error = _validate_password(password)
    if pwd_error:
        return jsonify({"message": pwd_error}), 400

    existing = (Student if role == "student" else Admin).find_by_email(db, email)
    if existing:
        return jsonify({"message": "User with this email already exists"}), 409

    user_data = {
        "name":     name,
        "email":    email,                          # already lowercase
        "password": generate_password_hash(password),
    }

    if role == "student":
        user_data["institution"] = data.get("institution", "")
        user_data["country"]     = data.get("country", "")
        user = Student.create(db, user_data)
    else:
        user = Admin.create(db, user_data)

    token = _make_token(user, role)

    return jsonify({
        "message": "User created successfully",
        "token":   token,
        "user":    _user_payload(user, role),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    from app import db

    if db is None:
        return jsonify({"message": "Database connection failed"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    email    = (data.get("email") or "").strip().lower()   # normalise to lowercase
    password = data.get("password") or ""
    role     = data.get("role", "student")

    if not all([email, password]):
        return jsonify({"message": "Email and password are required"}), 400

    if role not in ("student", "admin"):
        return jsonify({"message": "Invalid role"}), 400

    user = (Student if role == "student" else Admin).find_by_email(db, email)

    # Use a single generic message to avoid user-enumeration attacks
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid credentials"}), 401

    token = _make_token(user, role)

    # Consistent response shape: always wrap user data under a "user" key
    return jsonify({
        "message": "Login successful",
        "token":   token,
        "user":    _user_payload(user, role),
    }), 200


@auth_bp.route("/verify", methods=["GET"])
@token_required
def verify_token(current_user):
    from app import db

    if db is None:
        return jsonify({"message": "Database connection failed"}), 500

    role    = current_user.get("role")
    user_id = current_user.get("user_id")

    user = (Student if role == "student" else Admin).find_by_id(db, user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "valid": True,
        "user":  _user_payload(user, role),
    }), 200
    