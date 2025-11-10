from flask import Flask, jsonify
from flask_cors import CORS
from database import init_db, db
from routes.user_routes import user_blueprint
from routes.license_routes import license_blueprint
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_secret_key')

init_db(app)

app.register_blueprint(user_blueprint, url_prefix = '/api/users')

app.register_blueprint(license_blueprint, url_prefix = '/api/licenses')



@app.route('/')
def home():
    return jsonify({'message': 'Flask + SQLAlchemy + PostgreSQL API is running '})

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Route not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(host='0.0.0.0', port=5000, debug=True)
