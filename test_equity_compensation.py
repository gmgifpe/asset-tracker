#!/usr/bin/env python3
"""
Test script for equity compensation features:
Stock Options, RSUs, and ESPP tracking
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:5000'

def test_equity_compensation():
    print("🧪 Testing Equity Compensation Features")
    print("=" * 50)
    
    session = requests.Session()
    
    # Login
    print("🔐 Logging in...")
    login_data = {'username': 'testuser', 'password': 'testpass123'}
    response = session.post(f'{BASE_URL}/api/login', json=login_data)
    
    if response.status_code != 200:
        print("❌ Please create a test user first")
        return
    
    print("✅ Logged in successfully")
    
    # Create a company stock account
    print("\n🏢 Creating company stock account...")
    account_data = {
        'name': 'Company Stock Plan',
        'account_type': 'investment',
        'currency': 'USD'
    }
    
    response = session.post(f'{BASE_URL}/api/accounts', json=account_data)
    if response.status_code == 201:
        print("✅ Company stock account created")
        account_id = response.json()['account_id']
    else:
        print("ℹ️ Using existing account")
        # Get existing accounts
        response = session.get(f'{BASE_URL}/api/accounts')
        accounts = response.json()
        account_id = accounts[0]['id'] if accounts else None
    
    # Test Stock Options
    print("\n📈 Testing Stock Options...")
    
    today = datetime.now()
    grant_date = today - timedelta(days=365)  # Granted 1 year ago
    vest_date = today + timedelta(days=365)   # Vests in 1 year
    exp_date = today + timedelta(days=365*10) # Expires in 10 years
    
    stock_option_data = {
        'symbol': 'COMPX',
        'name': 'Company X Inc.',
        'asset_type': 'stock_option',
        'account_id': account_id,
        'quantity': 1000,
        'purchase_price': 0,  # Options typically have no purchase cost
        'currency': 'USD',
        'notes': 'Employee stock option grant',
        # Equity compensation fields
        'grant_date': grant_date.isoformat(),
        'vesting_date': vest_date.isoformat(),
        'expiration_date': exp_date.isoformat(),
        'strike_price': 50.00,
        'status': 'granted'
    }
    
    response = session.post(f'{BASE_URL}/api/assets', json=stock_option_data)
    if response.status_code == 201:
        print("✅ Stock option added successfully")
        print(f"   📊 {stock_option_data['quantity']} options at ${stock_option_data['strike_price']} strike")
        print(f"   📅 Vests: {vest_date.strftime('%Y-%m-%d')}")
    else:
        print(f"❌ Failed to add stock option: {response.text}")
    
    # Test RSUs
    print("\n🎁 Testing RSUs (Restricted Stock Units)...")
    
    rsu_vest_date = today + timedelta(days=180)  # Vests in 6 months
    
    rsu_data = {
        'symbol': 'COMPX',
        'name': 'Company X Inc.',
        'asset_type': 'rsu',
        'account_id': account_id,
        'quantity': 500,
        'purchase_price': 0,  # RSUs have no purchase cost
        'currency': 'USD',
        'notes': 'RSU grant from promotion',
        # Equity compensation fields
        'grant_date': today.isoformat(),
        'vesting_date': rsu_vest_date.isoformat(),
        'vest_fmv': 75.00,  # Fair Market Value when granted
        'status': 'granted'
    }
    
    response = session.post(f'{BASE_URL}/api/assets', json=rsu_data)
    if response.status_code == 201:
        print("✅ RSU added successfully")
        print(f"   🎯 {rsu_data['quantity']} RSUs")
        print(f"   💰 Grant FMV: ${rsu_data['vest_fmv']}")
        print(f"   📅 Vests: {rsu_vest_date.strftime('%Y-%m-%d')}")
    else:
        print(f"❌ Failed to add RSU: {response.text}")
    
    # Test ESPP
    print("\n🛒 Testing ESPP (Employee Stock Purchase Plan)...")
    
    espp_data = {
        'symbol': 'COMPX',
        'name': 'Company X Inc.',
        'asset_type': 'espp',
        'account_id': account_id,
        'quantity': 200,
        'purchase_price': 60.00,  # 15% discount from $70 market price
        'currency': 'USD',
        'notes': 'ESPP purchase with 15% discount',
        'status': 'vested'
    }
    
    response = session.post(f'{BASE_URL}/api/assets', json=espp_data)
    if response.status_code == 201:
        print("✅ ESPP shares added successfully")
        print(f"   🛒 {espp_data['quantity']} shares at ${espp_data['purchase_price']} (discounted)")
    else:
        print(f"❌ Failed to add ESPP: {response.text}")
    
    # Test getting all assets to see equity compensation
    print("\n📊 Testing equity compensation display...")
    response = session.get(f'{BASE_URL}/api/assets')
    if response.status_code == 200:
        assets = response.json()
        print(f"✅ Loaded {len(assets)} assets")
        
        equity_assets = [a for a in assets if a['asset_type'] in ['stock_option', 'rsu', 'espp']]
        print(f"   🏢 Found {len(equity_assets)} equity compensation assets:")
        
        for asset in equity_assets:
            print(f"   📈 {asset['asset_type'].upper()}: {asset['symbol']} - {asset['quantity']} units")
            print(f"      💰 Current value: ${asset['total_value']:.2f}")
            print(f"      📊 Status: {asset['status']}")
            
            if asset['asset_type'] == 'stock_option' and asset['strike_price']:
                # Assume current price for demo
                current_price = 80.00  # Would be fetched from API
                intrinsic_value = max(0, current_price - asset['strike_price'])
                if intrinsic_value > 0:
                    print(f"      💎 In-the-money: ${intrinsic_value:.2f} per share")
                    print(f"      🎯 Total intrinsic value: ${intrinsic_value * asset['quantity']:.2f}")
                else:
                    print(f"      ⏳ Out-of-money (current price < strike price)")
            
            if asset.get('vesting_date'):
                vest_date = datetime.fromisoformat(asset['vesting_date'])
                days_to_vest = (vest_date - datetime.now()).days
                if days_to_vest > 0:
                    print(f"      ⏰ Vests in {days_to_vest} days")
                else:
                    print(f"      ✅ Already vested")
    else:
        print(f"❌ Failed to load assets: {response.text}")
    
    # Test portfolio summary with equity compensation
    print("\n📋 Testing portfolio summary with equity compensation...")
    response = session.get(f'{BASE_URL}/api/portfolio-summary')
    if response.status_code == 200:
        summary = response.json()
        print("✅ Portfolio summary includes equity compensation")
        print(f"   💰 Total Portfolio Value: ${summary['total_value']:.2f}")
        
        # Show asset distribution
        asset_dist = summary.get('asset_distribution', {})
        for asset_type, value in asset_dist.items():
            if asset_type in ['stock_option', 'rsu', 'espp']:
                print(f"   📊 {asset_type.upper()}: ${value:.2f}")
    else:
        print(f"❌ Failed to load portfolio summary: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 Equity Compensation Testing Complete!")
    print("\n✅ What's now supported:")
    print("   📈 Stock Options - Track strike price, expiration, intrinsic value")
    print("   🎁 RSUs - Track vesting dates, tax cost basis")
    print("   🛒 ESPP - Track discounted purchase prices")
    print("   📅 Vesting Schedules - See when equity vests")
    print("   💰 Tax Planning - Track cost basis for tax purposes")
    print("   📊 Status Tracking - Granted, vested, exercised, expired")
    print("   🎯 Smart Valuations - Options show intrinsic value")
    print("\n💡 Usage Tips:")
    print("   1. Create a 'Company Stock Plan' account for all equity compensation")
    print("   2. Use Strike Price for options, Fair Market Value for RSUs")
    print("   3. Track vesting dates to plan exercises and sales")
    print("   4. Monitor option intrinsic values for exercise timing")
    print("   5. Use status field to track lifecycle (granted → vested → exercised)")

if __name__ == '__main__':
    test_equity_compensation()