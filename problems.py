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

@problems_bp.route('/<problem_id>/leaderboard', methods=['GET'])
def get_problem_leaderboard(problem_id):
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        dimension = int(request.args.get('dimension', '20'))
        
        leaderboard = Submission.get_leaderboard(db, problem_id, dimension)
        
        for entry in leaderboard:
            entry['_id'] = str(entry['_id'])
        
        return jsonify({
            'success': True,
            'data': leaderboard
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
