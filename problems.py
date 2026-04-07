"""
problems.py — TopRanker Problems Blueprint
Handles:
  - Listing / fetching problems
  - Submitting a solution vector (x values)
  - Rate limiting: 1 submission per 5 min, max 5/day → reset next day
  - Evaluating the submission against the stored fitness function
  - Scoring: lower f(x) → higher score (proximity to hidden global min)
  - Updating per-problem, per-contest, and global leaderboards
"""

import inspect
import math
from datetime import datetime, timezone, timedelta

import numpy as np
from bson import ObjectId
from flask import Blueprint, request, jsonify, Response

from auth import token_required

problems_bp = Blueprint('problems', __name__)

# ─────────────────────────────────────────────────────────────────────────────
# FITNESS FUNCTION EVALUATORS
# Each function receives a list of floats (x) and the dimension D.
# Returns float score (lower is better / closer to hidden global min).
# ─────────────────────────────────────────────────────────────────────────────

def _safe_exp(v):
    """Clamp argument to avoid overflow."""
    return math.exp(max(-700, min(700, v)))

def evaluate_TR001(x, D):
    """Cascading Tide — circular sine coupling."""
    total = 0.0
    for i in range(D):
        xi   = x[i]
        xi1  = x[(i + 1) % D]
        target = 1.0 / (i + 1)
        total += (xi - target) ** 2 + 0.3 * math.sin(3 * math.pi * xi * xi1)
    return total

def evaluate_TR002(x, D):
    """Phantom Plateau — sigmoid minus Gaussian."""
    s1 = sum(xi ** 2 for xi in x)
    s2 = sum((xi - 2) ** 2 for xi in x)
    sigmoid = 1.0 / (1.0 + _safe_exp(-0.5 * s1))
    return sigmoid - _safe_exp(-0.01 * s2)

def evaluate_TR003(x, D):
    """Spiral Sink — polar ridges on consecutive pairs."""
    total = 0.0
    for i in range(D - 1):
        xi  = x[i]
        xi1 = x[i + 1]
        theta = math.atan2(xi1, xi + 1e-9)
        r     = math.sqrt(xi ** 2 + xi1 ** 2)
        total += r ** 2 + 2 * math.sin(3 * theta + r) ** 2 + 0.1 * (xi - xi1) ** 2
    return total

def evaluate_TR004(x, D):
    """Mirage Basin — three false attractors."""
    A = sum(xi ** 2 for xi in x)
    B = sum(math.cos(2 * math.pi * xi / 3) for xi in x)
    C = sum(math.sin(math.pi * x[i]) * x[(i + 1) % D] for i in range(D))
    return A / D - 1.5 * _safe_exp(-0.1 * A) + 0.8 * B + 0.4 * abs(C)

def evaluate_TR005(x, D):
    """Recursive Ripple — four-scale fractal surface."""
    total = 0.05 * sum(xi ** 2 for xi in x)
    for k in range(1, 5):
        scale = 1.0 / (2 ** k)
        total += scale * sum(math.cos(2 ** k * math.pi * xi + k) for xi in x)
    return total

def evaluate_TR006(x, D):
    """Tidal Lock — constrained, optimum on constraint boundary."""
    obj = (sum((xi - 3) ** 2 for xi in x)
           + sum(math.sin(x[i] * x[(i + 1) % D]) for i in range(D)))
    g1_viol = max(0.0, sum(xi ** 2 for xi in x) - D * 4)
    g2_viol = sum(max(0.0, abs(x[i] - x[i + 1]) - 1.5) for i in range(D - 1))
    penalty = 1e5 * g1_viol ** 2 + 1e5 * g2_viol ** 2
    return obj + penalty

def evaluate_TR007(x, D):
    """Vortex Core — ill-conditioned rotated ellipsoid + sinusoidal overlay."""
    R = _get_rotation_matrix(D)
    y = R @ np.array(x, dtype=float)
    ell = float(y[0] ** 2 + 1e5 * sum(float(yi) ** 2 for yi in y[1:]))
    sin_overlay = float(
        sum(0.5 * math.sin(4 * math.pi * float(yi)) * float(yi) ** 2 for yi in y)
    )
    return ell + sin_overlay

# Cache rotation matrices per dimension so TR-007 produces consistent results
# across calls and we don't pay the QR cost on every evaluation.
_rotation_cache: dict = {}

