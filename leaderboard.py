from flask import Blueprint, jsonify, request
from bson import ObjectId
from functools import wraps
import jwt
import os

leaderboard_bp = Blueprint('leaderboard', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            data = jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'your-secret-key'), algorithms=['HS256'])
            current_user = data
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@leaderboard_bp.route('/users', methods=['GET'])
def get_user_leaderboard():
    """Get global user leaderboard based on ratings"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        skip = (page - 1) * limit
        
        # Get users sorted by rating
        users = list(db.students.find(
            {},
            {'name': 1, 'email': 1, 'country': 1, 'institution': 1, 'rating': 1, 'problemsSolved': 1}
        ).sort('rating', -1).skip(skip).limit(limit))
        
        total = db.students.count_documents({})
        
        # Format leaderboard
        leaderboard = []
        for idx, user in enumerate(users, start=skip + 1):
            # Get user's submission stats
            total_submissions = db.submissions.count_documents({'userId': str(user['_id'])})
            problems_attempted = len(db.submissions.distinct('problemId', {'userId': str(user['_id'])}))
            
            leaderboard.append({
                'rank': idx,
                'userId': str(user['_id']),
                'name': user.get('name', 'Anonymous'),
                'country': user.get('country', 'N/A'),
                'institution': user.get('institution', 'N/A'),
                'rating': user.get('rating', 0),
                'problemsSolved': problems_attempted,
                'totalSubmissions': total_submissions
            })
        
        return jsonify({
            'success': True,
            'data': leaderboard,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@leaderboard_bp.route('/countries', methods=['GET'])
def get_country_leaderboard():
    """Get country leaderboard based on average user ratings and total users"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        # Aggregate by country
        pipeline = [
            {
                '$match': {
                    'country': {'$exists': True, '$ne': None, '$ne': ''}
                }
            },
            {
                '$group': {
                    '_id': '$country',
                    'totalUsers': {'$sum': 1},
                    'avgRating': {'$avg': '$rating'},
                    'totalRating': {'$sum': '$rating'}
                }
            },
            {
                '$sort': {'totalRating': -1}
            },
            {
                '$limit': 100
            }
        ]
        
        countries = list(db.students.aggregate(pipeline))
        
        # Format leaderboard
        leaderboard = []
        for idx, country in enumerate(countries, start=1):
            # Get total submissions from this country
            users_from_country = db.students.distinct('_id', {'country': country['_id']})
            total_submissions = db.submissions.count_documents({
                'userId': {'$in': [str(uid) for uid in users_from_country]}
            })
            
            leaderboard.append({
                'rank': idx,
                'country': country['_id'],
                'totalUsers': country['totalUsers'],
                'avgRating': round(country['avgRating'], 2) if country['avgRating'] else 0,
                'totalRating': round(country['totalRating'], 2),
                'totalSubmissions': total_submissions
            })
        
        return jsonify({
            'success': True,
            'data': leaderboard
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@leaderboard_bp.route('/institutions', methods=['GET'])
def get_institution_leaderboard():
    """Get institution leaderboard based on total users and ratings"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        # Aggregate by institution
        pipeline = [
            {
                '$match': {
                    'institution': {'$exists': True, '$ne': None, '$ne': ''}
                }
            },
            {
                '$group': {
                    '_id': '$institution',
                    'country': {'$first': '$country'},
                    'totalUsers': {'$sum': 1},
                    'avgRating': {'$avg': '$rating'},
                    'totalRating': {'$sum': '$rating'}
                }
            },
            {
                '$sort': {'totalRating': -1}
            },
            {
                '$limit': 100
            }
        ]
        
        institutions = list(db.students.aggregate(pipeline))
        
        # Format leaderboard
        leaderboard = []
        for idx, inst in enumerate(institutions, start=1):
            # Get total submissions from this institution
            users_from_inst = db.students.distinct('_id', {'institution': inst['_id']})
            total_submissions = db.submissions.count_documents({
                'userId': {'$in': [str(uid) for uid in users_from_inst]}
            })
            
            leaderboard.append({
                'rank': idx,
                'institution': inst['_id'],
                'country': inst.get('country', 'N/A'),
                'totalUsers': inst['totalUsers'],
                'avgRating': round(inst['avgRating'], 2) if inst['avgRating'] else 0,
                'totalRating': round(inst['totalRating'], 2),
                'totalSubmissions': total_submissions
            })
        
        return jsonify({
            'success': True,
            'data': leaderboard
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@leaderboard_bp.route('/problem-setters', methods=['GET'])
def get_problem_setter_leaderboard():
    """Get problem setter leaderboard based on number of problems contributed"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        # Aggregate by problem owner
        pipeline = [
            {
                '$match': {
                    'ownerName': {'$exists': True, '$ne': None, '$ne': ''}
                }
            },
            {
                '$group': {
                    '_id': '$ownerName',
                    'institution': {'$first': '$ownerInstitution'},
                    'totalProblems': {'$sum': 1},
                    'totalSubmissions': {'$sum': '$totalSubmissions'},
                    'avgAcceptanceRate': {'$avg': '$acceptanceRate'}
                }
            },
            {
                '$sort': {'totalProblems': -1}
            },
            {
                '$limit': 100
            }
        ]
        
        setters = list(db.problems.aggregate(pipeline))
        
        # Format leaderboard
        leaderboard = []
        for idx, setter in enumerate(setters, start=1):
            leaderboard.append({
                'rank': idx,
                'name': setter['_id'],
                'institution': setter.get('institution', 'N/A'),
                'totalProblems': setter['totalProblems'],
                'totalSubmissions': setter['totalSubmissions'],
                'avgAcceptanceRate': round(setter['avgAcceptanceRate'], 2) if setter['avgAcceptanceRate'] else 0
            })
        
        return jsonify({
            'success': True,
            'data': leaderboard
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
