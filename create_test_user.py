#!/usr/bin/env python3
"""
Create a test user for the equity compensation testing
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

def create_test_user():
    print("🔐 Creating test user...")
    
    # Create test user
    user_data = {
        'username': 'testuser',
        'password': 'testpass123',
        'email': 'test@example.com'
    }
    
    try:
        response = requests.post(f'{BASE_URL}/api/register', json=user_data)
        
        if response.status_code == 201:
            print("✅ Test user created successfully")
            print(f"   Username: {user_data['username']}")
            print(f"   Password: {user_data['password']}")
        elif response.status_code == 400 and 'already exists' in response.text:
            print("ℹ️ Test user already exists - that's fine!")
        else:
            print(f"❌ Failed to create test user: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to server: {e}")
        return False
    
    return True

if __name__ == '__main__':
    create_test_user()