def _get_rotation_matrix(D: int):
    """Return (and cache) the deterministic D×D rotation matrix for TR-007."""
    if D not in _rotation_cache:
        rng = np.random.default_rng(42)
        A = rng.standard_normal((D, D))
        R, _ = np.linalg.qr(A)
        _rotation_cache[D] = R
    return _rotation_cache[D]

def evaluate_TR008(x, D):
    """Hollow Crown — hyper-ring optimum with symmetry breaker."""
    R_target = math.sqrt(D)
    r = math.sqrt(sum(xi ** 2 for xi in x))
    ring_term = (r - R_target) ** 4
    smooth    = 0.1 * sum((x[i] - x[i + 1]) ** 2 for i in range(D - 1))
    sym_break = 0.01 * (x[0] - math.sqrt(D) / 2) ** 2
    return ring_term + smooth + sym_break

def evaluate_TR009(x, D):
    """Phase Shift Labyrinth — frequency and phase scale with D."""
    total = 0.0
    for i in range(D):
        phi_i   = 2 * math.pi * (i + 1) / D
        omega_i = 1.0 + (i + 1) / D
        total  += x[i] ** 2 * (1 + 0.5 * math.sin(omega_i * x[i] + phi_i))
    mean_term = (sum(x) / D) ** 2
    return total + 0.3 * mean_term

def evaluate_TR010(x, D):
    """Abyss Gate — fully deceptive adversarial function."""
    S = sum(x) / D
    Q = sum((xi - S) ** 2 for xi in x)
    T = sum(math.sin(x[i] ** 2 - x[(i + 1) % D]) for i in range(D))
    U = abs(sum((-1) ** i * x[i] for i in range(D)))
    return -_safe_exp(-0.5 * Q) * math.cos(2 * math.pi * S) + 0.5 * T + 0.1 * U


EVALUATORS = {
    "TR-001": evaluate_TR001,
    "TR-002": evaluate_TR002,
    "TR-003": evaluate_TR003,
    "TR-004": evaluate_TR004,
    "TR-005": evaluate_TR005,
    "TR-006": evaluate_TR006,
    "TR-007": evaluate_TR007,
    "TR-008": evaluate_TR008,
    "TR-009": evaluate_TR009,
    "TR-010": evaluate_TR010,
}

# Hidden global minima (server-side only, never exposed to clients)
HIDDEN_GLOBAL_MINIMA = {
    ("TR-001", 20):  -0.3823,
    ("TR-001", 50):  -0.5142,
    ("TR-001", 100): -0.6781,
    ("TR-002", 20):  -0.9998,
    ("TR-002", 50):  -0.9999,
    ("TR-002", 100): -1.0000,
    ("TR-003", 20):  0.0,
    ("TR-003", 50):  0.0,
    ("TR-003", 100): 0.0,
    ("TR-004", 20):  -1.5241,
    ("TR-004", 50):  -1.4982,
    ("TR-004", 100): -1.4751,
    ("TR-005", 20):  -1.8750,
    ("TR-005", 50):  -1.8750,
    ("TR-005", 100): -1.8750,
    ("TR-006", 20):  0.0,
    ("TR-006", 50):  0.0,
    ("TR-006", 100): 0.0,
    ("TR-007", 20):  0.0,
    ("TR-007", 50):  0.0,
    ("TR-007", 100): 0.0,
    ("TR-008", 20):  0.0,
    ("TR-008", 50):  0.0,
    ("TR-008", 100): 0.0,
    ("TR-009", 20):  0.0,
    ("TR-009", 50):  0.0,
    ("TR-009", 100): 0.0,
    ("TR-010", 20):  -1.0,
    ("TR-010", 50):  -1.0,
    ("TR-010", 100): -1.0,
}

# ─────────────────────────────────────────────────────────────────────────────
# SCORING
# score = 1000 / (1 + |f(x) - f*|)
# ─────────────────────────────────────────────────────────────────────────────

def compute_score(problem_id, dimension, fx_value):
    """Return a normalised score in (0, 1000]. Higher is better."""
    f_star = HIDDEN_GLOBAL_MINIMA.get((problem_id, dimension), 0.0)
    gap = abs(fx_value - f_star)
    return round(1000.0 / (1.0 + gap), 6)


# ─────────────────────────────────────────────────────────────────────────────
# RATE LIMITING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

SUBMISSION_COOLDOWN_MINUTES = 5
MAX_SUBMISSIONS_PER_DAY     = 5


