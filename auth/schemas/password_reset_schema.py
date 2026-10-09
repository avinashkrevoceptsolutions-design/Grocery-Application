from marshmallow import Schema, fields, validate, ValidationError
import re

class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True, error_messages={'required': 'Email is required', 'invalid': 'Invalid email format'})

class ValidateResetTokenSchema(Schema):
    token = fields.String(required=True, validate=validate.Length(min=1), error_messages={'required': 'Token is required'})

class ResetPasswordSchema(Schema):
    token = fields.String(required=True, validate=validate.Length(min=1), error_messages={'required': 'Token is required'})
    new_password = fields.String(required=True, validate=validate.Length(min=8), error_messages={'required': 'Password is required', 'validator_failed': 'Password must be at least 8 characters'})
    confirm_password = fields.String(required=True, error_messages={'required': 'Password confirmation is required'})
    
    def validate_password_strength(self, password):
        """Validate password meets complexity requirements"""
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character')
    
    def load(self, data, **kwargs):
        result = super().load(data, **kwargs)
        if result.get('new_password') != result.get('confirm_password'):
            raise ValidationError('Passwords do not match')
        self.validate_password_strength(result.get('new_password'))
        return result