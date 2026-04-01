"""
Ranking System for TopRanker
Calculates and updates user rankings based on problem submissions.
"""

# FIX: datetime was used in update_user_rankings() but only imported locally
# at the bottom of the file inside recalculate_all_rankings() — any call to
# update_user_rankings() before recalculate_all_rankings() ran would raise a
# NameError.  Import it at module level here.
from datetime import datetime, timezone
from bson import ObjectId


def _now_utc() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def calculate_problem_rankings(db, problem_id, dimension=None):
    """
    Calculate rankings for a specific problem and (optionally) one dimension.
    Returns a nested dict: { problem_id: { user_id: { dimension_ranks, best_scores } } }
    """
    problem = db.problems.find_one({"problemId": problem_id})
    if not problem:
        return {}

    dimensions_to_process = (
        [dimension] if dimension
        else [d['dimension'] for d in problem.get('dimensions', [])]
    )

    rankings: dict = {}

    for dim in dimensions_to_process:
        # Best score per user across all their submissions for this dim
        submissions = list(db.submissions.find(
            {
                'problemId': problem_id,
                'dimension': dim,
                'status':    'evaluated',
                'score':     {'$ne': None},
            }
        ))

        user_best: dict = {}
        for sub in submissions:
            uid   = sub['userId']
            score = sub['score']
            if uid not in user_best or score > user_best[uid]['score']:
                user_best[uid] = {'score': score, 'submission_id': sub['_id']}

        # Rank users by best score descending (higher = better)
        sorted_users = sorted(user_best.items(), key=lambda kv: kv[1]['score'], reverse=True)

        for rank, (user_id, data) in enumerate(sorted_users, start=1):
            rankings.setdefault(problem_id, {}).setdefault(user_id, {
                'dimension_ranks': {},
                'best_scores':     {},
            })
            rankings[problem_id][user_id]['dimension_ranks'][dim] = rank
            rankings[problem_id][user_id]['best_scores'][dim]     = data['score']

    return rankings


def calculate_overall_problem_rank(db, problem_id, user_id):
    """
    Calculate the overall rank for a user on a specific problem.
    Based on average of per-dimension ranks (lower average = better overall rank).
    Returns the integer overall rank, or None if no data.
    """
    student = db.students.find_one({"_id": ObjectId(user_id)})
    if not student:
        return None

    problem_rankings = student.get('problem_rankings', {})
    if problem_id not in problem_rankings:
        return None

    dimension_ranks = problem_rankings[problem_id].get('dimension_ranks', {})
    if not dimension_ranks:
        return None

    avg_rank = sum(dimension_ranks.values()) / len(dimension_ranks)

    # Get every student who has attempted this problem
    all_users = list(db.students.find(
        {f'problem_rankings.{problem_id}': {'$exists': True}},
        {f'problem_rankings.{problem_id}.dimension_ranks': 1},
    ))

    user_avg_ranks = []
    for user in all_users:
        user_dim_ranks = (user.get('problem_rankings', {})
                              .get(problem_id, {})
                              .get('dimension_ranks', {}))
        if user_dim_ranks:
            user_avg = sum(user_dim_ranks.values()) / len(user_dim_ranks)
            user_avg_ranks.append((str(user['_id']), user_avg))

    # Lower average dimension rank → better overall rank
    user_avg_ranks.sort(key=lambda x: x[1])

    for idx, (uid, _) in enumerate(user_avg_ranks):
        if uid == str(user_id):
            return idx + 1

    return None


def update_user_rankings(db, user_id, problem_id, dimension):
    """
    Update a specific user's rankings after a new submission.
    Called incrementally (per-submission) rather than doing a full recalc.
    """
    rankings = calculate_problem_rankings(db, problem_id, dimension)

    if not rankings or problem_id not in rankings or user_id not in rankings[problem_id]:
        return False

    user_ranking_data = rankings[problem_id][user_id]

    # FIX: datetime.utcnow() replaced with timezone-aware _now_utc()
    update_data = {
        f'problem_rankings.{problem_id}.dimension_ranks.{dimension}':
            user_ranking_data['dimension_ranks'][dimension],
        f'problem_rankings.{problem_id}.best_scores.{dimension}':
            user_ranking_data['best_scores'][dimension],
        'updated_at': _now_utc(),
    }

    overall_rank = calculate_overall_problem_rank(db, problem_id, user_id)
    if overall_rank is not None:
        update_data[f'problem_rankings.{problem_id}.overall_rank'] = overall_rank

    db.students.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': update_data},
    )

    return True


def recalculate_all_rankings(db):
    """
    Recalculate all rankings for all active problems.
    Useful for initial setup or after data migration.
    """
    problems = list(db.problems.find({'status': 'active'}))

    for problem in problems:
        problem_id = problem['problemId']
        rankings   = calculate_problem_rankings(db, problem_id)

        for pid, user_rankings in rankings.items():
            for user_id, ranking_data in user_rankings.items():
                # FIX: datetime is now imported at module level so this
                # always works, even when called without first calling
                # recalculate_all_rankings (the original file imported
                # datetime locally inside this function only).
                update_data = {
                    f'problem_rankings.{pid}': ranking_data,
                    'updated_at':              _now_utc(),
                }

                overall_rank = calculate_overall_problem_rank(db, pid, user_id)
                if overall_rank is not None:
                    update_data[f'problem_rankings.{pid}.overall_rank'] = overall_rank

                db.students.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': update_data},
                )

    return True


def get_user_problem_rankings(db, user_id):
    """
    Get all problem rankings for a specific user,
    enriched with total participant counts per dimension.
    """
    student = db.students.find_one({'_id': ObjectId(user_id)})
    if not student:
        return {}

    problem_rankings  = student.get('problem_rankings', {})
    enhanced_rankings = {}

    for problem_id, ranking_data in problem_rankings.items():
        enhanced = ranking_data.copy()

        dimension_totals: dict = {}
        for dim in ranking_data.get('dimension_ranks', {}).keys():
            total_participants = db.students.count_documents({
                f'problem_rankings.{problem_id}.dimension_ranks.{dim}': {'$exists': True}
            })
            dimension_totals[dim] = total_participants

        enhanced['dimension_totals'] = dimension_totals

        total_problem_participants = db.students.count_documents({
            f'problem_rankings.{problem_id}.overall_rank': {'$exists': True}
        })
        enhanced['total_participants'] = total_problem_participants

        enhanced_rankings[problem_id] = enhanced

    return enhanced_rankings
