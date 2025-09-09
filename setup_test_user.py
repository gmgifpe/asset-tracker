#!/usr/bin/env python3
"""
Set up test user directly in database
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import os

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/asset_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

def setup_test_user():
    with app.app_context():
        print("🔐 Setting up test user...")
        
        # Check if user already exists
        existing_user = User.query.filter_by(username='testuser').first()
        if existing_user:
            print("ℹ️ Test user already exists - that's fine!")
            return True
        
        # Create test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('testpass123')
        )
        
        try:
            db.session.add(test_user)
            db.session.commit()
            print("✅ Test user created successfully")
            print("   Username: testuser")
            print("   Password: testpass123")
            return True
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            return False

if __name__ == '__main__':
    setup_test_user()