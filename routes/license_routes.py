from flask import Blueprint, request, jsonify, current_app
from database import db
from models import License
from validatators.license_validatator import LicenseCreateValidation,UpdateLicenseStatusValidation,UpdateLicenseBlockValidation
from utils.validate_request import validate_request
from auth_middleware import token_required
from sqlalchemy import or_, func

license_blueprint = Blueprint('license', __name__)

# Create License
@license_blueprint.route('/', methods=['POST'])
@token_required
@validate_request(LicenseCreateValidation)
def create_license():
    data = request.get_json()
    
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return jsonify({'error': 'User ID is missing from request context'}), 400

    # ✅ Check if license already exists for this user
    existing_license = License.query.filter_by(user_id=user_id).first()
    if existing_license:
        return jsonify({
            'error': 'License already exists for this user',
            'license_id': existing_license.id,
            'license_key': existing_license.license_key
        }), 400

    # Create new license if none exists
    new_license = License(**{**data, 'user_id': user_id})
    db.session.add(new_license)
    db.session.commit()

    return jsonify({
        'id': new_license.id,
        'user_id': new_license.user_id,
        'message': 'License created successfully'
    }), 201

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


# Get user of a specific license
@license_blueprint.route('/<int:license_id>/user', methods=['GET'])
@token_required
def get_license_user(license_id):
    license = License.query.get(license_id)

    if not license:
        return jsonify({'error': 'License not found'}), 404

    if not license.user:
        return jsonify({'error': 'User not associated with this license'}), 404

    user = license.user

    return jsonify({
        'license_id': license.id,
        'license_key': license.license_key,
        'user': {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'mobile_number': user.mobile_number,
            'city': user.city,
            'state': user.state
        }
    }), 200

## License Status
@license_blueprint.route('/<int:license_id>/status', methods=['PUT'])
@token_required
def license_status(license_id):
    license = License.query.get_or_404(license_id)

    data = request.get_json()
    schema = UpdateLicenseStatusValidation()
    validated_data = schema.load(data)

    for key, value in validated_data.items():
        setattr(license, key, value)

    db.session.commit()

    return jsonify({'message': 'License status updated successfully'})

## License Block
@license_blueprint.route('/<int:license_id>/block', methods=['PUT'])
@token_required
def license_block(license_id):
    license = License.query.get_or_404(license_id)

    data = request.get_json()
    schema = UpdateLicenseBlockValidation()
    validated_data = schema.load(data)

    for key, value in validated_data.items():
        setattr(license, key, value)

    db.session.commit()

    return jsonify({'message': 'License block updated successfully'})


"""@user_blueprint.route('/<int:id>', methods=['PUT'])
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


# Admin Block License
@license_blueprint.route('/<int:license_id>/block', methods=['PUT'])
@token_required
def block_license(license_id):
    license = License.query.get(license_id)
    if not license:
        return jsonify({'error': 'License not found'}), 404

    license.is_blocked = True
    license.status = False
    license.appeal_status = "none"
    db.session.commit()

    return jsonify({
        'license_id': license.id,
        'license_key': license.license_key,
        'status': license.status,
        'is_blocked': license.is_blocked,
        'message': 'License has been blocked by admin.'
    }), 200



# User Appeal for Blocked License
@license_blueprint.route('/<int:license_id>/appeal', methods=['POST'])
@token_required
def appeal_license(license_id):
    license = License.query.get(license_id)
    if not license:
        return jsonify({'error': 'License not found'}), 404

    if not license.is_blocked:
        return jsonify({'message': 'License is not blocked; appeal not required.'}), 400

    data = request.get_json()
    appeal_message = data.get('appeal_message', '').strip()

    if not appeal_message:
        return jsonify({'error': 'Appeal message is required.'}), 400

    license.appeal_message = appeal_message
    license.appeal_status = "pending"
    db.session.commit()

    return jsonify({
        'license_id': license.id,
        'license_key': license.license_key,
        'appeal_status': license.appeal_status,
        'message': 'Appeal submitted successfully.'
    }), 200


# Admin Review Appeal (Approve/Reject)
@license_blueprint.route('/<int:license_id>/appeal/review', methods=['PUT'])
@token_required
def review_appeal(license_id):
    license = License.query.get(license_id)
    if not license:
        return jsonify({'error': 'License not found'}), 404

    data = request.get_json()
    action = data.get('action')  # "approve" or "reject"

    if action not in ['approve', 'reject']:
        return jsonify({'error': 'Invalid action. Use approve or reject.'}), 400

    if license.appeal_status != "pending":
        return jsonify({'message': 'No pending appeal found.'}), 400

    if action == 'approve':
        license.is_blocked = False
        license.status = True
        license.appeal_status = "approved"
    else:
        license.appeal_status = "rejected"

    db.session.commit()

    return jsonify({
        'license_id': license.id,
        'license_key': license.license_key,
        'appeal_status': license.appeal_status,
        'is_blocked': license.is_blocked,
        'status': license.status,
        'message': f'Appeal {action}ed successfully.'
    }), 200"""