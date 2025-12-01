from database import db
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    landmark = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(50), nullable=True) 
    state = db.Column(db.String(50), nullable=True)
    zipcode = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    license = db.relationship('License', back_populates='user', uselist=False, cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', back_populates='user', cascade='all, delete-orphan')

    


    

class License(db.Model):
    __tablename__ = 'licenses'  

    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(120), unique=True, nullable=False)
    concurrent_session_count = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # New fields for status and blocking system
    status = db.Column(db.DateTime, default=datetime.utcnow)          
    is_blocked = db.Column(db.Boolean, default=False, nullable=False)     
    

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

 
    user = db.relationship('User', back_populates='license')

class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.Text, nullable=False)
    status = db.Column(db.Boolean, default=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    expiry = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='sessions')


class RefreshToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    expires = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)




"""class User_License(db.Model):
    _tablename_ = 'user_license'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, primary_key=False)
    license_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)"""
    
"""CREATE TABLE active_sessions (
    session_id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL,  -- Assuming a users table exists
    login_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expiry_time TIMESTAMP NOT NULL,  -- e.g., login_time + session_duration
    active BOOLEAN NOT NULL DEFAULT TRUE
);
"""


