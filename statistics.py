from flask import Blueprint, jsonify
from datetime import datetime, timedelta

statistics_bp = Blueprint('statistics', __name__)

@statistics_bp.route('/', methods=['GET'])
def get_statistics():
    """Get platform-wide statistics"""
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        # Total counts
        total_submissions = db.submissions.count_documents({})
        total_users = db.students.count_documents({})
        total_problems = db.problems.count_documents({'status': 'active'})
        
        # Country distribution
        countries = db.students.aggregate([
            {'$group': {'_id': '$country', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        country_stats = list(countries)
        total_countries = len(country_stats)
        
        # Get specific country counts
        india_users = db.students.count_documents({'country': 'India'})
        
        # User type distribution
        academic_users = db.students.count_documents({'institution': {'$exists': True, '$ne': ''}})
        
        # Problems solved distribution (can be enhanced)
        active_users = db.students.count_documents({'problems_solved': {'$gt': 0}})
        
        # Top rankers (top 10 by rating)
        top_rankers = list(db.students.find(
            {},
            {'name': 1, 'country': 1, 'rating': 1, 'institution': 1}
        ).sort('rating', -1).limit(10))
        
        for ranker in top_rankers:
            ranker['_id'] = str(ranker['_id'])
        
        # Top contributors (admins/problem creators)
        top_contributors = db.problems.aggregate([
            {'$group': {
                '_id': '$ownerName',
                'problemCount': {'$sum': 1},
                'institution': {'$first': '$ownerInstitution'}
            }},
            {'$sort': {'problemCount': -1}},
            {'$limit': 10}
        ])
        contributor_stats = list(top_contributors)
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_submissions = db.submissions.count_documents({
            'submittedAt': {'$gte': thirty_days_ago}
        })
        recent_users = db.students.count_documents({
            'created_at': {'$gte': thirty_days_ago}
        })
        
        return jsonify({
            'success': True,
            'data': {
                'totalSubmissions': total_submissions,
                'totalUsers': total_users,
                'totalProblems': total_problems,
                'totalCountries': total_countries,
                'indiaUsers': india_users,
                'academicUsers': academic_users,
                'activeUsers': active_users,
                'topRankers': top_rankers,
                'topContributors': contributor_stats,
                'countryDistribution': country_stats[:10],  # Top 10 countries
                'recentActivity': {
                    'submissions': recent_submissions,
                    'newUsers': recent_users
                }
            }
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@statistics_bp.route('/user/<user_id>', methods=['GET'])
def get_user_statistics(user_id):
    """Get statistics for a specific user"""
    from app import db
    from bson import ObjectId
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        user = db.students.find_one({'_id': ObjectId(user_id)})
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get submission stats
        total_submissions = db.submissions.count_documents({'userId': user_id})
        
        # Get problems attempted and solved
        problem_rankings = user.get('problem_rankings', {})
        problems_attempted = len(problem_rankings)
        
        # Calculate activity heatmap (last 365 days)
        one_year_ago = datetime.utcnow() - timedelta(days=365)
        submissions_by_date = db.submissions.aggregate([
            {
                '$match': {
                    'userId': user_id,
                    'submittedAt': {'$gte': one_year_ago}
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': '$submittedAt'
                        }
                    },
                    'count': {'$sum': 1}
                }
            }
        ])
        
        activity_data = {item['_id']: item['count'] for item in submissions_by_date}
        
        # Get rank distribution across problems
        rank_distribution = []
        for problem_id, ranking in problem_rankings.items():
            overall_rank = ranking.get('overall_rank')
            total_participants = ranking.get('total_participants', 0)
            if overall_rank and total_participants:
                rank_distribution.append({
                    'problemId': problem_id,
                    'rank': overall_rank,
                    'totalParticipants': total_participants
                })
        
        user['_id'] = str(user['_id'])
        
        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'totalSubmissions': total_submissions,
                'problemsAttempted': problems_attempted,
                'activityHeatmap': activity_data,
                'rankDistribution': rank_distribution
            }
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
