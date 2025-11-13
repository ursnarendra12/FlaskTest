from marshmallow import Schema, fields, validate, validates, ValidationError
from models import License

class LicenseCreateValidation(Schema):
    license_key = fields.Str(
        required=True,
        error_messages={"required": "License key is required."},
        validate=validate.Length(min=6, error="License key  must be at least 6 characters long.")
    )

    concurrent_session_count = fields.Int(
    required=True,
    error_messages={"required": "Concurrent session count is required."},
    validate=validate.Range(
        min=1,
        max=10,
        error="Concurrent session count must be between 1 and 10."
    )
    )

    @validates("license_key")
    def validate_unique_license_key(self, value, **kwargs):
        """Ensure license key is unique."""
        existing = License.query.filter_by(license_key=value).first()
        if existing:
            raise ValidationError("This license key is already registered.")
        
# Update License Validation
class LicenseUpdateValidation(Schema):
    license_key = fields.Str(
        required=False,
        validate=validate.Length(min=6, error="License key must be at least 6 characters long.")
    )
    concurrent_session_count = fields.Int(
        required=False,
        validate=validate.Range(
            min=1,
            max=10, 
            error="Concurrent session count must be between 1 and 10.")
    )

    # Ensure unique key if updating license_key
    @validates("license_key")
    def validate_unique_license_key(self, value, **kwargs):
        existing = License.query.filter_by(license_key=value).first()
        if existing:
            raise ValidationError("This license key is already registered.")
        
class UpdateLicenseStatusValidation(Schema):
    status = fields.Bool(
        required=True,
        error_messages={
            "required": "Status is required.",
        }
    )

class UpdateLicenseBlockValidation(Schema):
    is_blocked = fields.Bool(
        required=True,
        error_messages={
            "required": "Block is required.",
        }
    )