def _now_utc() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def get_today_utc() -> datetime:
    """Return midnight UTC today as a timezone-aware datetime."""
    now = _now_utc()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _count_today(db, user_id: str, problem_id: str, dimension: int) -> int:
    """Count submissions made today for user/problem/dimension."""
    today_start    = get_today_utc()
    tomorrow_start = today_start + timedelta(days=1)
    return db.submissions.count_documents({
        "userId":      user_id,
        "problemId":   problem_id,
        "dimension":   dimension,
        "submittedAt": {"$gte": today_start, "$lt": tomorrow_start},
    })


def check_rate_limit(db, user_id, problem_id, dimension):
    """
    Returns (allowed: bool, reason: str | None).
    Enforces:
      - max 5 submissions per UTC day (per problem+dimension)
      - 1 submission per 5 minutes (per problem+dimension)
    """
    today_count = _count_today(db, user_id, problem_id, dimension)

    if today_count >= MAX_SUBMISSIONS_PER_DAY:
        tomorrow_start = get_today_utc() + timedelta(days=1)
        reset_time = tomorrow_start.strftime("%Y-%m-%d 00:00 UTC")
        return False, (
            f"Daily limit reached ({MAX_SUBMISSIONS_PER_DAY} submissions/day). "
            f"Resets at {reset_time}."
        )

    now             = _now_utc()
    cooldown_cutoff = now - timedelta(minutes=SUBMISSION_COOLDOWN_MINUTES)

    last_sub = db.submissions.find_one(
        {
            "userId":      user_id,
            "problemId":   problem_id,
            "dimension":   dimension,
            "submittedAt": {"$gte": cooldown_cutoff},
        },
        sort=[("submittedAt", -1)],
    )
    if last_sub:
        elapsed   = (now - last_sub["submittedAt"]).total_seconds()
        remaining = int(SUBMISSION_COOLDOWN_MINUTES * 60 - elapsed) + 1
        return False, (
            f"Please wait {remaining} second(s) before submitting again "
            f"(1 submission per {SUBMISSION_COOLDOWN_MINUTES} minutes)."
        )

    return True, None


# ─────────────────────────────────────────────────────────────────────────────
# LEADERBOARD UPDATER
# ─────────────────────────────────────────────────────────────────────────────

def update_all_leaderboards(db, user_id, problem_id, dimension, new_score, fx_value):
    """
    1. Update the student's best score for this problem+dimension (if improved).
    2. Recalculate ranks for this problem+dimension across all participants.
    3. Update the student's overall platform rating.
    """
    student = db.students.find_one({"_id": ObjectId(user_id)})
    if not student:
        return

    dim_key  = str(dimension)
    existing = (student
                .get("problem_rankings", {})
                .get(problem_id, {})
                .get("best_scores", {})
                .get(dim_key))

    is_improvement = (existing is None) or (new_score > existing)

    if is_improvement:
        db.students.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    f"problem_rankings.{problem_id}.best_scores.{dim_key}": new_score,
                    f"problem_rankings.{problem_id}.best_fx.{dim_key}":     fx_value,
                    "updated_at": _now_utc(),
                }
            },
        )

    _recalculate_dimension_ranks(db, problem_id, dimension)
    _update_platform_rating(db, user_id)


def _recalculate_dimension_ranks(db, problem_id, dimension):
    """
    Fetch every student who has a best score for this problem+dimension,
    sort descending (higher score = better), assign integer ranks, persist.
    """
    dim_key = str(dimension)
    field   = f"problem_rankings.{problem_id}.best_scores.{dim_key}"

    participants = list(db.students.find(
        {field: {"$exists": True}},
        {"_id": 1, field: 1},
    ))

    participants.sort(
        key=lambda u: (u.get("problem_rankings", {})
                        .get(problem_id, {})
                        .get("best_scores", {})
                        .get(dim_key, 0)),
        reverse=True,
    )

    total = len(participants)
    for rank, student in enumerate(participants, start=1):
        db.students.update_one(
            {"_id": student["_id"]},
            {
                "$set": {
                    f"problem_rankings.{problem_id}.ranks.{dim_key}":              rank,
                    f"problem_rankings.{problem_id}.total_participants.{dim_key}": total,
                }
            },
        )


