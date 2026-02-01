from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from models import Student, Admin
import os

auth_bp = Blueprint('auth', __name__)

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/signup', methods=['POST'])
def signup():
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'student')
    
    if not all([name, email, password]):
        return jsonify({'message': 'Name, email, and password are required'}), 400
    
    if role not in ['student', 'admin']:
        return jsonify({'message': 'Invalid role. Must be student or admin'}), 400
    
    if role == 'student':
        existing_user = Student.find_by_email(db, email)
    else:
        existing_user = Admin.find_by_email(db, email)
    
    if existing_user:
        return jsonify({'message': 'User with this email already exists'}), 409
    
    hashed_password = generate_password_hash(password)
    
    user_data = {
        'name': name,
        'email': email,
        'password': hashed_password
    }
    
    if role == 'student':
        user_data['institution'] = data.get('institution', '')
        user_data['country'] = data.get('country', '')
        user = Student.create(db, user_data)
    else:
        user = Admin.create(db, user_data)
    
    token = jwt.encode({
        'user_id': str(user['_id']),
        'email': user['email'],
        'name': user.get('name', user['email']),
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        'message': 'User created successfully',
        'token': token,
        'user': {
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email'],
            'role': role
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'student')
    
    if not all([email, password]):
        return jsonify({'message': 'Email and password are required'}), 400
    
    if role not in ['student', 'admin']:
        return jsonify({'message': 'Invalid role'}), 400
    
    if role == 'student':
        user = Student.find_by_email(db, email)
    else:
        user = Admin.find_by_email(db, email)
    
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    if not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = jwt.encode({
        'user_id': str(user['_id']),
        'email': user['email'],
        'name': user.get('name', user['email']),
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'role': user['role'],
        'user_id': str(user['_id']),
        'email': user['email'],
        'userName': user.get('name', user['email'])
    }), 200

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    from app import db
    
    if db is None:
        return jsonify({'message': 'Database connection failed'}), 500
    
    role = current_user.get('role')
    user_id = current_user.get('user_id')
    
    if role == 'student':
        user = Student.find_by_id(db, user_id)
    else:
        user = Admin.find_by_id(db, user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'valid': True,
        'user': {
            'id': str(user['_id']),
            'name': user['name'],
            'email': user['email'],
            'role': role
        }
    }), 200
