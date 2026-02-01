from flask import Blueprint, request, jsonify
from auth import token_required
from models import Problem, Submission
from datetime import datetime
from bson import ObjectId

problems_bp = Blueprint('problems', __name__)

@problems_bp.route('/', methods=['GET'])
def get_problems():
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        difficulty = request.args.get('difficulty', 'All')
        
        skip = (page - 1) * limit
        
        filters = {}
        if difficulty != 'All':
            filters['level'] = difficulty
        
        problems, total = Problem.find_all(db, filters, skip, limit)
        
        for problem in problems:
            problem['_id'] = str(problem['_id'])
        
        return jsonify({
            'success': True,
            'data': problems,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@problems_bp.route('/<problem_id>', methods=['GET'])
def get_problem(problem_id):
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        problem = Problem.find_by_id(db, problem_id)
        
        if not problem:
            return jsonify({'message': 'Problem not found'}), 404
        
        problem['_id'] = str(problem['_id'])
        
        return jsonify({
            'success': True,
            'data': problem
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@problems_bp.route('/<problem_id>/submit', methods=['POST'])
@token_required
def submit_solution(current_user, problem_id):
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    solution = data.get('solution')
    dimension = data.get('dimension')
    
    if not all([solution, dimension]):
        return jsonify({'message': 'Solution array and dimension are required'}), 400
    
    problem = Problem.find_by_id(db, problem_id)
    if not problem:
        return jsonify({'message': 'Problem not found'}), 404
    
    # Parse solution array
    try:
        # Handle different input formats: "[1,2,3]" or "1,2,3" or "1 2 3"
        solution_str = solution.strip()
        if solution_str.startswith('[') and solution_str.endswith(']'):
            solution_str = solution_str[1:-1]
        
        # Split by comma or space
        if ',' in solution_str:
            solution_array = [float(x.strip()) for x in solution_str.split(',')]
        else:
            solution_array = [float(x.strip()) for x in solution_str.split()]
        
        # Validate dimension
        if len(solution_array) != int(dimension):
            return jsonify({
                'message': f'Solution array length ({len(solution_array)}) does not match dimension ({dimension})'
            }), 400
            
    except ValueError as e:
        return jsonify({'message': f'Invalid solution format: {str(e)}'}), 400
    
    # Validate solution bounds
    from evaluate_solution import validate_solution
    is_valid, error_msg = validate_solution(problem_id, solution_array)
    if not is_valid:
        return jsonify({'message': error_msg}), 400
    
    submission_data = {
        'problemId': problem_id,
        'userId': current_user['user_id'],
        'userEmail': current_user['email'],
        'userName': current_user.get('name', ''),
        'code': str(solution_array),
        'language': 'array',
        'dimension': int(dimension),
        'solutionArray': solution_array
    }
    
    try:
        submission = Submission.create(db, submission_data)
        
        # Evaluate the solution immediately
        from evaluate_solution import evaluate_fitness
        score = evaluate_fitness(problem_id, solution_array)
        
        # Update submission with score
        Submission.update_evaluation(db, submission['_id'], score)
        
        Problem.increment_submissions(db, problem_id, int(dimension))
        
        # Update user rankings
        from ranking_system import update_user_rankings
        update_user_rankings(db, current_user['user_id'], problem_id, int(dimension))
        
        return jsonify({
            'success': True,
            'message': 'Solution submitted and evaluated successfully',
            'submissionId': str(submission['_id']),
            'score': score
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@problems_bp.route('/<problem_id>/submissions', methods=['GET'])
@token_required
def get_user_submissions(current_user, problem_id):
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        submissions = Submission.find_by_user(db, current_user['user_id'], problem_id)
        
        for sub in submissions:
            sub['_id'] = str(sub['_id'])
        
        return jsonify({
            'success': True,
            'data': submissions
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@problems_bp.route('/submissions/all', methods=['GET'])
@token_required
def get_all_user_submissions(current_user):
    """Get all submissions by the current user across all problems"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit
        
        submissions = list(db.submissions.find(
            {'userId': current_user['user_id']}
        ).sort('submittedAt', -1).skip(skip).limit(limit))
        
        total = db.submissions.count_documents({'userId': current_user['user_id']})
        
        # Get problem details for each submission
        for sub in submissions:
            sub['_id'] = str(sub['_id'])
            problem = db.problems.find_one({'problemId': sub['problemId']})
            if problem:
                sub['problemName'] = problem['name']
                sub['problemLevel'] = problem['level']
        
        return jsonify({
            'success': True,
            'data': submissions,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@problems_bp.route('/<problem_id>/leaderboard', methods=['GET'])
def get_problem_leaderboard(problem_id):
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        dimension = int(request.args.get('dimension', '20'))
        
        # Get all submissions for this problem-dimension
        submissions = list(db.submissions.find({
            'problemId': problem_id,
            'dimension': dimension,
            'status': 'evaluated',
            'score': {'$ne': None}
        }).sort('score', 1))
        
        # Get best score per user
        user_best = {}
        for sub in submissions:
            user_id = sub['userId']
            if user_id not in user_best or sub['score'] < user_best[user_id]['score']:
                user_best[user_id] = {
                    'score': sub['score'],
                    'userName': sub['userName'],
                    'userEmail': sub['userEmail'],
                    'submittedAt': sub['submittedAt']
                }
        
        # Create leaderboard
        leaderboard = []
        for user_id, data in user_best.items():
            # Get user details
            user = db.students.find_one({'_id': ObjectId(user_id)})
            entry = {
                'userId': user_id,
                'userName': data['userName'],
                'userEmail': data['userEmail'],
                'score': data['score'],
                'submittedAt': data['submittedAt']
            }
            if user:
                entry['institution'] = user.get('institution', '')
                entry['country'] = user.get('country', '')
            leaderboard.append(entry)
        
        # Sort by score
        leaderboard.sort(key=lambda x: x['score'])
        
        # Add ranks
        for idx, entry in enumerate(leaderboard, 1):
            entry['rank'] = idx
        
        return jsonify({
            'success': True,
            'data': leaderboard,
            'dimension': dimension
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@problems_bp.route('/<problem_id>/leaderboard/all', methods=['GET'])
def get_problem_leaderboard_all_dimensions(problem_id):
    """Get leaderboard for all dimensions of a problem"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        leaderboards = {}
        
        for dimension in [20, 50, 100]:
            # Get submissions for this dimension
            submissions = list(db.submissions.find({
                'problemId': problem_id,
                'dimension': dimension,
                'status': 'evaluated',
                'score': {'$ne': None}
            }).sort('score', 1).limit(10))  # Top 10 per dimension
            
            # Get best score per user
            user_best = {}
            for sub in submissions:
                user_id = sub['userId']
                if user_id not in user_best or sub['score'] < user_best[user_id]['score']:
                    user_best[user_id] = {
                        'score': sub['score'],
                        'userName': sub['userName'],
                        'userEmail': sub['userEmail']
                    }
            
            # Create leaderboard
            dim_leaderboard = []
            for user_id, data in user_best.items():
                user = db.students.find_one({'_id': ObjectId(user_id)})
                entry = {
                    'userId': user_id,
                    'userName': data['userName'],
                    'score': data['score']
                }
                if user:
                    entry['institution'] = user.get('institution', '')
                    entry['country'] = user.get('country', '')
                dim_leaderboard.append(entry)
            
            # Sort and add ranks
            dim_leaderboard.sort(key=lambda x: x['score'])
            for idx, entry in enumerate(dim_leaderboard, 1):
                entry['rank'] = idx
            
            leaderboards[f'D{dimension}'] = dim_leaderboard
        
        return jsonify({
            'success': True,
            'data': leaderboards
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@problems_bp.route('/user/rankings', methods=['GET'])
@token_required
def get_user_rankings(current_user):
    from app import db
    from ranking_system import get_user_problem_rankings
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        rankings = get_user_problem_rankings(db, current_user['user_id'])
        
        return jsonify({
            'success': True,
            'data': rankings
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@problems_bp.route('/contribute', methods=['POST'])
@token_required
def contribute_problem(current_user):
    """Allow users to contribute new problems"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'description', 'level']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'{field} is required'}), 400
    
    try:
        # Get user info
        user = db.students.find_one({'_id': ObjectId(current_user['user_id'])})
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Generate new problem ID
        last_problem = db.problems.find_one(sort=[('problemId', -1)])
        new_id = str(int(last_problem['problemId']) - 1) if last_problem else '1000'
        
        problem_data = {
            'problemId': new_id,
            'name': data['name'],
            'description': data['description'],
            'level': data['level'],
            'owner': f"{user['name']}, {user.get('institution', 'Individual')}",
            'ownerName': user['name'],
            'ownerInstitution': user.get('institution', 'Individual'),
            'cc': '🌍',  # Default flag
            'type': data.get('type', 'Optimization'),
            'category': data.get('category', 'User Contributed'),
            'tags': data.get('tags', ['optimization', 'user-contributed']),
            'dimensions': [
                {'dimension': 20, 'submissions': 0},
                {'dimension': 50, 'submissions': 0},
                {'dimension': 100, 'submissions': 0}
            ],
            'fitnessFunction': {
                'formula': data.get('formula', ''),
                'constraint': data.get('constraint', ''),
                'codeFiles': {
                    'python': '',
                    'java': '',
                    'cpp': '',
                    'c': ''
                }
            },
            'totalSubmissions': 0,
            'totalSolved': 0,
            'acceptanceRate': 0.0,
            'submissionDate': datetime.utcnow(),
            'status': 'pending',  # Requires admin approval
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.problems.insert_one(problem_data)
        
        return jsonify({
            'success': True,
            'message': 'Problem submitted for review',
            'problemId': new_id
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500