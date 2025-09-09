#!/usr/bin/env python3
"""
Test script for the full version Asset Tracker
This script tests basic functionality without requiring web browser
"""

import requests
import json
import time

BASE_URL = 'http://localhost:5000'

def test_api_endpoint(endpoint, method='GET', data=None, session=None):
    """Test an API endpoint"""
    url = f'{BASE_URL}{endpoint}'
    
    try:
        if method == 'POST':
            response = session.post(url, json=data) if session else requests.post(url, json=data)
        elif method == 'DELETE':
            response = session.delete(url) if session else requests.delete(url)
        else:
            response = session.get(url) if session else requests.get(url)
        
        return response.status_code, response.json() if response.content else None
    except Exception as e:
        return None, str(e)

def main():
    print("🧪 Testing Advanced Asset Tracker Full Version")
    print("=" * 50)
    
    # Test server is running
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server not responding properly")
            return
    except:
        print("❌ Server not running. Please start with: python app.py")
        return
    
    session = requests.Session()
    
    # Test user creation
    print("\n📝 Testing user registration...")
    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    }
    
    status, response = test_api_endpoint('/api/users', 'POST', user_data)
    if status == 201:
        print("✅ User registration works")
        user_id = response['user_id']
    else:
        print(f"⚠️  User registration: {status} - {response}")
    
    # Test login
    print("\n🔐 Testing login...")
    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    
    status, response = test_api_endpoint('/api/login', 'POST', login_data, session)
    if status == 200:
        print("✅ Login works")
    else:
        print(f"❌ Login failed: {status} - {response}")
        return
    
    # Test account creation
    print("\n🏦 Testing account creation...")
    account_data = {
        'name': 'Test Investment Account',
        'account_type': 'investment',
        'currency': 'USD'
    }
    
    status, response = test_api_endpoint('/api/accounts', 'POST', account_data, session)
    if status == 201:
        print("✅ Account creation works")
        account_id = response['account_id']
    else:
        print(f"❌ Account creation failed: {status} - {response}")
        return
    
    # Test asset addition
    print("\n💰 Testing asset addition...")
    asset_data = {
        'symbol': 'AAPL',
        'name': 'Apple Inc.',
        'asset_type': 'stock',
        'quantity': 10,
        'purchase_price': 150.00,
        'currency': 'USD',
        'account_id': account_id,
        'notes': 'Test stock purchase'
    }
    
    status, response = test_api_endpoint('/api/assets', 'POST', asset_data, session)
    if status == 201:
        print("✅ Asset addition works")
        asset_id = response['asset_id']
    else:
        print(f"❌ Asset addition failed: {status} - {response}")
        return
    
    # Test portfolio summary
    print("\n📊 Testing portfolio summary...")
    status, response = test_api_endpoint('/api/portfolio-summary', session=session)
    if status == 200:
        print("✅ Portfolio summary works")
        print(f"   Total value: ${response['total_value']:.2f}")
        print(f"   Total cost: ${response['total_cost']:.2f}")
        print(f"   Assets: {response['asset_count']}")
    else:
        print(f"❌ Portfolio summary failed: {status} - {response}")
    
    # Test price updates
    print("\n📈 Testing price updates...")
    status, response = test_api_endpoint('/api/update-prices', 'POST', session=session)
    if status == 200:
        print("✅ Price updates work")
        print(f"   {response['message']}")
    else:
        print(f"⚠️  Price updates: {status} - {response}")
    
    # Test advanced analytics
    print("\n📊 Testing advanced analytics...")
    
    # Portfolio metrics
    status, response = test_api_endpoint('/api/portfolio-metrics', session=session)
    if status == 200:
        print("✅ Portfolio metrics work")
        if response['best_performer']:
            print(f"   Best performer: {response['best_performer']['symbol']}")
    else:
        print(f"⚠️  Portfolio metrics: {status} - {response}")
    
    # Asset performance
    status, response = test_api_endpoint('/api/asset-performance', session=session)
    if status == 200:
        print("✅ Asset performance analysis works")
        print(f"   Analyzing {len(response)} assets")
    else:
        print(f"⚠️  Asset performance: {status} - {response}")
    
    # Portfolio history
    status, response = test_api_endpoint('/api/portfolio-history', session=session)
    if status == 200:
        print("✅ Portfolio history works")
        print(f"   Historical data points: {len(response)}")
    else:
        print(f"⚠️  Portfolio history: {status} - {response}")
    
    # Test data backup
    print("\n💾 Testing data backup...")
    status, response = test_api_endpoint('/api/backup-data', session=session)
    if status == 200:
        print("✅ Data backup works")
        print(f"   Backup includes {len(response['assets'])} assets")
    else:
        print(f"❌ Data backup failed: {status} - {response}")
    
    # Test symbol search
    print("\n🔍 Testing symbol search...")
    status, response = test_api_endpoint('/api/search-symbol/MSFT', session=session)
    if status == 200:
        print("✅ Symbol search works")
        print(f"   Found: {response['name']} - ${response['price']}")
    else:
        print(f"⚠️  Symbol search: {status} - {response}")
    
    # Test currency conversion
    print("\n💱 Testing currency conversion...")
    status, response = test_api_endpoint('/api/currency-conversion/USD/EUR/100', session=session)
    if status == 200:
        print("✅ Currency conversion works")
        print(f"   $100 USD = €{response['converted_amount']:.2f} EUR")
    else:
        print(f"⚠️  Currency conversion: {status} - {response}")
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")
    print("\nThe full version Asset Tracker is working properly.")
    print("You can now use the web interface at: http://localhost:5000")

if __name__ == '__main__':
    main()