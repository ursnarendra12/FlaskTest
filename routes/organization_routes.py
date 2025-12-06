from flask import Blueprint, request, jsonify, current_app, make_response
from database import db
from models import Organization
from flask_cors import cross_origin

organization_blueprint = Blueprint('organization', __name__)

#CREATE Organization
@organization_blueprint.route('', methods=['POST'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True
)
def create_organization():
    data = request.get_json()

    org = Organization(
        organization_name=data.get("organization_name"),
        address=data.get("address"),
        state=data.get("state"),
        city=data.get("city"),
        zipcode=data.get("zipcode"),
        contact_first_name=data.get("contact_first_name"),
        contact_last_name=data.get("contact_last_name"),
        contact_email=data.get("contact_email"),
        contact_mobile=data.get("contact_mobile")
    )

    db.session.add(org)
    db.session.commit()

    return jsonify({
        "message": "Organization created successfully",
        "id": org.id
    }), 201

#Get Organization
@organization_blueprint.route('/<int:id>', methods=['GET'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True
)
def get_organization(id):
    org = Organization.query.get_or_404(id)

    return jsonify({
        "id": org.id,
        "organization_name": org.organization_name,
        "address": org.address,
        "state": org.state,
        "city": org.city,
        "zipcode": org.zipcode,
        "contact_first_name": org.contact_first_name,
        "contact_last_name": org.contact_last_name,
        "contact_email": org.contact_email,
        "contact_mobile": org.contact_mobile
    })

#UPDATE Organization
@organization_blueprint.route('/<int:id>', methods=['PUT', 'OPTIONS'])
@cross_origin(
    origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    supports_credentials=True,
    allow_headers=["Content-Type"],
    methods=["PUT", "OPTIONS"]
)
def update_organization(id):
    if request.method == "OPTIONS":
        return make_response("", 200)

    data = request.get_json()
    org = Organization.query.get_or_404(id)

    org.organization_name = data.get("organization_name")
    org.address = data.get("address")
    org.state = data.get("state")
    org.city = data.get("city")
    org.zipcode = data.get("zipcode")
    org.contact_first_name = data.get("contact_first_name")
    org.contact_last_name = data.get("contact_last_name")
    org.contact_email = data.get("contact_email")
    org.contact_mobile = data.get("contact_mobile")

    db.session.commit()

    return jsonify({"message": "Organization updated successfully"}), 200

