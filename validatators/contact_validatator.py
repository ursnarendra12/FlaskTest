from marshmallow import Schema, fields, validate, validates, ValidationError
from models import Contact

class ContactCreateSchema(Schema):
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)

    email = fields.Email(required=True)
    mobile_number = fields.Str(
        required=True,
        validate=validate.Length(equal=10)
    )

    @validates("email")
    def validate_email_unique(self, value, **kwargs):
        if Contact.query.filter_by(email=value).first():
            raise ValidationError("Email already exists.")

    @validates("mobile_number")
    def validate_mobile_unique(self, value, **kwargs):
        if Contact.query.filter_by(mobile_number=value).first():
            raise ValidationError("Mobile number already exists.")
    
    address = fields.String(required=False, allow_none=True)
    landmark = fields.String(required=False, allow_none=True)
    city = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    zipcode = fields.String(required=False, allow_none=True)
    


class ContactUpdateSchema(Schema):
    def __init__(self, contact_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contact_id = contact_id

    first_name = fields.Str()
    last_name = fields.Str()
    email = fields.Email()
    mobile_number = fields.Str(validate=validate.Length(equal=10))

    @validates("email")
    def validate_unique_email(self, value, **kwargs):
        existing = Contact.query.filter_by(email=value).first()
        if existing and existing.id != self.contact_id:
            raise ValidationError("Email already exists")

    @validates("mobile_number")
    def validate_unique_mobile(self, value, **kwargs):
        existing = Contact.query.filter_by(mobile_number=value).first()
        if existing and existing.id != self.contact_id:
            raise ValidationError("Mobile number already exists")

    address = fields.String(allow_none=True)
    landmark = fields.String(allow_none=True)
    city = fields.String(allow_none=True)
    state = fields.String(allow_none=True)
    zipcode = fields.String(allow_none=True)

