from flask import Blueprint, request, jsonify, current_app
from database import db
from models import User
import bcrypt
import jwt
import datetime
from auth_middleware import token_required
from validatators.user_validatator import UserCreateSchema, UserLoginValidation, UpdateUserValidation, UpdatePasswordValidation
from utils.validate_request import validate_request
from sqlalchemy import or_, func

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

    token = jwt.encode({
        'id': user.id,
        'email': user.email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=4)
    }, SECRET_KEY, algorithm='HS256')

    return jsonify({'token': token})

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
    user = User.query.get_or_404(request.user_id)
    return jsonify({col.name: getattr(user, col.name) for col in User.__table__.columns})

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