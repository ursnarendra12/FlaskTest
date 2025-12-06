from flask import Blueprint, request, jsonify, current_app, make_response
from database import db
from models import User, UserSession, RefreshToken
import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from auth_middleware import token_required
from validatators.user_validatator import (
    UserCreateSchema,
    UserLoginValidation,
    UpdateUserValidation,
    UpdatePasswordValidation
)
from utils.validate_request import validate_request
from sqlalchemy import or_, func, asc, desc
import json
import secrets
from flask_cors import cross_origin

user_blueprint = Blueprint('user', __name__)

# =========================================
# 🔐 REGISTER USER
# =========================================
@user_blueprint.route('', methods=['POST'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True
)
@validate_request(UserCreateSchema)
def create_user():
    data = request.get_json()

    hashed_password = bcrypt.hashpw(
        data['password'].encode('utf-8'), bcrypt.gensalt()
    ).decode('utf-8')

    user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        mobile_number=data['mobile_number'],
        password=hashed_password,
        #organization=data['organization'],
        #status=data['status'],
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created", "id": user.id}), 201


# =========================================
# 🔐 LOGIN USER (SET COOKIES)
# =========================================
@user_blueprint.route('/login', methods=['POST'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True
)
@validate_request(UserLoginValidation)
def login_user():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode(), user.password.encode()):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Access Token
    access_exp = datetime.utcnow() + timedelta(minutes=60)
    access_token = jwt.encode(
        {"id": user.id, "email": user.email, "exp": access_exp},
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    # Refresh Token
    refresh_exp = datetime.utcnow() + timedelta(days=15)
    refresh_token = secrets.token_urlsafe(64)

    db.session.add(RefreshToken(token=refresh_token, user_id=user.id, expires=refresh_exp))
    db.session.commit()

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

    # Cookies
    response.set_cookie("access_token", access_token, httponly=True, secure=False,
                        samesite="Lax", expires=access_exp)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=False,
                        samesite="Lax", expires=refresh_exp)

    return response

#UPDATE USER
@user_blueprint.route('/<int:user_id>', methods=['PUT'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True
)
def update_user(user_id):
    data = request.get_json() or {}

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Update fields
    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user.email = data.get("email", user.email)
    user.mobile_number = data.get("mobile_number", user.mobile_number)

    # If user updates password
    if "password" in data and data["password"]:
        hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
        user.password = hashed.decode()

    db.session.commit()

    return jsonify({"message": "User updated successfully"}), 200

#GET USER BY ID
@user_blueprint.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "mobile_number": user.mobile_number
        }
    })

#CHANGE PASSWORD
@user_blueprint.route('/<int:user_id>/change-password', methods=['PUT'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True
)
def admin_change_password(user_id):
    data = request.get_json() or {}
    new_password = data.get("password")

    if not new_password:
        return jsonify({"error": "New password is required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    user.password = hashed.decode()

    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200


# =========================================
# 🔐 AUTH CHECK (ALWAYS RETURNS 200)
# =========================================
@user_blueprint.route('/auth/check', methods=['GET'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True
)
def auth_check():
    access_token = request.cookies.get("access_token")

    if not access_token:
        return jsonify({"authenticated": False}), 200

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
        return jsonify({"authenticated": False, "error": "token_expired"}), 200

    except Exception:
        return jsonify({"authenticated": False}), 200


# =========================================
# 🔄 REFRESH TOKEN
# =========================================
@user_blueprint.route('/refresh', methods=['POST'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True
)
def refresh_token():
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Refresh token missing"}), 401

    stored = RefreshToken.query.filter_by(token=refresh_token, revoked=False).first()
    if not stored or stored.expires < datetime.utcnow():
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    user = User.query.get(stored.user_id)

    new_access_exp = datetime.utcnow() + timedelta(minutes=60)
    new_access_token = jwt.encode(
        {"id": user.id, "email": user.email, "exp": new_access_exp},
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    new_refresh_token = secrets.token_urlsafe(64)
    new_refresh_exp = datetime.utcnow() + timedelta(days=15)

    stored.revoked = True
    db.session.add(RefreshToken(token=new_refresh_token, user_id=user.id, expires=new_refresh_exp))
    db.session.commit()

    response = make_response(jsonify({"message": "Token refreshed"}))

    response.set_cookie("access_token", new_access_token, httponly=True, secure=False,
                        samesite="Lax", expires=new_access_exp)
    response.set_cookie("refresh_token", new_refresh_token, httponly=True, secure=False,
                        samesite="Lax", expires=new_refresh_exp)

    return response


# =========================================
# 🔐 LOGOUT
# =========================================
@user_blueprint.route('/logout', methods=['POST'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True
)
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


# =========================================
# 📌 REMAINING ROUTES (unchanged)
# =========================================

# Dashboard
@user_blueprint.route("/dashboard", methods=["GET"])
def dashboard():
    token = request.cookies.get("access_token")
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return jsonify({
            "collectedMTD": 1234.56,
            "collectedYTD": 7890.12,
            "progress1": 86,
            "progress2": 45
        })
    except:
        return jsonify({"error": "Unauthorized"}), 401

# (Rest of your CRUD routes remain
