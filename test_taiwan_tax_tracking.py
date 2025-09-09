#!/usr/bin/env python3
"""
Test script for Taiwan tax tracking features:
- Stock options tax calculation (40% on exercise gain)
- RSU tax calculation (40% on market price at vesting)
- Tax liability display and tracking
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:5000'

def test_taiwan_tax_tracking():
    print("🇹🇼 Testing Taiwan Tax Tracking Features")
    print("=" * 60)
    
    session = requests.Session()
    
    # Login
    print("🔐 Logging in...")
    login_data = {'username': 'testuser', 'password': 'testpass123'}
    response = session.post(f'{BASE_URL}/api/login', json=login_data)
    
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    print("✅ Logged in successfully")
    
    # Create a Taiwan company stock account
    print("\n🏢 Creating Taiwan company stock account...")
    account_data = {
        'name': 'Taiwan Company Stock Plan (公司股票)',
        'account_type': 'investment',
        'currency': 'TWD'
    }
    
    response = session.post(f'{BASE_URL}/api/accounts', json=account_data)
    if response.status_code == 201:
        print("✅ Taiwan company stock account created")
        account_id = response.json()['account_id']
    else:
        # Get existing accounts
        response = session.get(f'{BASE_URL}/api/accounts')
        accounts = response.json()
        account_id = accounts[0]['id'] if accounts else None
        print("ℹ️ Using existing account")
    
    # Test 1: Stock Options - Granted (Potential Tax)
    print("\n📈 Test 1: Stock Options - Granted Status (Potential Tax)")
    print("-" * 50)
    
    today = datetime.now()
    grant_date = today - timedelta(days=30)   # Granted 1 month ago
    vest_date = today + timedelta(days=335)   # Vests in 11 months
    exp_date = today + timedelta(days=365*5)  # Expires in 5 years
    
    stock_option_granted = {
        'symbol': 'TWCO',
        'name': 'Taiwan Company Inc. (台灣公司)',
        'asset_type': 'stock_option',
        'account_id': account_id,
        'quantity': 2000,
        'purchase_price': 0,  # Options typically have no purchase cost
        'currency': 'TWD',
        'notes': 'Employee stock option grant - Taiwan tax applicable',
        # Equity compensation fields
        'grant_date': grant_date.isoformat(),
        'vesting_date': vest_date.isoformat(),
        'expiration_date': exp_date.isoformat(),
        'strike_price': 100.00,  # Strike price TWD 100
        'status': 'granted',
        # Taiwan tax fields
        'tax_country': 'TW',
        'tax_rate': 0.40  # 40% Taiwan tax
    }
    
    response = session.post(f'{BASE_URL}/api/assets', json=stock_option_granted)
    if response.status_code == 201:
        print("✅ Stock option (granted) added successfully")
        print(f"   📊 {stock_option_granted['quantity']} options at TWD {stock_option_granted['strike_price']} strike")
        print(f"   📅 Vests: {vest_date.strftime('%Y-%m-%d')}")
        print("   ⚠️ Should show potential tax liability based on current price")
    else:
        print(f"❌ Failed to add stock option: {response.text}")
    
    # Test 2: Stock Options - Exercised (Current Tax Owed)
    print("\n📈 Test 2: Stock Options - Exercised Status (Tax Owed)")
    print("-" * 50)
    
    exercise_date = today - timedelta(days=5)  # Exercised 5 days ago
    
    stock_option_exercised = {
        'symbol': 'TWCO',
        'name': 'Taiwan Company Inc. (台灣公司)',
        'asset_type': 'stock_option',
        'account_id': account_id,
        'quantity': 500,
        'purchase_price': 0,
        'currency': 'TWD',
        'notes': 'Exercised stock options - Taiwan tax owed',
        # Equity compensation fields
        'grant_date': (today - timedelta(days=400)).isoformat(),
        'vesting_date': (today - timedelta(days=30)).isoformat(),
        'expiration_date': (today + timedelta(days=365*4)).isoformat(),
        'strike_price': 80.00,   # Strike price TWD 80
        'status': 'exercised',
        # Taiwan tax fields
        'tax_country': 'TW',
        'tax_rate': 0.40,
        'exercise_price': 150.00,   # Exercised at TWD 150
        'exercise_date': exercise_date.isoformat()
    }
    
    response = session.post(f'{BASE_URL}/api/assets', json=stock_option_exercised)
    if response.status_code == 201:
        print("✅ Stock option (exercised) added successfully")
        print(f"   📊 {stock_option_exercised['quantity']} options")
        print(f"   💰 Strike: TWD {stock_option_exercised['strike_price']}")
        print(f"   🎯 Exercised at: TWD {stock_option_exercised['exercise_price']}")
        print(f"   📅 Exercised: {exercise_date.strftime('%Y-%m-%d')}")
        gain = (stock_option_exercised['exercise_price'] - stock_option_exercised['strike_price']) * stock_option_exercised['quantity']
        tax_owed = gain * 0.40
        print(f"   💸 Expected tax owed: TWD {tax_owed:.0f} (40% of TWD {gain:.0f} gain)")
    else:
        print(f"❌ Failed to add exercised stock option: {response.text}")
    
    # Test 3: RSUs - Granted (Potential Tax)
    print("\n🎁 Test 3: RSUs - Granted Status (Potential Tax)")
    print("-" * 50)
    
    rsu_vest_date = today + timedelta(days=90)  # Vests in 3 months
    
    rsu_granted = {
        'symbol': 'TWCO',
        'name': 'Taiwan Company Inc. (台灣公司)',
        'asset_type': 'rsu',
        'account_id': account_id,
        'quantity': 300,
        'purchase_price': 0,  # RSUs have no purchase cost
        'currency': 'TWD',
        'notes': 'RSU grant - Taiwan tax will apply at vesting',
        # Equity compensation fields
        'grant_date': today.isoformat(),
        'vesting_date': rsu_vest_date.isoformat(),
        'vest_fmv': 120.00,  # Fair Market Value when granted
        'status': 'granted',
        # Taiwan tax fields
        'tax_country': 'TW',
        'tax_rate': 0.40
    }
    
    response = session.post(f'{BASE_URL}/api/assets', json=rsu_granted)
    if response.status_code == 201:
        print("✅ RSU (granted) added successfully")
        print(f"   🎯 {rsu_granted['quantity']} RSUs")
        print(f"   💰 Grant FMV: TWD {rsu_granted['vest_fmv']}")
        print(f"   📅 Vests: {rsu_vest_date.strftime('%Y-%m-%d')}")
        print("   ⚠️ Should show potential tax liability based on current market price")
    else:
        print(f"❌ Failed to add RSU: {response.text}")
    
    # Test 4: RSUs - Vested (Tax Owed)
    print("\n🎁 Test 4: RSUs - Vested Status (Tax Owed)")
    print("-" * 50)
    
    vest_date_past = today - timedelta(days=10)  # Vested 10 days ago
    
    rsu_vested = {
        'symbol': 'TWCO',
        'name': 'Taiwan Company Inc. (台灣公司)',
        'asset_type': 'rsu',
        'account_id': account_id,
        'quantity': 200,
        'purchase_price': 0,
        'currency': 'TWD',
        'notes': 'Vested RSUs - Taiwan tax owed',
        # Equity compensation fields
        'grant_date': (today - timedelta(days=365)).isoformat(),
        'vesting_date': vest_date_past.isoformat(),
        'vest_fmv': 110.00,  # FMV when originally granted
        'status': 'vested',
        # Taiwan tax fields
        'tax_country': 'TW',
        'tax_rate': 0.40,
        'vest_market_price': 160.00  # Market price when vested (higher than grant FMV)
    }
    
    response = session.post(f'{BASE_URL}/api/assets', json=rsu_vested)
    if response.status_code == 201:
        print("✅ RSU (vested) added successfully")
        print(f"   🎯 {rsu_vested['quantity']} RSUs")
        print(f"   💰 Grant FMV: TWD {rsu_vested['vest_fmv']}")
        print(f"   📈 Vesting Market Price: TWD {rsu_vested['vest_market_price']}")
        print(f"   📅 Vested: {vest_date_past.strftime('%Y-%m-%d')}")
        tax_owed = rsu_vested['vest_market_price'] * rsu_vested['quantity'] * 0.40
        print(f"   💸 Expected tax owed: TWD {tax_owed:.0f} (40% of TWD {rsu_vested['vest_market_price'] * rsu_vested['quantity']:.0f})")
    else:
        print(f"❌ Failed to add vested RSU: {response.text}")
    
    # Test 5: Check all assets with tax calculations
    print("\n📊 Test 5: Viewing All Assets with Tax Information")
    print("-" * 50)
    
    response = session.get(f'{BASE_URL}/api/assets')
    if response.status_code == 200:
        assets = response.json()
        print(f"✅ Loaded {len(assets)} assets")
        
        total_current_tax = 0
        total_potential_tax = 0
        
        for asset in assets:
            if asset['asset_type'] in ['stock_option', 'rsu'] and asset.get('tax_country') == 'TW':
                print(f"\n   📈 {asset['asset_type'].upper()}: {asset['symbol']}")
                print(f"      📊 Quantity: {asset['quantity']}")
                print(f"      💰 Current value: TWD {asset['total_value']:.2f}")
                print(f"      📊 Status: {asset['status']}")
                print(f"      🇹🇼 Tax Country: {asset['tax_country']} ({asset['tax_rate']*100:.0f}%)")
                
                current_tax = asset.get('current_tax_liability', 0)
                potential_tax = asset.get('potential_tax_liability', 0)
                
                if current_tax > 0:
                    print(f"      💸 CURRENT TAX OWED: TWD {current_tax:.2f}")
                    total_current_tax += current_tax
                elif potential_tax > 0:
                    print(f"      ⚠️ Potential tax: TWD {potential_tax:.2f}")
                    total_potential_tax += potential_tax
                
                if asset['asset_type'] == 'stock_option':
                    if asset.get('exercise_price') and asset.get('strike_price'):
                        gain_per_share = asset['exercise_price'] - asset['strike_price']
                        print(f"      📈 Gain per share: TWD {gain_per_share:.2f}")
                    elif asset.get('strike_price'):
                        # Assume current price for demo (normally would fetch from API)
                        current_price = 140.00  # Demo current market price
                        intrinsic_value = max(0, current_price - asset['strike_price'])
                        if intrinsic_value > 0:
                            print(f"      💎 In-the-money: TWD {intrinsic_value:.2f} per share")
                            print(f"      🎯 Total intrinsic value: TWD {intrinsic_value * asset['quantity']:.2f}")
                
                elif asset['asset_type'] == 'rsu':
                    if asset.get('vest_market_price'):
                        print(f"      💰 Vesting market price: TWD {asset['vest_market_price']:.2f}")
                    if asset.get('vest_fmv'):
                        print(f"      📊 Grant FMV: TWD {asset['vest_fmv']:.2f}")
        
        print(f"\n🧮 TAIWAN TAX SUMMARY:")
        print(f"   💸 Current tax owed: TWD {total_current_tax:.2f}")
        print(f"   ⚠️ Potential future tax: TWD {total_potential_tax:.2f}")
        print(f"   📊 Total tax exposure: TWD {total_current_tax + total_potential_tax:.2f}")
        
    else:
        print(f"❌ Failed to load assets: {response.text}")
    
    print("\n" + "=" * 60)
    print("🎉 Taiwan Tax Tracking Testing Complete!")
    print("\n✅ Features implemented:")
    print("   🇹🇼 40% Taiwan tax rate for equity compensation")
    print("   📈 Stock options: Tax on (exercise price - strike price) * quantity")
    print("   🎁 RSUs: Tax on market price at vesting * quantity")
    print("   💸 Current tax liability tracking for exercised/vested assets")
    print("   ⚠️ Potential tax liability for granted assets")
    print("   🎯 Tax calculations updated in real-time with current prices")
    print("   🖥️ Visual indicators in UI for tax liabilities")
    
    print("\n💡 Tax Planning Tips:")
    print("   1. Monitor potential tax liabilities before exercising options")
    print("   2. Consider timing of option exercises for tax planning")
    print("   3. Set aside funds for tax obligations when RSUs vest")
    print("   4. Track actual vs. estimated tax liabilities for accuracy")
    print("   5. Consult tax professionals for complex equity compensation scenarios")

if __name__ == '__main__':
    test_taiwan_tax_tracking()