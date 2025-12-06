from marshmallow import Schema, fields, validate, validates, ValidationError
from models import User
 

class UserCreateSchema(Schema):
    first_name = fields.Str(
        required=True,
        error_messages={"required": "First name is required."},
        validate=validate.Length(min=2, error="First name must be at least 2 characters long.")
    )

    last_name = fields.Str(
        required=True,
        error_messages={"required": "Last name is required."},
        validate=validate.Length(min=2, error="Last name must be at least 2 characters long.")
    )

    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Please enter a valid email address."
        }
    )

    password = fields.Str(
        required=True,
        error_messages={"required": "Password is required."},
        validate=validate.Length(min=6, error="Password must be at least 6 characters long.")
    )

    mobile_number = fields.Str(
        required=True,
        error_messages={"required": "Mobile number is required."},
        validate=validate.Length(equal=10, error="Mobile number must be exactly 10 digits.")
    )

    #organization = fields.Str(required=True, validate=validate.OneOf(["MedLawRCM", "JP Morgan Chase"]) )
    #status = fields.Str(required=True, validate=validate.OneOf(["Active", "Inactive"]))

    @validates("email")
    def validate_unique_email(self, value, **kwargs):
        """Ensure email is unique."""
        existing = User.query.filter_by(email=value).first()
        if existing:
            raise ValidationError("This email is already registered.")

    @validates("mobile_number")
    def validate_unique_mobile(self, value, **kwargs):
        """Ensure mobile number is unique."""
        existing = User.query.filter_by(mobile_number=value).first()
        if existing:
            raise ValidationError("This mobile number is already registered.")
        
class UserLoginValidation(Schema):
    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Please provide a valid email address."
        }
    )
    password = fields.Str(
        required=True,
        error_messages={"required": "Password is required."},
        validate=validate.Length(min=6, error="Password must be at least 6 characters long.")
    )

class UpdateUserValidation(Schema):
    def __init__(self, user_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id  # store current user ID

    email = fields.Email(
        required=False,
        error_messages={"invalid": "Please provide a valid email address."}
    )
    mobile_number = fields.Str(
        required=False,
        validate=validate.Length(equal=10, error="Mobile number must be exactly 10 digits.")
    )
    first_name = fields.Str(required=False, validate=validate.Length(min=2))
    last_name = fields.Str(required=False, validate=validate.Length(min=2))
    address = fields.Str(required=False)
    landmark = fields.Str(required=False)
    city = fields.Str(required=False)
    state = fields.Str(required=False)
    zipcode = fields.Str(required=False)

    @validates("email")
    def validate_existing_email(self, value, **kwargs):
        if not value:
            return
        user = User.query.filter(User.email == value, User.id != self.user_id).first()
        if user:
            raise ValidationError("Email is already in use by another account.")

    @validates("mobile_number")
    def validate_existing_mobile(self, value, **kwargs):
        if not value:
            return
        user = User.query.filter(User.mobile_number == value, User.id != self.user_id).first()
        if user:
            raise ValidationError("Mobile number is already in use by another account.")


class UpdatePasswordValidation(Schema):
    current_password = fields.Str(
        required=True,
        error_messages={"required": "Current password is required."}
    )
    new_password = fields.Str(
        required=True,
        error_messages={"required": "New password is required."},
        validate=validate.Length(min=6, error="New password must be at least 6 characters long.")
    )
    confirm_password = fields.Str(
        required=True,
        error_messages={"required": "Confirm password is required."}
    )

    @validates("confirm_password")
    def validate_confirm_password(self, value, **kwargs):
        # Validation only checks consistency; actual matching happens in route
        if not value:
            raise ValidationError("Confirm password cannot be empty.")