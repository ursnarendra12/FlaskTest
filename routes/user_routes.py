from flask import Blueprint, request, jsonify, current_app, make_response
from database import db
from models import User, UserSession
import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from auth_middleware import token_required
from validatators.user_validatator import UserCreateSchema, UserLoginValidation, UpdateUserValidation, UpdatePasswordValidation
from utils.validate_request import validate_request
from sqlalchemy import or_, func, asc, desc
#from redis_client import redis_client
import json
import secrets
from models import RefreshToken
from flask_cors import cross_origin

user_blueprint = Blueprint('user', __name__)

SECRET_KEY = "my_secret_key"

# REGISTER (Create User)
@user_blueprint.route('/', methods=['POST'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True
)
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
@cross_origin(
    origins=["http://localhost:5173"],
    supports_credentials=True
)
@validate_request(UserLoginValidation)
def login_user():
    data = request.get_json() or {}
    email, password = data.get("email"), data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password.encode()):
        return jsonify({"error": "Invalid credentials"}), 401

    # 1) Access token
    access_exp = datetime.utcnow() + timedelta(minutes=60)
    access_token = jwt.encode(
        {"id": user.id, "email": user.email, "exp": access_exp},
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    # 2) Refresh token
    refresh_exp = datetime.utcnow() + timedelta(days=15)
    refresh_token = secrets.token_urlsafe(64)

    # Save refresh token in DB
    new_refresh = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires=refresh_exp
    )
    db.session.add(new_refresh)
    db.session.commit()

    # -------------------------
    # ADD USER DETAILS IN RESPONSE
    # -------------------------
    user_data = {
        "id": user.id,
        "first_name": getattr(user, "first_name", None),
        "last_name": getattr(user, "last_name", None),
        "email": user.email
    }

    response = make_response(jsonify({
        "message": "Login successful",
        "user": user_data
    }))

    # COOKIE: Access Token
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=False,              # OK for localhost, must be True in production (HTTPS)
        samesite="None",           # IMPORTANT for cross-site cookies
        expires=access_exp,
        domain="localhost"         # ensures cookie works for 5173 → 5000
    )

    # COOKIE: Refresh Token
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=False,
        samesite="None",
        expires=refresh_exp,
        domain="localhost"
    )


    return response

#Create Auth Check
@user_blueprint.route('/auth/check', methods=['GET'])
def auth_check():
    access_token = request.cookies.get("access_token")
    print('Narendra')
    print(access_token)

    if not access_token:
        return jsonify({"authenticated": False}), 401

    try:
        decoded = jwt.decode(
            access_token,
            current_app.config["SECRET_KEY"],
            algorithms=["HS256"]
        )
        return jsonify({
            "authenticated": True,
            "user": {
                "id": decoded["id"],
                "email": decoded["email"]
            }
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"authenticated": False, "error": "token_expired"}), 401

    except Exception:
        return jsonify({"authenticated": False}), 401

#REFRESH
@user_blueprint.route('/refresh', methods=['POST'])
def refresh_token():
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Refresh token missing"}), 401

    # Check in DB
    stored = RefreshToken.query.filter_by(token=refresh_token, revoked=False).first()
    if not stored:
        return jsonify({"error": "Invalid refresh token"}), 401
    if stored.expires < datetime.utcnow():
        return jsonify({"error": "Refresh token expired"}), 401

    user = User.query.get(stored.user_id)

    # Generate new access token
    new_access_exp = datetime.utcnow() + timedelta(minutes=60)
    new_access_token = jwt.encode(
        {"id": user.id, "email": user.email, "exp": new_access_exp},
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    # ROTATE refresh token (recommended)
    new_refresh_token = secrets.token_urlsafe(64)
    new_refresh_exp = datetime.utcnow() + timedelta(days=15)

    # revoke old refresh token
    stored.revoked = True

    # save new one
    fresh = RefreshToken(
        token=new_refresh_token,
        user_id=user.id,
        expires=new_refresh_exp
    )
    db.session.add(fresh)
    db.session.commit()

    response = make_response(jsonify({"message": "Token refreshed"}))

    response.set_cookie(
        "access_token",
        new_access_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        expires=new_access_exp
    )

    response.set_cookie(
        "refresh_token",
        new_refresh_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        expires=new_refresh_exp
    )

    return response

#Dashboard
@user_blueprint.route("/dashboard", methods=["GET"])
def dashboard():
    token = request.cookies.get("access_token")
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # Fetch real stats from DB
        return jsonify({
            "collectedMTD": 1234.56,
            "collectedYTD": 7890.12,
            "progress1": 86,
            "progress2": 45
        })
    except:
        return jsonify({"error": "Unauthorized"}), 401


#Logout User
@user_blueprint.route('/logout', methods=['POST'])
def logout_user():
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        stored = RefreshToken.query.filter_by(token=refresh_token).first()
        if stored:
            stored.revoked = True
            db.session.commit()

    response = make_response(jsonify({"message": "Logout successful"}))
    response.set_cookie("access_token", "", expires=0)
    response.set_cookie("refresh_token", "", expires=0)

    return response

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
#@cross_origin(origins=["http://localhost:5173"], supports_credentials=True)
def get_users():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    search = request.args.get('search', '').strip()
    sort_field = request.args.get('sortField', 'id')
    sort_order = int(request.args.get('sortOrder', -1))  # 1 for ASC, -1 for DESC

    query = User.query

    # Search
    if search:
        full_name = func.concat(User.first_name, ' ', User.last_name)
        query = query.filter(
            or_(
                full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.mobile_number.ilike(f"%{search}%")
            )
        )

    # Sorting
    if hasattr(User, sort_field):
        column_attr = getattr(User, sort_field)
        if sort_order == 1:
            query = query.order_by(asc(column_attr))
        else:
            query = query.order_by(desc(column_attr))
    else:
        # Default sort by id DESC
        query = query.order_by(User.id.desc())

    # Pagination
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

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
@user_blueprint.route("/profile", methods=["GET"])
def profile():
    token = request.cookies.get("access_token")
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"id": payload["id"], "email": payload["email"]})
    except:
        return jsonify({"error": "Unauthorized"}), 401


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