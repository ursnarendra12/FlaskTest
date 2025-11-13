from flask import Blueprint, request, jsonify, current_app
from database import db
from models import User, UserSession
import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from auth_middleware import token_required
from validatators.user_validatator import UserCreateSchema, UserLoginValidation, UpdateUserValidation, UpdatePasswordValidation
from utils.validate_request import validate_request
from sqlalchemy import or_, func
#from redis_client import redis_client
import json

user_blueprint = Blueprint('user', __name__)

SECRET_KEY = "my_secret_key"

# REGISTER (Create User)
@user_blueprint.route('/', methods=['POST'])
@validate_request(UserCreateSchema)
def create_user():
    data = request.get_json()

    hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

    user = User(**{**data, 'password': hashed.decode('utf-8')})
    db.session.add(user)
    db.session.commit()

    return jsonify({'id': user.id, 'message': 'User created successfully'}), 201
    

# LOGIN (Generate JWT)
@user_blueprint.route('/login', methods=['POST'])
@validate_request(UserLoginValidation)
def login_user():
    data = request.get_json() or {}
    email, password = data.get('email'), data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate JWT token
    expiry_time = datetime.utcnow() + timedelta(hours=4)
    token = jwt.encode({
        'id': user.id,
        'email': user.email,
        'exp': expiry_time
    }, SECRET_KEY, algorithm='HS256')

    # Convert token to string (for PostgreSQL Text column)
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.user_agent.string

    # Create a session record
    new_session = UserSession(
        user_id=user.id,
        token=token,
        status=True,
        expiry=expiry_time,
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.session.add(new_session)
    db.session.commit()

    return jsonify({
        'token': token,
        'session_id': str(new_session.id),
        'expiry': expiry_time.isoformat()
    }), 200

# Get all licenses for a user
@user_blueprint.route('/<int:user_id>/licenses', methods=['GET'])
@token_required
def get_user_licenses(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Access licenses from the relationship
    licenses = [
        {
            'id': license.id,
            'license_key': license.license_key,
            'concurrent_session_count': license.concurrent_session_count,
            'created_at': license.created_at.isoformat(),
            'updated_at': license.updated_at.isoformat() if license.updated_at else None
        }
        for license in user.licenses
    ]

    return jsonify({
        'user_id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'licenses': licenses
    }), 200

# Get all sessions for a user
@user_blueprint.route('/<int:user_id>/sessions', methods=['GET'])
#@token_required
def get_user_sessions(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404
    # Access sessions from the relationship
    sessions = [
        {
            'id': sessions.id,
            'user_id': sessions.user.id,
            'token': sessions.token,
            'status': sessions.status,
            'expiry': sessions.expiry.isoformat(),
            'ip_address': sessions.ip_address,
            'user_agent' : sessions.user_agent
        }
        for sessions in user.sessions
    ]
    return jsonify({
        'user_id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'sessions': sessions
    }), 200

# GET ALL USERS
@user_blueprint.route('/', methods=['GET'])
@token_required
def get_users():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    search = request.args.get('search', '').strip()

    query = User.query

    if search:
        # Combine first_name and last_name for name-based search
        full_name = func.concat(User.first_name, ' ', User.last_name)
        query = query.filter(
            or_(
                full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.mobile_number.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(User.id.desc()).paginate(page=page, per_page=limit, error_out=False)

    users_data = [
        {
            col.name: getattr(user, col.name)
            for col in User.__table__.columns
            if col.name != 'password'
        }
        for user in pagination.items
    ]
    return jsonify({
        "data": users_data,
        "meta": {
            "page": page,
            "limit": limit,
            "total": pagination.total,
            "pages": pagination.pages
        }
    })

# GET SINGLE USER
@user_blueprint.route('/<int:id>', methods=['GET'])
@token_required
def get_user(id):
    user = User.query.get_or_404(id)
    
    user_data = {
        col.name: getattr(user, col.name)
        for col in User.__table__.columns
        if col.name != 'password'
    }
    
    return jsonify(user_data)


# UPDATE USER
@user_blueprint.route('/<int:id>', methods=['PUT'])
@token_required
def update_user(id):
    user = User.query.get_or_404(id)

    data = request.get_json()
    schema = UpdateUserValidation(user_id=id)
    validated_data = schema.load(data)

    for key, value in validated_data.items():
        setattr(user, key, value)

    db.session.commit()

    return jsonify({'message': 'User updated successfully'})

# DELETE USER
@user_blueprint.route('/<int:id>', methods=['DELETE'])
@token_required
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})


# PROFILE_ROUTE
@user_blueprint.route('/profile', methods=['GET'])
@token_required
def get_profile():
    try:

        #cache_key = f"user:{request.user_id}"

        #cached_user = redis_client.get(cache_key)
        #if cached_user:
         #   return jsonify(json.loads(cached_user)), 200
        
        user = User.query.get_or_404(request.user_id)
        user_data = {
            col.name : getattr(user, col.name)
            for col in User.__table__.columns
            if col.name != 'password'
        }
        #redis_client.setex(cache_key, 300, json.dumps(user_data))
        return jsonify(user_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500




   # return jsonify({col.name: getattr(user, col.name) for col in User.__table__.columns})

# CHANGE PASSWORD
@user_blueprint.route('/change-password', methods=['PUT'])
@token_required
@validate_request(UpdatePasswordValidation)
def change_password():
    data = request.get_json() or {}
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

    # Get logged-in user
    user = User.query.get_or_404(request.user_id)

    # Verify current password
    if not bcrypt.checkpw(current_password.encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'error': 'Current password is incorrect.'}), 401
    
    # Hash and update new password
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    user.password = hashed.decode('utf-8')
    db.session.commit()

    return jsonify({'message': 'Password updated successfully.'}), 200