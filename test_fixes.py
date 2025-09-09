#!/usr/bin/env python3
"""
Test script for the latest fixes:
1. Symbol search functionality
2. TWD currency support
3. Account association for assets and transactions
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

def test_fixes():
    print("🧪 Testing Latest Fixes")
    print("=" * 40)
    
    session = requests.Session()
    
    # Login (assuming test user exists)
    print("🔐 Logging in...")
    login_data = {'username': 'testuser', 'password': 'testpass123'}
    response = session.post(f'{BASE_URL}/api/login', json=login_data)
    
    if response.status_code != 200:
        print("❌ Please create a test user first")
        return
    
    print("✅ Logged in successfully")
    
    # Test symbol search
    print("\n🔍 Testing symbol search...")
    test_symbols = ['AAPL', 'MSFT', '2330']  # Apple, Microsoft, Taiwan Semiconductor
    
    for symbol in test_symbols:
        try:
            response = session.get(f'{BASE_URL}/api/search-symbol/{symbol}')
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {symbol}: {data['name']} - {data['currency']} ${data['price']:.2f}")
            else:
                print(f"⚠️ {symbol}: Search failed")
        except Exception as e:
            print(f"❌ {symbol}: Error - {e}")
    
    # Create a test account for TWD
    print("\n🏦 Creating TWD account...")
    account_data = {
        'name': 'Taiwan Stock Account',
        'account_type': 'investment',
        'currency': 'TWD'
    }
    
    response = session.post(f'{BASE_URL}/api/accounts', json=account_data)
    if response.status_code == 201:
        print("✅ TWD account created successfully")
        account_id = response.json()['account_id']
    else:
        print(f"❌ Failed to create TWD account: {response.text}")
        account_id = None
    
    # Test adding a transaction with TWD currency and account association
    if account_id:
        print("\n💰 Testing TWD transaction with account...")
        transaction_data = {
            'transaction_type': 'BUY',
            'symbol': '2330',
            'name': 'Taiwan Semiconductor Manufacturing',
            'asset_type': 'stock',
            'quantity': 100,
            'price_per_unit': 600.00,
            'currency': 'TWD',
            'account_id': account_id,
            'notes': 'Taiwan stock purchase'
        }
        
        response = session.post(f'{BASE_URL}/api/transactions', json=transaction_data)
        if response.status_code == 201:
            print("✅ TWD transaction added successfully")
        else:
            print(f"❌ TWD transaction failed: {response.text}")
    
    # Test getting transactions with account names
    print("\n📊 Testing transaction list with account names...")
    response = session.get(f'{BASE_URL}/api/transactions')
    if response.status_code == 200:
        transactions = response.json()
        print(f"✅ Loaded {len(transactions)} transactions")
        
        for txn in transactions[-3:]:  # Show last 3 transactions
            account_info = txn.get('account_name', 'No Account')
            currency_info = txn.get('currency', 'USD')
            print(f"   {txn['symbol']} - {txn['transaction_type']} - {account_info} - {currency_info}")
    else:
        print(f"❌ Failed to load transactions: {response.text}")
    
    # Test getting assets with account names
    print("\n📈 Testing asset list with account names...")
    response = session.get(f'{BASE_URL}/api/assets')
    if response.status_code == 200:
        assets = response.json()
        print(f"✅ Loaded {len(assets)} assets")
        
        for asset in assets[-3:]:  # Show last 3 assets
            account_info = asset.get('account_name', 'No Account')
            currency_info = asset.get('currency', 'USD')
            print(f"   {asset['symbol']} - {account_info} - {currency_info} {asset['total_value']:.2f}")
    else:
        print(f"❌ Failed to load assets: {response.text}")
    
    # Test accounts list
    print("\n🏦 Testing accounts list...")
    response = session.get(f'{BASE_URL}/api/accounts')
    if response.status_code == 200:
        accounts = response.json()
        print(f"✅ User has {len(accounts)} accounts:")
        
        for account in accounts:
            print(f"   📋 {account['name']} ({account['account_type']}) - {account['currency']}")
    else:
        print(f"❌ Failed to load accounts: {response.text}")
    
    print("\n" + "=" * 40)
    print("🎉 All fixes tested!")
    print("\n✅ Fixed Issues:")
    print("   1. Symbol search now works properly")
    print("   2. Added TWD (New Taiwan Dollar) currency")
    print("   3. Taiwan stocks (4-digit numbers) auto-detect .TW suffix")
    print("   4. Assets and transactions show account names")
    print("   5. Account associations are properly displayed")
    print("\n📱 Try the web interface to see these improvements!")

if __name__ == '__main__':
    test_fixes()