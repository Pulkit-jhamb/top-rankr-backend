from flask import Blueprint, request, jsonify
from auth import token_required
from datetime import datetime
from bson import ObjectId

contests_bp = Blueprint('contests', __name__)

@contests_bp.route('/', methods=['GET'])
def get_contests():
    """Get all contests with pagination and filtering"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        contest_type = request.args.get('type', 'all')
        status = request.args.get('status', 'all')
        
        skip = (page - 1) * limit
        
        # Build filters
        filters = {}
        if contest_type != 'all':
            filters['type'] = contest_type
        if status != 'all':
            filters['status'] = status
        
        # Get contests with optimized query
        # Use projection to only fetch needed fields for list view
        projection = {
            'eventId': 1, 'cc': 1, 'name': 1, 'confHomePage': 1, 
            'organizer': 1, 'type': 1, 'startDate': 1, 'endDate': 1, 
            'prize': 1, 'status': 1, 'problems': 1
        }
        contests = list(db.contests.find(filters, projection).skip(skip).limit(limit).sort("_id", -1))
        total = db.contests.count_documents(filters)
        
        # Convert ObjectId to string
        for contest in contests:
            contest['_id'] = str(contest['_id'])
        
        return jsonify({
            'success': True,
            'data': contests,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@contests_bp.route('/<contest_id>', methods=['GET'])
def get_contest(contest_id):
    """Get single contest details"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        contest = db.contests.find_one({"eventId": contest_id})
        
        if not contest:
            return jsonify({'message': 'Contest not found'}), 404
        
        contest['_id'] = str(contest['_id'])
        
        # Get problem details for each problem in contest
        if 'problems' in contest and contest['problems']:
            problem_details = []
            for problem_id in contest['problems']:
                problem = db.problems.find_one({"problemId": problem_id})
                if problem:
                    problem['_id'] = str(problem['_id'])
                    problem_details.append(problem)
            contest['problemDetails'] = problem_details
        
        return jsonify({
            'success': True,
            'data': contest
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@contests_bp.route('/<contest_id>/participate', methods=['POST'])
@token_required
def participate_in_contest(current_user, contest_id):
    """Join a contest with event code"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    data = request.get_json()
    event_code = data.get('eventCode')
    
    if not event_code:
        return jsonify({'message': 'Event code is required'}), 400
    
    try:
        contest = db.contests.find_one({"eventId": contest_id})
        
        if not contest:
            return jsonify({'message': 'Contest not found'}), 404
        
        # Verify event code
        if contest.get('eventCode') != event_code:
            return jsonify({'message': 'Invalid event code'}), 403
        
        # Check if already participated
        participants = contest.get('participants', [])
        user_id = current_user['user_id']
        
        if user_id in participants:
            return jsonify({'message': 'Already participating in this contest'}), 400
        
        # Add user to participants
        db.contests.update_one(
            {"eventId": contest_id},
            {"$push": {"participants": user_id}}
        )
        
        return jsonify({
            'success': True,
            'message': 'Successfully joined the contest'
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@contests_bp.route('/<contest_id>/leaderboard', methods=['GET'])
def get_contest_leaderboard(contest_id):
    """Get contest leaderboard - aggregate scores across all problems"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        contest = db.contests.find_one({"eventId": contest_id})
        
        if not contest:
            return jsonify({'message': 'Contest not found'}), 404
        
        problem_ids = contest.get('problems', [])
        participants = contest.get('participants', [])
        
        # Calculate scores for each participant
        leaderboard = []
        
        for user_id in participants:
            user = db.students.find_one({"_id": ObjectId(user_id)})
            if not user:
                continue
            
            total_score = 0
            problems_solved = 0
            problem_rankings = user.get('problem_rankings', {})
            
            # Aggregate scores from all contest problems
            for problem_id in problem_ids:
                if problem_id in problem_rankings:
                    ranking = problem_rankings[problem_id]
                    # Use average of best scores across dimensions
                    best_scores = ranking.get('best_scores', {})
                    if best_scores:
                        avg_score = sum(best_scores.values()) / len(best_scores)
                        total_score += avg_score
                        problems_solved += 1
            
            leaderboard.append({
                'userId': str(user['_id']),
                'userName': user['name'],
                'email': user['email'],
                'institution': user.get('institution', ''),
                'country': user.get('country', ''),
                'totalScore': total_score,
                'problemsSolved': problems_solved
            })
        
        # Sort by total score (ascending for minimization)
        leaderboard.sort(key=lambda x: x['totalScore'])
        
        # Add ranks
        for idx, entry in enumerate(leaderboard, 1):
            entry['rank'] = idx
        
        return jsonify({
            'success': True,
            'data': leaderboard
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@contests_bp.route('/my-contests', methods=['GET'])
@token_required
def get_my_contests(current_user):
    """Get contests user is participating in"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        user_id = current_user['user_id']
        
        # Find contests where user is a participant
        contests = list(db.contests.find({
            "participants": user_id
        }).sort("created_at", -1))
        
        for contest in contests:
            contest['_id'] = str(contest['_id'])
        
        return jsonify({
            'success': True,
            'data': contests
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
