from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from marshmallow import ValidationError
from models import Contact
from database import db
from validatators.contact_validatator import ContactCreateSchema, ContactUpdateSchema
from utils.validate_request import validate_request

contact_blueprint = Blueprint("contacts", __name__, url_prefix="/api/contacts")



# ----------------------------
# CORS for React localhost:5173
# ----------------------------
@contact_blueprint.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


# ----------------------------
# CREATE CONTACT
# ----------------------------
@contact_blueprint.route("", methods=["POST"])
@cross_origin(supports_credentials=True)
@validate_request(ContactCreateSchema)
def create_contact():
    data = request.get_json()

    contact = Contact(
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        email=data.get("email"),
        mobile_number=data.get("mobile_number"),
        address=data.get("address"),
        landmark=data.get("landmark"),
        city=data.get("city"),
        state=data.get("state"),
        zipcode=data.get("zipcode")
    )

    db.session.add(contact)
    db.session.commit()

    return jsonify({"message": "Contact created", "id": contact.id}), 201
# ----------------------------
# GET ALL CONTACTS
# ----------------------------
@contact_blueprint.route("/", methods=["GET"])
def get_contacts():
    contacts = Contact.query.all()

    data = []
    for c in contacts:
        data.append({
            "id": c.id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
            "mobile_number": c.mobile_number
        })

    return jsonify(data), 200


# ----------------------------
# GET CONTACT BY ID
# ----------------------------
@contact_blueprint.route("/<int:id>", methods=["GET"])
def get_contact(id):
    contact = Contact.query.get(id)
    if not contact:
        return jsonify({"error": "Contact not found"}), 404

    return jsonify({
        "id": contact.id,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "email": contact.email,
        "mobile_number": contact.mobile_number,
        "address": contact.address,
        "landmark": contact.landmark,
        "city": contact.city,
        "state": contact.state,
        "zipcode": contact.zipcode
    }), 200


# ----------------------------
# UPDATE CONTACT
# ----------------------------
@contact_blueprint.route("/<int:contact_id>", methods=["PUT"])
@cross_origin(supports_credentials=True)
def update_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)

    # Pass current ID to validator to avoid duplicate errors
    schema = ContactUpdateSchema(contact_id=contact_id)

    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    # Update fields dynamically
    for key, value in data.items():
        setattr(contact, key, value)

    db.session.commit()

    return jsonify({
        "message": "Contact updated successfully",
        "contact": {
            "id": contact.id,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "mobile_number": contact.mobile_number,
            "address": contact.address,
            "landmark": contact.landmark,
            "city": contact.city,
            "state": contact.state,
            "zipcode": contact.zipcode,
            "created_at": contact.created_at
        }
    }), 200



# ----------------------------
# DELETE CONTACT
# ----------------------------
@contact_blueprint.route("/<int:id>", methods=["DELETE"])
def delete_contact(id):
    contact = Contact.query.get(id)
    if not contact:
        return jsonify({"error": "Contact not found"}), 404

    db.session.delete(contact)
    db.session.commit()

    return jsonify({"message": "Contact deleted"}), 200
