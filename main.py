from flask import Flask, jsonify
from flask_cors import CORS
from database import init_db, db
from routes.user_routes import user_blueprint
from routes.organization_routes import organization_blueprint
from routes.license_routes import license_blueprint
from routes.contact_routes import contact_blueprint
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------
# FIX: FULL CORS SUPPORT FOR COOKIES
# ---------------------------------------------------------
CORS(app,
    supports_credentials=True,
    resources={r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]
    }}
)
# ---------------------------------------------------------

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my_secret_key')

init_db(app)
migrate = Migrate(app, db)

app.register_blueprint(user_blueprint, url_prefix='/api/users')
app.register_blueprint(organization_blueprint, url_prefix="/api/organizations")
app.register_blueprint(license_blueprint, url_prefix='/api/licenses')
app.register_blueprint(contact_blueprint, url_prefix='/api/contacts')
# ---------------------------------------------------------
# FIX: FORCE HEADERS AFTER RESPONSE
# ---------------------------------------------------------
@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response
# ---------------------------------------------------------

@app.route('/')
def home():
    return jsonify({'message': 'Flask API running'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
