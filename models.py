from database import db
from datetime import datetime

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
    license_key = db.Column(db.String(120), nullable=True)
    concurrent_session_count = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

class License(db.Model):
    _tablename_ = 'licenses'

    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(120), unique=True, nullable=False)
    concurrent_session_count = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate = datetime.utcnow)




class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
