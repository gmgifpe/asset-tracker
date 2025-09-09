#!/usr/bin/env python3
"""
Test script for new features: Transaction tracking and Dark mode
This script tests the buy/sell transaction functionality
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:5000'

def test_transaction_features():
    print("🧪 Testing New Features: Transactions & Dark Mode")
    print("=" * 60)
    
    session = requests.Session()
    
    # Login (assuming test user exists from previous tests)
    print("🔐 Logging in...")
    login_data = {'username': 'testuser', 'password': 'testpass123'}
    response = session.post(f'{BASE_URL}/api/login', json=login_data)
    
    if response.status_code != 200:
        print("❌ Please run the basic tests first to create a test user")
        return
    
    print("✅ Logged in successfully")
    
    # Test BUY transaction
    print("\n💰 Testing BUY transaction...")
    buy_transaction = {
        'transaction_type': 'BUY',
        'symbol': 'AAPL',
        'name': 'Apple Inc.',
        'asset_type': 'stock',
        'quantity': 10,
        'price_per_unit': 150.00,
        'transaction_date': datetime.now().isoformat(),
        'currency': 'USD',
        'notes': 'Initial purchase'
    }
    
    response = session.post(f'{BASE_URL}/api/transactions', json=buy_transaction)
    if response.status_code == 201:
        print("✅ BUY transaction added successfully")
        buy_txn_id = response.json()['transaction_id']
    else:
        print(f"❌ BUY transaction failed: {response.text}")
        return
    
    # Test another BUY transaction (same stock, different price)
    print("\n💰 Testing second BUY transaction (same stock)...")
    buy2_transaction = {
        'transaction_type': 'BUY',
        'symbol': 'AAPL',
        'name': 'Apple Inc.',
        'asset_type': 'stock',
        'quantity': 5,
        'price_per_unit': 160.00,
        'transaction_date': (datetime.now() + timedelta(days=1)).isoformat(),
        'currency': 'USD',
        'notes': 'Additional purchase'
    }
    
    response = session.post(f'{BASE_URL}/api/transactions', json=buy2_transaction)
    if response.status_code == 201:
        print("✅ Second BUY transaction added successfully")
    else:
        print(f"❌ Second BUY transaction failed: {response.text}")
        return
    
    # Test SELL transaction
    print("\n💸 Testing SELL transaction...")
    sell_transaction = {
        'transaction_type': 'SELL',
        'symbol': 'AAPL',
        'name': 'Apple Inc.',
        'asset_type': 'stock',
        'quantity': 7,
        'price_per_unit': 170.00,
        'transaction_date': (datetime.now() + timedelta(days=2)).isoformat(),
        'currency': 'USD',
        'notes': 'Partial sale'
    }
    
    response = session.post(f'{BASE_URL}/api/transactions', json=sell_transaction)
    if response.status_code == 201:
        print("✅ SELL transaction added successfully")
    else:
        print(f"❌ SELL transaction failed: {response.text}")
        return
    
    # Test invalid SELL (more than holdings)
    print("\n⚠️ Testing invalid SELL transaction (insufficient holdings)...")
    invalid_sell = {
        'transaction_type': 'SELL',
        'symbol': 'AAPL',
        'name': 'Apple Inc.',
        'asset_type': 'stock',
        'quantity': 20,  # More than current holdings
        'price_per_unit': 170.00,
        'transaction_date': datetime.now().isoformat(),
        'currency': 'USD'
    }
    
    response = session.post(f'{BASE_URL}/api/transactions', json=invalid_sell)
    if response.status_code == 400:
        print("✅ Invalid SELL transaction correctly rejected")
        print(f"   Error: {response.json().get('error', 'Unknown error')}")
    else:
        print(f"❌ Invalid SELL should have been rejected: {response.text}")
    
    # Test transaction history
    print("\n📊 Testing transaction history...")
    response = session.get(f'{BASE_URL}/api/transactions')
    if response.status_code == 200:
        transactions = response.json()
        print(f"✅ Transaction history loaded: {len(transactions)} transactions")
        
        # Show transaction summary
        buy_count = sum(1 for t in transactions if t['transaction_type'] == 'BUY')
        sell_count = sum(1 for t in transactions if t['transaction_type'] == 'SELL')
        print(f"   📈 BUY transactions: {buy_count}")
        print(f"   📉 SELL transactions: {sell_count}")
    else:
        print(f"❌ Failed to load transaction history: {response.text}")
    
    # Test holdings calculation
    print("\n🏦 Testing current holdings...")
    response = session.get(f'{BASE_URL}/api/holdings')
    if response.status_code == 200:
        holdings = response.json()
        print(f"✅ Holdings calculated successfully")
        
        if 'AAPL' in holdings:
            aapl_holding = holdings['AAPL']
            print(f"   AAPL Holdings: {aapl_holding['quantity']} shares")
            print(f"   Average Cost: ${aapl_holding['average_cost']:.2f}")
            print(f"   Current Value: ${aapl_holding.get('current_value', 0):.2f}")
            print(f"   Unrealized P&L: ${aapl_holding.get('unrealized_gain_loss', 0):.2f}")
        else:
            print("   No AAPL holdings found")
    else:
        print(f"❌ Failed to load holdings: {response.text}")
    
    # Test realized gains
    print("\n💰 Testing realized gains calculation...")
    response = session.get(f'{BASE_URL}/api/realized-gains')
    if response.status_code == 200:
        realized_gains = response.json()
        print(f"✅ Realized gains calculated: {len(realized_gains)} sell transactions")
        
        total_realized = sum(gain['realized_gain_loss'] for gain in realized_gains)
        print(f"   Total Realized Gains: ${total_realized:.2f}")
        
        for gain in realized_gains:
            print(f"   {gain['symbol']}: ${gain['realized_gain_loss']:.2f} ({gain['realized_gain_loss_percent']:.1f}%)")
    else:
        print(f"❌ Failed to load realized gains: {response.text}")
    
    # Test transaction summary for specific symbol
    print("\n📋 Testing transaction summary for AAPL...")
    response = session.get(f'{BASE_URL}/api/transaction-summary/AAPL')
    if response.status_code == 200:
        summary = response.json()
        print(f"✅ Transaction summary loaded for {summary['symbol']}")
        print(f"   Current Holdings: {summary['current_holdings']}")
        print(f"   Total Buy Quantity: {summary['total_buy_quantity']}")
        print(f"   Total Sell Quantity: {summary['total_sell_quantity']}")
        print(f"   Average Cost Basis: ${summary['average_cost_basis']:.2f}")
        print(f"   Realized Gains: ${summary['realized_gain_loss']:.2f}")
        print(f"   Transaction Count: {summary['transaction_count']}")
    else:
        print(f"❌ Failed to load transaction summary: {response.text}")
    
    print("\n" + "=" * 60)
    print("🎉 Transaction tracking tests completed!")
    print("\n📝 What you can now do:")
    print("   1. Go to Transactions tab in the web interface")
    print("   2. Add BUY transactions for stocks you purchase")
    print("   3. Add SELL transactions when you sell")
    print("   4. View realized gains/losses automatically calculated")
    print("   5. See current holdings with average cost basis")
    print("   6. Click 'History' button for detailed transaction history")
    print("   7. Use 'Quick Sell' button for fast selling")
    print("   8. Toggle dark mode with the 🌓 button")
    print("   9. Dark mode preference is saved automatically")

if __name__ == '__main__':
    test_transaction_features()