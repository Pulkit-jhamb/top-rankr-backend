"""
admin.py — TopRanker Admin Blueprint

Endpoints (all require admin role):
  GET  /api/admin/users              - list all students with rankings
  GET  /api/admin/submissions        - all problem submissions
  POST /api/admin/contests           - create a new contest
  PUT  /api/admin/contests/<id>      - update a contest
  POST /api/admin/problems           - create a new problem
  PUT  /api/admin/problems/<id>      - update a problem
"""

import math
from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, request, jsonify

from auth import token_required

admin_bp = Blueprint("admin", __name__)


def _admin_required(current_user):
    """Return error response if user is not admin, else None."""
    if current_user.get("role") != "admin":
        return jsonify({"message": "Admin access required"}), 403
    return None


# ─────────────────────────────────────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/users", methods=["GET"])
@token_required
def get_all_users(current_user):
    """List all students with their rankings and submission stats."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500
    err = _admin_required(current_user)
    if err:
        return err

    try:
        page  = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 50))
        skip  = (page - 1) * limit
        search = request.args.get("search", "").strip()

        filters = {"role": "student"}
        if search:
            filters["$or"] = [
                {"name":        {"$regex": search, "$options": "i"}},
                {"email":       {"$regex": search, "$options": "i"}},
                {"institution": {"$regex": search, "$options": "i"}},
                {"country":     {"$regex": search, "$options": "i"}},
            ]

        users = list(db.students.find(
            filters,
            {"password": 0},
        ).skip(skip).limit(limit).sort("created_at", -1))

        total = db.students.count_documents(filters)

        result = []
        for u in users:
            uid = str(u["_id"])
            sub_count = db.submissions.count_documents({"userId": uid})
            problem_rankings = u.get("problem_rankings", {})
            result.append({
                "_id":           uid,
                "name":          u.get("name", ""),
                "email":         u.get("email", ""),
                "country":       u.get("country", ""),
                "institution":   u.get("institution", ""),
                "createdAt":     u.get("created_at", ""),
                "totalSubmissions": sub_count,
                "problemsAttempted": len(problem_rankings),
                "globalRank":    u.get("global_rank"),
            })

        return jsonify({
            "success": True,
            "data": result,
            "pagination": {
                "page": page, "limit": limit,
                "total": total,
                "pages": math.ceil(total / limit) if total else 0,
            },
        }), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@admin_bp.route("/users/<user_id>", methods=["GET"])
@token_required
def get_user_detail(current_user, user_id):
    """Get full detail for a single user — rankings + submission history."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500
    err = _admin_required(current_user)
    if err:
        return err

    try:
        user = db.students.find_one({"_id": ObjectId(user_id)}, {"password": 0})
        if not user:
            return jsonify({"message": "User not found"}), 404

        user["_id"] = str(user["_id"])

        submissions = list(db.submissions.find(
            {"userId": user_id},
            {"x": 0},
        ).sort("submittedAt", -1).limit(100))
        for s in submissions:
            s["_id"] = str(s["_id"])

        contests_joined = list(db.contests.find(
            {"participants": user_id},
            {"eventCode": 0, "participants": 0},
        ))
        for c in contests_joined:
            c["_id"] = str(c["_id"])

        return jsonify({
            "success": True,
            "data": {
                "user":        user,
                "submissions": submissions,
                "contests":    contests_joined,
            },
        }), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# SUBMISSIONS
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/submissions", methods=["GET"])
@token_required
def get_all_submissions(current_user):
    """Return paginated submission history across all users."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500
    err = _admin_required(current_user)
    if err:
        return err

    try:
        page      = int(request.args.get("page", 1))
        limit     = int(request.args.get("limit", 50))
        skip      = (page - 1) * limit
        problem   = request.args.get("problem", "").strip()
        user_name = request.args.get("user", "").strip()

        filters = {}
        if problem:
            filters["problemId"] = {"$regex": problem, "$options": "i"}
        if user_name:
            filters["userName"] = {"$regex": user_name, "$options": "i"}

        subs = list(db.submissions.find(filters, {"x": 0})
                    .sort("submittedAt", -1).skip(skip).limit(limit))
        total = db.submissions.count_documents(filters)

        for s in subs:
            s["_id"] = str(s["_id"])
            if hasattr(s.get("submittedAt"), "isoformat"):
                s["submittedAt"] = s["submittedAt"].isoformat()

        return jsonify({
            "success": True,
            "data": subs,
            "pagination": {
                "page": page, "limit": limit,
                "total": total,
                "pages": math.ceil(total / limit) if total else 0,
            },
        }), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# CONTESTS  (create / update)
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/contests", methods=["POST"])
@token_required
def create_contest(current_user):
    """Create a new contest."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500
    err = _admin_required(current_user)
    if err:
        return err

    try:
        data = request.get_json() or {}
        required = ["eventId", "name", "organizer"]
        for field in required:
            if not data.get(field):
                return jsonify({"message": f"'{field}' is required"}), 400

        if db.contests.find_one({"eventId": data["eventId"]}):
            return jsonify({"message": f"Contest '{data['eventId']}' already exists"}), 409

        contest = {
            "eventId":      data["eventId"].strip(),
            "name":         data["name"].strip(),
            "organizer":    data["organizer"].strip(),
            "type":         data.get("type", "Open"),
            "status":       data.get("status", "upcoming"),
            "prize":        data.get("prize"),
            "confHomePage": data.get("confHomePage", ""),
            "problems":     data.get("problems", []),
            "participants": [],
            "eventCode":    data.get("eventCode", ""),
            "created_at":   datetime.now(timezone.utc),
        }
        if data.get("startDate"):
            try:
                contest["startDate"] = datetime.fromisoformat(data["startDate"])
            except ValueError:
                pass
        if data.get("endDate"):
            try:
                contest["endDate"] = datetime.fromisoformat(data["endDate"])
            except ValueError:
                pass

        result = db.contests.insert_one(contest)
        return jsonify({
            "success": True,
            "message": f"Contest '{data['name']}' created",
            "id": str(result.inserted_id),
        }), 201
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@admin_bp.route("/contests/<contest_id>", methods=["PUT"])
@token_required
def update_contest(current_user, contest_id):
    """Update an existing contest."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500
    err = _admin_required(current_user)
    if err:
        return err

    try:
        data = request.get_json() or {}
        allowed = {"name", "organizer", "type", "status", "prize",
                   "confHomePage", "problems", "startDate", "endDate", "eventCode"}
        update = {k: v for k, v in data.items() if k in allowed}
        if not update:
            return jsonify({"message": "No valid fields to update"}), 400

        for date_field in ("startDate", "endDate"):
            if date_field in update and isinstance(update[date_field], str):
                try:
                    update[date_field] = datetime.fromisoformat(update[date_field])
                except ValueError:
                    pass

        res = db.contests.update_one({"eventId": contest_id}, {"$set": update})
        if res.matched_count == 0:
            return jsonify({"message": "Contest not found"}), 404

        return jsonify({"success": True, "message": "Contest updated"}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# PROBLEMS  (create / update)
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/problems", methods=["POST"])
@token_required
def create_problem(current_user):
    """Create a new problem."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500
    err = _admin_required(current_user)
    if err:
        return err

    try:
        data = request.get_json() or {}
        required = ["problemId", "name"]
        for field in required:
            if not data.get(field):
                return jsonify({"message": f"'{field}' is required"}), 400

        if db.problems.find_one({"problemId": data["problemId"]}):
            return jsonify({"message": f"Problem '{data['problemId']}' already exists"}), 409

        problem = {
            "problemId":        data["problemId"].strip(),
            "name":             data["name"].strip(),
            "level":            data.get("level", "Medium"),
            "type":             data.get("type", "Minimization"),
            "category":         data.get("category", ""),
            "tags":             data.get("tags", []),
            "description":      data.get("description", ""),
            "status":           data.get("status", "active"),
            "totalSubmissions": 0,
            "owner":            current_user.get("user_id", ""),
            "ownerName":        current_user.get("name", ""),
            "created_at":       datetime.now(timezone.utc),
            "dimensions":       [
                {"dimension": d, "submissions": 0}
                for d in data.get("dimensions", [10, 20, 30])
            ],
            "fitnessFunction": {
                "formula":     data.get("formula", ""),
                "constraint":  data.get("constraint", ""),
                "bounds": {
                    "min": data.get("boundsMin", -10),
                    "max": data.get("boundsMax",  10),
                },
                "globalMinimum": data.get("globalMinimum", 0),
            },
        }

        result = db.problems.insert_one(problem)
        return jsonify({
            "success": True,
            "message": f"Problem '{data['name']}' created",
            "id": str(result.inserted_id),
        }), 201
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