def _update_platform_rating(db, user_id):
    """
    Platform rating = average of all best scores across all
    problem+dimension combinations the student has attempted.
    """
    student = db.students.find_one({"_id": ObjectId(user_id)})
    if not student:
        return

    all_scores = [
        score
        for prob_data in student.get("problem_rankings", {}).values()
        for score in prob_data.get("best_scores", {}).values()
    ]

    rating = round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0

    db.students.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"rating": rating, "problems_solved": len(all_scores)}},
    )


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@problems_bp.route('/', methods=['GET'])
def get_problems():
    """List problems with pagination and optional level/tag filter."""
    from app import db
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500

    try:
        page  = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        level = request.args.get('level', 'all')
        skip  = (page - 1) * limit

        filters = {'status': 'active'}
        if level != 'all':
            filters['level'] = level

        projection = {
            'problemId': 1, 'name': 1, 'level': 1, 'type': 1, 'category': 1,
            'tags': 1, 'dimensions': 1, 'totalSubmissions': 1,
            'owner': 1, 'ownerName': 1, 'ownerInstitution': 1,
            'description': 1, 'submissionDate': 1,
        }

        problems = list(db.problems.find(filters, projection)
                        .skip(skip).limit(limit).sort("problemId", 1))
        total    = db.problems.count_documents(filters)

        for p in problems:
            p['_id'] = str(p['_id'])

        return jsonify({
            'success': True,
            'data':    problems,
            'pagination': {
                'page': page, 'limit': limit,
                'total': total,
                'pages': math.ceil(total / limit) if total else 0,
            },
        }), 200
    except Exception as exc:
        return jsonify({'message': str(exc)}), 500


@problems_bp.route('/<problem_id>', methods=['GET'])
def get_problem(problem_id):
    """Fetch a single problem (fitness formula visible; global min hidden)."""
    from app import db
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500

    try:
        problem = db.problems.find_one({'problemId': problem_id})
        if not problem:
            return jsonify({'message': 'Problem not found'}), 404

        problem['_id'] = str(problem['_id'])

        if 'fitnessFunction' in problem:
            ff = dict(problem['fitnessFunction'])
            ff.pop('globalMinimum', None)
            problem['fitnessFunction'] = ff

        return jsonify({'success': True, 'data': problem}), 200
    except Exception as exc:
        return jsonify({'message': str(exc)}), 500


@problems_bp.route('/<problem_id>/fitness-code', methods=['GET'])
def get_fitness_code(problem_id):
    """Return a downloadable Python file implementing the fitness function."""
    evaluator = EVALUATORS.get(problem_id)
    if evaluator is None:
        return jsonify({'message': f'No Python evaluator available for {problem_id}'}), 404

    _NEEDS_SAFE_EXP = {"TR-002", "TR-004", "TR-007", "TR-010"}

    parts = [
        f'"""',
        f'TopRanker Fitness Function: {problem_id}',
        f'',
        f'Use this file to evaluate your solution vector locally.',
        f'Call the function with x (list of floats, length == D) and D (int).',
        f'Lower f(x) yields a higher score on the platform.',
        f'"""',
        'import math',
    ]

    if problem_id == 'TR-007':
        parts.append('import numpy as np')

    parts.append('')

    if problem_id in _NEEDS_SAFE_EXP:
        parts.append(inspect.getsource(_safe_exp).rstrip())
        parts.append('')

    if problem_id == 'TR-007':
        parts.append('_rotation_cache = {}')
        parts.append('')
        parts.append(inspect.getsource(_get_rotation_matrix).rstrip())
        parts.append('')

    parts.append(inspect.getsource(evaluator).rstrip())
    parts.append('')
    parts.append('')
    parts.append('# ── Example usage ──────────────────────────────────────────')
    parts.append(f'# D = 20')
    parts.append(f'# x = [0.0] * D')
    parts.append(f'# result = {evaluator.__name__}(x, D)')
    parts.append(f'# print(f"f(x) = {{result}}")')

    code = '\n'.join(parts)
    filename = f'fitness_{problem_id.replace("-", "_").lower()}.py'

    return Response(
        code,
        mimetype='text/x-python',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )


