from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os

db = SQLAlchemy() 

def init_db(app: Flask):
    # Get connection string from environment variable
    connection_string = os.getenv(
        'DATABASE_URL',
        'postgresql://neondb_owner:npg_PYcbU2ZwmeO3@ep-square-forest-ah7u6qx7-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
    )

    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    return db
