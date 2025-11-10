from flask import Blueprint, request, jsonify, current_app
from database import db
from models import License
from validatators.license_validatator import LicenseCreateValidation
from utils.validate_request import validate_request
from auth_middleware import token_required
from sqlalchemy import or_, func

license_blueprint = Blueprint('license', __name__)

SECRET_KEY = "my_secret_key"

#Create License
@license_blueprint.route('/', methods =['POST'])
@validate_request(LicenseCreateValidation)
def create_license():
    data = request.get_json()

    license = License(**{**data})
    db.session.add(license)
    db.session.commit()

    return jsonify({'id': license.id, 'message': 'License created successfully'}), 201

#Get All Licenses
@license_blueprint.route('/', methods=['GET'])
def get_licenses():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    search = request.args.get('search', '').strip()

    query = License.query

    if search:
        query = query.filter(
            or_(
                License.license_key.ilike(f"%{search}%"),
                func.cast(License.concurrent_session_count, db.String).ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(License.id.desc()).paginate(page=page, per_page=limit, error_out=False)

    licenses_data = [
        {
            col.name: getattr(license, col.name)
            for col in License.__table__.columns
        }
        for license in pagination.items
    ]

    return jsonify({
        "data": licenses_data,
        "meta": {
            "page": page,
            "limit": limit,
            "total": pagination.total,
            "pages": pagination.pages
        }
    }), 200


# Get Single License
@license_blueprint.route('/<int:license_id>', methods=['GET'])
def get_license(license_id):
    license = License.query.get(license_id)
    if not license:
        return jsonify({"error": "License not found"}), 404

    data = {col.name: getattr(license, col.name) for col in License.__table__.columns}
    return jsonify(data), 200


# Delete License
@license_blueprint.route('/<int:license_id>', methods=['DELETE'])
def delete_license(license_id):
    license = License.query.get(license_id)
    if not license:
        return jsonify({"error": "License not found"}), 404

    db.session.delete(license)
    db.session.commit()

    return jsonify({"message": "License deleted successfully"}), 200

@license_blueprint.route('/invoke', methods=['GET'])
@token_required
def get_license():
    user = User.query.get_or_404(request.user_id)
    if user.license_key:
        return jsonify
    license_key = '2393846'
    concurrent_sessions = 3
    license = License.query.get(license_id)
    if not license:
        return jsonify({"error": "License not found"}), 404

    data = {col.name: getattr(license, col.name) for col in License.__table__.columns}
    return jsonify(data), 200
