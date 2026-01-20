"""
Ranking System for TopRanker
Calculates and updates user rankings based on problem submissions
"""

from bson import ObjectId

def calculate_problem_rankings(db, problem_id, dimension=None):
    """
    Calculate rankings for a specific problem and dimension
    Returns updated rankings for all users who submitted to this problem
    """
    problem = db.problems.find_one({"problemId": problem_id})
    if not problem:
        return []
    
    dimensions_to_process = [dimension] if dimension else [d['dimension'] for d in problem.get('dimensions', [])]
    
    rankings = {}
    
    for dim in dimensions_to_process:
        # Get all evaluated submissions for this problem and dimension, sorted by score (ascending for minimization)
        submissions = list(db.submissions.find({
            'problemId': problem_id,
            'dimension': dim,
            'status': 'evaluated',
            'score': {'$ne': None}
        }).sort('score', 1))  # 1 for ascending (lower score is better)
        
        # Calculate ranks
        current_rank = 1
        prev_score = None
        rank_count = 0
        
        user_best_scores = {}
        
        for submission in submissions:
            user_id = submission['userId']
            score = submission['score']
            
            # Track best score per user
            if user_id not in user_best_scores or score < user_best_scores[user_id]['score']:
                user_best_scores[user_id] = {
                    'score': score,
                    'submission_id': submission['_id']
                }
        
        # Now rank users based on their best scores
        sorted_users = sorted(user_best_scores.items(), key=lambda x: x[1]['score'])
        
        for idx, (user_id, data) in enumerate(sorted_users):
            rank = idx + 1
            
            if problem_id not in rankings:
                rankings[problem_id] = {}
            if user_id not in rankings[problem_id]:
                rankings[problem_id][user_id] = {
                    'dimension_ranks': {},
                    'best_scores': {}
                }
            
            rankings[problem_id][user_id]['dimension_ranks'][dim] = rank
            rankings[problem_id][user_id]['best_scores'][dim] = data['score']
    
    return rankings

def calculate_overall_problem_rank(db, problem_id, user_id):
    """
    Calculate overall rank for a user on a specific problem
    Based on average of dimension ranks
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
    
    # Calculate average rank across dimensions
    avg_rank = sum(dimension_ranks.values()) / len(dimension_ranks)
    
    # Get all users who have submitted to this problem
    all_users = db.students.find({
        f'problem_rankings.{problem_id}': {'$exists': True}
    })
    
    # Calculate their average ranks
    user_avg_ranks = []
    for user in all_users:
        user_dim_ranks = user.get('problem_rankings', {}).get(problem_id, {}).get('dimension_ranks', {})
        if user_dim_ranks:
            user_avg = sum(user_dim_ranks.values()) / len(user_dim_ranks)
            user_avg_ranks.append((str(user['_id']), user_avg))
    
    # Sort by average rank
    user_avg_ranks.sort(key=lambda x: x[1])
    
    # Find user's overall rank
    for idx, (uid, _) in enumerate(user_avg_ranks):
        if uid == user_id:
            return idx + 1
    
    return None

def update_user_rankings(db, user_id, problem_id, dimension):
    """
    Update a specific user's rankings after a new submission
    """
    # Recalculate rankings for this problem and dimension
    rankings = calculate_problem_rankings(db, problem_id, dimension)
    
    if problem_id not in rankings or user_id not in rankings[problem_id]:
        return False
    
    user_ranking_data = rankings[problem_id][user_id]
    
    # Update student's problem_rankings
    update_data = {
        f'problem_rankings.{problem_id}.dimension_ranks.{dimension}': user_ranking_data['dimension_ranks'][dimension],
        f'problem_rankings.{problem_id}.best_scores.{dimension}': user_ranking_data['best_scores'][dimension],
        'updated_at': datetime.utcnow()
    }
    
    # Calculate overall problem rank
    overall_rank = calculate_overall_problem_rank(db, problem_id, user_id)
    if overall_rank:
        update_data[f'problem_rankings.{problem_id}.overall_rank'] = overall_rank
    
    db.students.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': update_data}
    )
    
    return True

def recalculate_all_rankings(db):
    """
    Recalculate all rankings for all problems
    Useful for initial setup or after data migration
    """
    from datetime import datetime
    
    problems = db.problems.find({'status': 'active'})
    
    for problem in problems:
        problem_id = problem['problemId']
        rankings = calculate_problem_rankings(db, problem_id)
        
        # Update all users
        for pid, user_rankings in rankings.items():
            for user_id, ranking_data in user_rankings.items():
                update_data = {
                    f'problem_rankings.{pid}': ranking_data,
                    'updated_at': datetime.utcnow()
                }
                
                # Calculate overall rank
                overall_rank = calculate_overall_problem_rank(db, pid, user_id)
                if overall_rank:
                    update_data[f'problem_rankings.{pid}.overall_rank'] = overall_rank
                
                db.students.update_one(
                    {'_id': ObjectId(user_id)},
                    {'$set': update_data}
                )
    
    return True

def get_user_problem_rankings(db, user_id):
    """
    Get all problem rankings for a specific user with total participant counts
    """
    student = db.students.find_one({'_id': ObjectId(user_id)})
    if not student:
        return {}
    
    problem_rankings = student.get('problem_rankings', {})
    
    # Enhance rankings with total participant counts
    enhanced_rankings = {}
    for problem_id, ranking_data in problem_rankings.items():
        enhanced_rankings[problem_id] = ranking_data.copy()
        
        # Get total participants per dimension
        dimension_totals = {}
        if 'dimension_ranks' in ranking_data:
            for dimension in ranking_data['dimension_ranks'].keys():
                # Count unique users who submitted for this dimension
                total_participants = db.students.count_documents({
                    f'problem_rankings.{problem_id}.dimension_ranks.{dimension}': {'$exists': True}
                })
                dimension_totals[dimension] = total_participants
        
        enhanced_rankings[problem_id]['dimension_totals'] = dimension_totals
        
        # Get total participants for overall problem
        total_problem_participants = db.students.count_documents({
            f'problem_rankings.{problem_id}.overall_rank': {'$exists': True}
        })
        enhanced_rankings[problem_id]['total_participants'] = total_problem_participants
    
    return enhanced_rankings

from datetime import datetime
