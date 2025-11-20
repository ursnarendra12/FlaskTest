import jwt
from flask import request, jsonify, current_app
from functools import wraps
from models import UserSession

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        # If not found, check in secure cookie
        if not token and 'auth_token' in request.cookies:
            token = request.cookies.get('auth_token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Decode the JWT
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = data['id']

            # Check if session exists in DB and is active
            session = UserSession.query.filter_by(token=token, user_id=user_id, status=True).first()
            if not session:
                return jsonify({'message': 'Session is invalid or has been logged out!'}), 401

            # Attach user_id and session_id to the request for downstream use
            request.user_id = user_id
            request.session_id = str(session.id)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(*args, **kwargs)
    return decorated