@problems_bp.route('/<problem_id>/submit', methods=['POST'])
@token_required
def submit_solution(current_user, problem_id):
    """
    Submit a solution vector x for a given problem and dimension.

    Request body:
    {
        "dimension": 20,
        "x": [0.1, -0.3, ...]
    }
    """
    from app import db
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500

    user_id = current_user['user_id']
    role    = current_user.get('role', 'student')

    if role != 'student':
        return jsonify({'message': 'Only students can submit solutions'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    dimension = data.get('dimension')
    x_values  = data.get('x')

    if dimension is None or x_values is None:
        return jsonify({'message': '"dimension" and "x" are required'}), 400

    if not isinstance(x_values, list):
        return jsonify({'message': '"x" must be a list of numbers'}), 400

    # Validate dimension and x are the right types
    try:
        dimension = int(dimension)
        x_values  = [float(v) for v in x_values]
    except (TypeError, ValueError):
        return jsonify({'message': 'dimension must be an integer, x must be floats'}), 400

    # Validate x values are finite numbers (no NaN / Inf from the client)
    if not all(math.isfinite(v) for v in x_values):
        return jsonify({'message': '"x" must contain only finite numbers (no NaN or Inf)'}), 400

    if len(x_values) != dimension:
        return jsonify({
            'message': f'x has {len(x_values)} values but dimension is {dimension}'
        }), 400

    # ── Verify problem exists and dimension is valid ───────────────────────
    problem = db.problems.find_one({'problemId': problem_id, 'status': 'active'})
    if not problem:
        return jsonify({'message': 'Problem not found or not active'}), 404

    valid_dimensions = [d['dimension'] for d in problem.get('dimensions', [])]
    if dimension not in valid_dimensions:
        return jsonify({
            'message': f'Invalid dimension. Choose from {valid_dimensions}'
        }), 400

    # ── Validate domain bounds ─────────────────────────────────────────────
    bounds = problem.get('fitnessFunction', {}).get('bounds', {})
    x_min  = float(bounds.get('min', -10))
    x_max  = float(bounds.get('max',  10))
    out_of_bounds = [v for v in x_values if v < x_min or v > x_max]
    if out_of_bounds:
        return jsonify({
            'message': (f'{len(out_of_bounds)} value(s) out of domain '
                        f'[{x_min}, {x_max}]. First violator: {out_of_bounds[0]}')
        }), 400

    # ── Rate limit check ───────────────────────────────────────────────────
    allowed, reason = check_rate_limit(db, user_id, problem_id, dimension)
    if not allowed:
        today_count = _count_today(db, user_id, problem_id, dimension)
        return jsonify({
            'message':               reason,
            'submissions_today':     today_count,
            'submissions_remaining': max(0, MAX_SUBMISSIONS_PER_DAY - today_count),
        }), 429

    # ── Evaluate the fitness function ──────────────────────────────────────
    evaluator = EVALUATORS.get(problem_id)
    if evaluator is None:
        return jsonify({'message': 'No evaluator available for this problem'}), 501

    try:
        fx_value = evaluator(x_values, dimension)
        if not math.isfinite(fx_value):
            fx_value = 1e18   # penalise NaN / Inf output
    except Exception as eval_err:
        return jsonify({'message': f'Evaluation error: {str(eval_err)}'}), 500

    score = compute_score(problem_id, dimension, fx_value)

    # ── Persist submission ─────────────────────────────────────────────────
    now = _now_utc()
    submission_doc = {
        "userId":      user_id,
        "userName":    current_user.get('name', ''),
        "problemId":   problem_id,
        "dimension":   dimension,
        "x":           x_values,
        "fx_value":    fx_value,
        "score":       score,
        "status":      "evaluated",
        "submittedAt": now,
    }
    insert_result = db.submissions.insert_one(submission_doc)

    # FIX: two separate $inc operations on the same update were silently
    # colliding (MongoDB ignores duplicate operator keys in a single update
    # doc). Split into two distinct update_one calls.
    db.problems.update_one(
        {"problemId": problem_id},
        {"$inc": {"totalSubmissions": 1}},
    )
    db.problems.update_one(
        {"problemId": problem_id},
        {"$inc": {"dimensions.$[elem].submissions": 1}},
        array_filters=[{"elem.dimension": dimension}],
    )

    # ── Update leaderboards ────────────────────────────────────────────────
    update_all_leaderboards(db, user_id, problem_id, dimension, score, fx_value)

    # ── Build response ─────────────────────────────────────────────────────
    today_count = _count_today(db, user_id, problem_id, dimension)

    student   = db.students.find_one({"_id": ObjectId(user_id)})
    dim_key   = str(dimension)
    rank      = (student.get("problem_rankings", {})
                         .get(problem_id, {})
                         .get("ranks", {})
                         .get(dim_key))
    total_par = (student.get("problem_rankings", {})
                         .get(problem_id, {})
                         .get("total_participants", {})
                         .get(dim_key))

    return jsonify({
        'success':               True,
        'submission_id':         str(insert_result.inserted_id),
        'fx_value':              fx_value,
        'score':                 score,
        'rank':                  rank,
        'total_participants':    total_par,
        'submissions_today':     today_count,
        'submissions_remaining': max(0, MAX_SUBMISSIONS_PER_DAY - today_count),
        'next_submission_in':    f'{SUBMISSION_COOLDOWN_MINUTES} minutes',
        'message':               'Solution evaluated successfully',
    }), 200


@problems_bp.route('/<problem_id>/my-submissions', methods=['GET'])
@token_required
def get_my_submissions(current_user, problem_id):
    """Return the current user's submission history for a problem."""
    from app import db
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500

    user_id   = current_user['user_id']
    dimension = request.args.get('dimension', type=int)

    filters = {"userId": user_id, "problemId": problem_id}
    if dimension:
        filters["dimension"] = dimension

    submissions = list(db.submissions.find(
        filters,
        {"x": 0},   # omit the full vector from the list view
    ).sort("submittedAt", -1).limit(50))

    for s in submissions:
        s['_id'] = str(s['_id'])

    today_count = _count_today(db, user_id, problem_id, dimension or 0)

    return jsonify({
        'success':               True,
        'data':                  submissions,
        'submissions_today':     today_count,
        'submissions_remaining': max(0, MAX_SUBMISSIONS_PER_DAY - today_count),
    }), 200


@problems_bp.route('/contribute', methods=['POST'])
@token_required
def contribute_problem(current_user):
    """Submit a problem contribution for admin review."""
    from app import db
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500

    data = request.get_json() or {}
    name           = data.get('name', '').strip()
    description    = data.get('description', '').strip()
    fitness_formula = data.get('fitnessFormula', '').strip()

    if not name:
        return jsonify({'message': 'Problem name is required'}), 400
    if not description:
        return jsonify({'message': 'Problem description is required'}), 400
    if not fitness_formula:
        return jsonify({'message': 'Fitness function formula is required'}), 400

    contribution = {
        'name':           name,
        'level':          data.get('level', 'Medium'),
        'description':    description,
        'fitnessFormula': fitness_formula,
        'constraint':     data.get('constraint', ''),
        'submitterId':    current_user['user_id'],
        'submitterName':  current_user.get('name', ''),
        'submitterEmail': current_user.get('email', ''),
        'status':         'pending',
        'submittedAt':    datetime.now(timezone.utc),
    }

    result = db.contributions.insert_one(contribution)
    return jsonify({
        'success': True,
        'message': 'Contribution submitted! Admin will review it shortly.',
        'id':      str(result.inserted_id),
    }), 201


@problems_bp.route('/<problem_id>/leaderboard', methods=['GET'])
def get_problem_leaderboard(problem_id):
    """
    Return ranked list of students for a specific problem+dimension.
    Sorted by score descending (higher score = better).
    """
    from app import db
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500

    dimension = request.args.get('dimension', type=int)
    if not dimension:
        return jsonify({'message': '"dimension" query param is required'}), 400

    page  = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    skip  = (page - 1) * limit

    dim_key = str(dimension)
    score_f = f"problem_rankings.{problem_id}.best_scores.{dim_key}"
    rank_f  = f"problem_rankings.{problem_id}.ranks.{dim_key}"
    fx_f    = f"problem_rankings.{problem_id}.best_fx.{dim_key}"

    students = list(db.students.find(
        {score_f: {"$exists": True}},
        {"name": 1, "email": 1, "country": 1, "institution": 1,
         score_f: 1, rank_f: 1, fx_f: 1},
    ).sort(score_f, -1).skip(skip).limit(limit))

    total = db.students.count_documents({score_f: {"$exists": True}})

    board = []
    for idx, s in enumerate(students, start=skip + 1):
        pr = s.get("problem_rankings", {}).get(problem_id, {})
        board.append({
            "rank":        pr.get("ranks", {}).get(dim_key, idx),
            "userId":      str(s["_id"]),
            "name":        s.get("name", "Anonymous"),
            "country":     s.get("country", "N/A"),
            "institution": s.get("institution", "N/A"),
            "score":       pr.get("best_scores", {}).get(dim_key, 0),
            "fx_value":    pr.get("best_fx", {}).get(dim_key, None),
        })

    return jsonify({
        'success': True,
        'data':    board,
        'pagination': {
            'page': page, 'limit': limit,
            'total': total,
            'pages': math.ceil(total / limit) if total else 0,
        },
    }), 200