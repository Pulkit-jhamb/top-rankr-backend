"""
contests.py — TopRanker Contests Blueprint

Key rules enforced here:
  • Only authenticated students may join or participate.
  • Contest leaderboard is derived from problem scores (NOT raw f(x)).
  • Joining is open — no event code required.
"""

import math
import os

import jwt
from flask import Blueprint, request, jsonify
from bson import ObjectId

from auth import token_required

_SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")

contests_bp = Blueprint("contests", __name__)

# Contest statuses that allow new registrations
_OPEN_STATUSES = {"upcoming", "active", "ongoing"}


# ─────────────────────────────────────────────────────────────────────────────
# LIST / DETAIL
# ─────────────────────────────────────────────────────────────────────────────

@contests_bp.route("/", methods=["GET"])
def get_contests():
    """Get all contests with pagination and status / type filtering."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500

    try:
        page         = int(request.args.get("page", 1))
        limit        = int(request.args.get("limit", 10))
        contest_type = request.args.get("type", "all")
        status       = request.args.get("status", "all")
        skip         = (page - 1) * limit

        filters = {}
        if contest_type != "all":
            filters["type"] = contest_type
        if status != "all":
            filters["status"] = status

        # Do NOT exclude 'participants' from the projection here — we need it
        # to compute participantCount.  eventCode is excluded for security.
        projection = {
            "eventId": 1, "cc": 1, "name": 1, "confHomePage": 1,
            "organizer": 1, "type": 1, "startDate": 1, "endDate": 1,
            "prize": 1, "status": 1, "problems": 1, "participants": 1,
        }
        contests = list(
            db.contests.find(filters, projection)
                        .skip(skip).limit(limit).sort("_id", -1)
        )
        total = db.contests.count_documents(filters)

        for c in contests:
            c["_id"] = str(c["_id"])
            # pop() now correctly finds 'participants' because it is projected
            c["participantCount"] = len(c.pop("participants", []))

        return jsonify({
            "success": True,
            "data": contests,
            "pagination": {
                "page":  page,
                "limit": limit,
                "total": total,
                "pages": math.ceil(total / limit) if total else 0,
            },
        }), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


# NOTE: /my-contests and /my-problems MUST be registered before /<contest_id>
# so Flask does not try to resolve these literal strings as a contest_id.
# ─────────────────────────────────────────────────────────────────────────────
# MY CONTESTS  (authenticated)
# ─────────────────────────────────────────────────────────────────────────────

@contests_bp.route("/my-contests", methods=["GET"])
@token_required
def get_my_contests(current_user):
    """Return all contests the authenticated user has joined."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500

    try:
        user_id = current_user["user_id"]

        # Project participants so we can derive participantCount; hide eventCode.
        contests = list(
            db.contests.find(
                {"participants": user_id},
                {"eventCode": 0},
            ).sort("created_at", -1)
        )

        for c in contests:
            c["_id"] = str(c["_id"])
            c["participantCount"] = len(c.pop("participants", []))

        return jsonify({"success": True, "data": contests}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# MY PROBLEMS  (authenticated) — all problems from contests the user joined
# ─────────────────────────────────────────────────────────────────────────────

@contests_bp.route("/my-problems", methods=["GET"])
@token_required
def get_my_problems(current_user):
    """
    Return all problems (with full details) from every contest the
    authenticated user has joined, grouped by contest.
    """
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500

    try:
        user_id = current_user["user_id"]

        contests = list(db.contests.find(
            {"participants": user_id},
            {"eventCode": 0},
        ).sort("created_at", -1))

        groups = []
        seen_problem_ids = set()

        for c in contests:
            c["_id"] = str(c["_id"])
            c["participantCount"] = len(c.pop("participants", []))
            problem_ids = c.get("problems", [])

            problem_details = []
            for pid in problem_ids:
                p = db.problems.find_one(
                    {"problemId": pid},
                    {"fitnessFunction.globalMinimum": 0},
                )
                if p:
                    p["_id"] = str(p["_id"])
                    problem_details.append(p)
                    seen_problem_ids.add(pid)

            groups.append({
                "contestId":    c.get("eventId"),
                "contestName":  c.get("name"),
                "status":       c.get("status"),
                "problems":     problem_details,
            })

        return jsonify({
            "success": True,
            "data": {
                "groups":       groups,
                "totalProblems": len(seen_problem_ids),
            },
        }), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# CONTEST DETAIL
# ─────────────────────────────────────────────────────────────────────────────

@contests_bp.route("/<contest_id>", methods=["GET"])
def get_contest(contest_id):
    """Fetch a single contest with its problem details."""
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500

    try:
        contest = db.contests.find_one({"eventId": contest_id})
        if not contest:
            return jsonify({"message": "Contest not found"}), 404

        contest["_id"] = str(contest["_id"])

        # Optionally resolve whether the requesting user is a participant
        is_participant = False
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                token_str = auth_header.split(" ", 1)[1]
                decoded = jwt.decode(token_str, _SECRET_KEY, algorithms=["HS256"])
                uid = decoded.get("user_id")
                if uid:
                    is_participant = uid in contest.get("participants", [])
            except Exception:
                pass

        contest["isParticipant"]    = is_participant
        contest["participantCount"] = len(contest.pop("participants", []))
        contest.pop("eventCode", None)   # never expose the join code

        if contest.get("problems"):
            problem_details = []
            for pid in contest["problems"]:
                p = db.problems.find_one(
                    {"problemId": pid},
                    {"fitnessFunction.globalMinimum": 0},  # hide exact f*
                )
                if p:
                    p["_id"] = str(p["_id"])
                    problem_details.append(p)
            contest["problemDetails"] = problem_details

        return jsonify({"success": True, "data": contest}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# JOIN CONTEST  (authenticated students only)
# ─────────────────────────────────────────────────────────────────────────────

@contests_bp.route("/<contest_id>/participate", methods=["POST"])
@token_required
def participate_in_contest(current_user, contest_id):
    """
    Join a contest.  No event code required — authentication is sufficient.
    """
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500

    if current_user.get("role") != "student":
        return jsonify({"message": "Only students can join contests"}), 403

    try:
        contest = db.contests.find_one({"eventId": contest_id})
        if not contest:
            return jsonify({"message": "Contest not found"}), 404

        if contest.get("status") not in _OPEN_STATUSES:
            return jsonify({"message": "Contest is not open for registration"}), 400

        user_id      = current_user["user_id"]
        participants = contest.get("participants", [])

        if user_id in participants:
            return jsonify({"message": "You are already registered for this contest"}), 400

        db.contests.update_one(
            {"eventId": contest_id},
            {"$push": {"participants": user_id}},
        )

        return jsonify({
            "success": True,
            "message": f'Successfully joined "{contest.get("name", contest_id)}"',
        }), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# CONTEST LEADERBOARD
# Aggregate each participant's best problem scores for all contest problems,
# sum them → total contest score → rank descending (highest score = rank 1).
# ─────────────────────────────────────────────────────────────────────────────

@contests_bp.route("/<contest_id>/leaderboard", methods=["GET"])
def get_contest_leaderboard(contest_id):
    """
    Contest leaderboard.
    Score per problem = max across all contest dimensions of student's best score.
    Total contest score = sum of per-problem scores.
    Ranked descending (highest total score = rank 1).
    """
    from app import db
    if db is None:
        return jsonify({"message": "Database connection failed"}), 500

    try:
        contest = db.contests.find_one({"eventId": contest_id})
        if not contest:
            return jsonify({"message": "Contest not found"}), 404

        problem_ids  = contest.get("problems", [])
        participants = contest.get("participants", [])

        leaderboard = []

        for user_id in participants:
            try:
                student = db.students.find_one({"_id": ObjectId(user_id)})
            except Exception:
                continue
            if not student:
                continue

            problem_rankings = student.get("problem_rankings", {})
            total_score      = 0.0
            problems_scored  = 0

            for pid in problem_ids:
                dim_scores = problem_rankings.get(pid, {}).get("best_scores", {})
                if dim_scores:
                    best         = max(dim_scores.values())
                    total_score += best
                    problems_scored += 1

            leaderboard.append({
                "userId":         str(student["_id"]),
                "name":           student.get("name", "Anonymous"),
                "email":          student.get("email", ""),
                "country":        student.get("country", "N/A"),
                "institution":    student.get("institution", "N/A"),
                "totalScore":     round(total_score, 4),
                "problemsScored": problems_scored,
                "totalProblems":  len(problem_ids),
                # participantCount on the leaderboard itself is just the total
                # number of registered participants, useful for UI display
                "participantCount": len(participants),
            })

        leaderboard.sort(key=lambda e: e["totalScore"], reverse=True)

        for idx, entry in enumerate(leaderboard, start=1):
            entry["rank"] = idx

        return jsonify({"success": True, "data": leaderboard}), 200
    except Exception as exc:
        return jsonify({"message": str(exc)}), 500