@admin_bp.route("/problems/<problem_id>", methods=["PUT"])
@token_required
def update_problem(current_user, problem_id):
    """Update an existing problem."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500
    err = _admin_required(current_user)
    if err:
        return err

    try:
        data = request.get_json() or {}
        allowed = {"name", "level", "type", "category", "tags",
                   "description", "status", "fitnessFunction", "dimensions"}
        update = {k: v for k, v in data.items() if k in allowed}
        if not update:
            return jsonify({"message": "No valid fields to update"}), 400

        res = db.problems.update_one({"problemId": problem_id}, {"$set": update})
        if res.matched_count == 0:
            return jsonify({"message": "Problem not found"}), 404

        return jsonify({"success": True, "message": "Problem updated"}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD STATS
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/stats", methods=["GET"])
@token_required
def get_admin_stats(current_user):
    """Quick overview counts for the admin dashboard."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500
    err = _admin_required(current_user)
    if err:
        return err

    try:
        return jsonify({
            "success": True,
            "data": {
                "totalUsers":       db.students.count_documents({"role": "student"}),
                "totalProblems":    db.problems.count_documents({}),
                "totalContests":    db.contests.count_documents({}),
                "totalSubmissions": db.submissions.count_documents({}),
                "activeContests":   db.contests.count_documents({"status": {"$in": ["active", "ongoing"]}}),
            },
        }), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500
