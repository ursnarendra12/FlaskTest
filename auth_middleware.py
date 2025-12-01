import jwt
from flask import request, jsonify, current_app
from functools import wraps
from models import UserSession

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 1. Try Authorization header first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        # 2. Fallback to cookie named 'access_token'
        if not token:
            token = request.cookies.get('access_token')

        if not token:
            return jsonify({'error': 'Token is missing!'}), 401

        try:
            # Decode the JWT
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            # Attach user info to request context for downstream use
            request.user_id = payload['id']
            request.user_email = payload['email']

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401
        except Exception as e:
            return jsonify({'error': f'Token decode error: {str(e)}'}), 401

        return f(*args, **kwargs)

    return decorated