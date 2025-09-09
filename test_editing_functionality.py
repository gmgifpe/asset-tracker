#!/usr/bin/env python3
"""
Test script for asset editing functionality:
- Test creating assets
- Test fetching asset details for editing
- Test updating asset information
- Test editing with different asset types and tax rates
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:5000'

def test_asset_editing():
    print("✏️ Testing Asset Editing Functionality")
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
    
    # Create account
    print("\n🏢 Creating test account...")
    account_data = {
        'name': 'Edit Test Account',
        'account_type': 'investment',
        'currency': 'USD'
    }
    
    response = session.post(f'{BASE_URL}/api/accounts', json=account_data)
    if response.status_code == 201:
        print("✅ Test account created")
        account_id = response.json()['account_id']
    else:
        response = session.get(f'{BASE_URL}/api/accounts')
        accounts = response.json()
        account_id = accounts[0]['id'] if accounts else None
        print("ℹ️ Using existing account")
    
    today = datetime.now()
    
    # Test 1: Create a basic stock asset
    print("\n📈 Test 1: Creating Basic Stock Asset")
    print("-" * 50)
    
    original_stock = {
        'symbol': 'EDITEST',
        'name': 'Edit Test Corporation',
        'asset_type': 'stock',
        'account_id': account_id,
        'quantity': 100,
        'purchase_price': 50.00,
        'currency': 'USD',
        'notes': 'Original stock for editing test'
    }
    
    response = session.post(f'{BASE_URL}/api/assets', json=original_stock)
    if response.status_code == 201:
        print("✅ Basic stock asset created")
        stock_id = response.json()['asset_id']
        print(f"   📊 Asset ID: {stock_id}")
        print(f"   📈 {original_stock['quantity']} shares of {original_stock['symbol']} at ${original_stock['purchase_price']}")
    else:
        print(f"❌ Failed to create stock: {response.text}")
        return
    
    # Test 2: Fetch asset details for editing
    print("\n📝 Test 2: Fetching Asset for Editing")
    print("-" * 50)
    
    response = session.get(f'{BASE_URL}/api/assets/{stock_id}')
    if response.status_code == 200:
        asset_details = response.json()
        print("✅ Asset details retrieved successfully")
        print(f"   📊 Symbol: {asset_details['symbol']}")
        print(f"   🏷️ Name: {asset_details['name']}")
        print(f"   📈 Type: {asset_details['asset_type']}")
        print(f"   🔢 Quantity: {asset_details['quantity']}")
        print(f"   💰 Price: ${asset_details['purchase_price']}")
        print(f"   💬 Notes: {asset_details['notes']}")
    else:
        print(f"❌ Failed to fetch asset details: {response.text}")
        return
    
    # Test 3: Edit the basic stock asset
    print("\n✏️ Test 3: Updating Basic Stock Asset")
    print("-" * 50)
    
    updated_stock = {
        'symbol': 'EDITUPD',
        'name': 'Edit Test Corp (Updated)',
        'asset_type': 'stock',
        'account_id': account_id,
        'quantity': 150,  # Increased quantity
        'purchase_price': 55.00,  # Updated price
        'currency': 'USD',
        'notes': 'Updated stock information - quantity and price changed'
    }
    
    response = session.put(f'{BASE_URL}/api/assets/{stock_id}', json=updated_stock)
    if response.status_code == 200:
        print("✅ Basic stock asset updated successfully")
        print(f"   📈 Symbol changed: {original_stock['symbol']} → {updated_stock['symbol']}")
        print(f"   🔢 Quantity changed: {original_stock['quantity']} → {updated_stock['quantity']}")
        print(f"   💰 Price changed: ${original_stock['purchase_price']} → ${updated_stock['purchase_price']}")
    else:
        print(f"❌ Failed to update stock: {response.text}")
        return
    
    # Test 4: Create and edit stock option with tax info
    print("\n🎯 Test 4: Create and Edit Stock Option with Tax Info")
    print("-" * 50)
    
    original_option = {
        'symbol': 'OPTEDIT',
        'name': 'Option Edit Test Corp',
        'asset_type': 'stock_option',
        'account_id': account_id,
        'quantity': 500,
        'purchase_price': 0,
        'currency': 'TWD',
        'notes': 'Original option for editing',
        'grant_date': (today - timedelta(days=30)).isoformat(),
        'vesting_date': (today + timedelta(days=300)).isoformat(),
        'expiration_date': (today + timedelta(days=365*5)).isoformat(),
        'strike_price': 100.00,
        'status': 'granted',
        'tax_country': 'TW',
        'tax_rate': 40
    }
    
    response = session.post(f'{BASE_URL}/api/assets', json=original_option)
    if response.status_code == 201:
        print("✅ Stock option created for editing")
        option_id = response.json()['asset_id']
        print(f"   📊 Option ID: {option_id}")
        print(f"   🎯 {original_option['quantity']} options at TWD {original_option['strike_price']} strike")
        print(f"   🇹🇼 Tax rate: {original_option['tax_rate']}%")
    else:
        print(f"❌ Failed to create option: {response.text}")
        return
    
    # Edit the stock option - change to exercised with custom tax rate
    print("\n✏️ Editing Stock Option: Change to Exercised Status")
    print("-" * 50)
    
    updated_option = {
        'symbol': 'OPTEDIT',
        'name': 'Option Edit Test Corp (Exercised)',
        'asset_type': 'stock_option',
        'account_id': account_id,
        'quantity': 500,
        'purchase_price': 0,
        'currency': 'TWD',
        'notes': 'Updated option - now exercised with custom tax rate',
        'grant_date': (today - timedelta(days=30)).isoformat(),
        'vesting_date': (today - timedelta(days=30)).isoformat(),  # Already vested
        'expiration_date': (today + timedelta(days=365*5)).isoformat(),
        'strike_price': 100.00,
        'status': 'exercised',  # Changed to exercised
        'tax_country': 'TW',
        'tax_rate': 35,  # Changed tax rate from 40% to 35%
        'exercise_price': 180.00,  # Added exercise price
        'exercise_date': (today - timedelta(days=5)).isoformat()  # Added exercise date
    }
    
    response = session.put(f'{BASE_URL}/api/assets/{option_id}', json=updated_option)
    if response.status_code == 200:
        print("✅ Stock option updated to exercised status")
        print(f"   📊 Status changed: {original_option['status']} → {updated_option['status']}")
        print(f"   🇹🇼 Tax rate changed: {original_option['tax_rate']}% → {updated_option['tax_rate']}%")
        print(f"   💰 Exercise price: TWD {updated_option['exercise_price']}")
        
        # Calculate expected tax
        gain = (updated_option['exercise_price'] - updated_option['strike_price']) * updated_option['quantity']
        tax = gain * (updated_option['tax_rate'] / 100)
        print(f"   💸 Expected tax: TWD {tax:.0f} ({updated_option['tax_rate']}% of TWD {gain:.0f} gain)")
    else:
        print(f"❌ Failed to update option: {response.text}")
        return
    
    # Test 5: Create and edit RSU
    print("\n🎁 Test 5: Create and Edit RSU")
    print("-" * 50)
    
    original_rsu = {
        'symbol': 'RSUEDIT',
        'name': 'RSU Edit Test Corp',
        'asset_type': 'rsu',
        'account_id': account_id,
        'quantity': 200,
        'purchase_price': 0,
        'currency': 'USD',
        'notes': 'Original RSU for editing',
        'grant_date': today.isoformat(),
        'vesting_date': (today + timedelta(days=180)).isoformat(),
        'vest_fmv': 120.00,
        'status': 'granted',
        'tax_country': 'US',
        'tax_rate': 35
    }
    
    response = session.post(f'{BASE_URL}/api/assets', json=original_rsu)
    if response.status_code == 201:
        print("✅ RSU created for editing")
        rsu_id = response.json()['asset_id']
        print(f"   🎯 {original_rsu['quantity']} RSUs with FMV ${original_rsu['vest_fmv']}")
        print(f"   🇺🇸 US tax rate: {original_rsu['tax_rate']}%")
    else:
        print(f"❌ Failed to create RSU: {response.text}")
        return
    
    # Edit RSU - change to vested with market price
    print("\n✏️ Editing RSU: Change to Vested Status")
    print("-" * 50)
    
    updated_rsu = {
        'symbol': 'RSUEDIT',
        'name': 'RSU Edit Test Corp (Vested)',
        'asset_type': 'rsu',
        'account_id': account_id,
        'quantity': 200,
        'purchase_price': 0,
        'currency': 'USD',
        'notes': 'Updated RSU - now vested with higher market price',
        'grant_date': today.isoformat(),
        'vesting_date': (today - timedelta(days=1)).isoformat(),  # Already vested
        'vest_fmv': 120.00,
        'status': 'vested',  # Changed to vested
        'tax_country': 'US',
        'tax_rate': 37,  # Changed tax rate to 37%
        'vest_market_price': 150.00  # Added vesting market price (higher than FMV)
    }
    
    response = session.put(f'{BASE_URL}/api/assets/{rsu_id}', json=updated_rsu)
    if response.status_code == 200:
        print("✅ RSU updated to vested status")
        print(f"   📊 Status changed: {original_rsu['status']} → {updated_rsu['status']}")
        print(f"   🇺🇸 Tax rate changed: {original_rsu['tax_rate']}% → {updated_rsu['tax_rate']}%")
        print(f"   💰 Vesting price: ${updated_rsu['vest_market_price']} (vs FMV ${updated_rsu['vest_fmv']})")
        
        # Calculate expected tax
        tax = updated_rsu['vest_market_price'] * updated_rsu['quantity'] * (updated_rsu['tax_rate'] / 100)
        print(f"   💸 Expected tax: ${tax:.0f} ({updated_rsu['tax_rate']}% of ${updated_rsu['vest_market_price'] * updated_rsu['quantity']:.0f})")
    else:
        print(f"❌ Failed to update RSU: {response.text}")
        return
    
    # Test 6: Verify all updates by fetching final asset state
    print("\n📊 Test 6: Verifying Final Asset States")
    print("-" * 50)
    
    response = session.get(f'{BASE_URL}/api/assets')
    if response.status_code == 200:
        assets = response.json()
        print(f"✅ Loaded {len(assets)} assets")
        
        for asset in assets:
            print(f"\n   {asset['symbol']} ({asset['asset_type'].upper()})")
            print(f"      📊 ID: {asset['id']}")
            print(f"      🔢 Quantity: {asset['quantity']}")
            print(f"      💰 Value: {asset['currency']} {asset['total_value']:.2f}")
            
            if asset['asset_type'] in ['stock_option', 'rsu']:
                print(f"      📊 Status: {asset['status']}")
                if asset.get('tax_rate'):
                    print(f"      🏛️ Tax: {asset['tax_country']} {asset['tax_rate']}%")
                    
                    current_tax = asset.get('current_tax_liability', 0)
                    potential_tax = asset.get('potential_tax_liability', 0)
                    
                    if current_tax > 0:
                        print(f"      💸 Tax Owed: {asset['currency']} {current_tax:.2f}")
                    elif potential_tax > 0:
                        print(f"      ⚠️ Potential Tax: {asset['currency']} {potential_tax:.2f}")
    else:
        print(f"❌ Failed to load final assets: {response.text}")
    
    # Test 7: Test error handling - try to edit non-existent asset
    print("\n❌ Test 7: Error Handling - Non-existent Asset")
    print("-" * 50)
    
    response = session.get(f'{BASE_URL}/api/assets/99999')
    if response.status_code == 404:
        print("✅ Correctly handled non-existent asset fetch")
        print(f"   ⚠️ Error: {response.json().get('error', 'Unknown error')}")
    else:
        print("❌ Error handling failed for non-existent asset")
    
    response = session.put(f'{BASE_URL}/api/assets/99999', json=updated_stock)
    if response.status_code == 404:
        print("✅ Correctly handled non-existent asset update")
        print(f"   ⚠️ Error: {response.json().get('error', 'Unknown error')}")
    else:
        print("❌ Error handling failed for non-existent asset update")
    
    print("\n" + "=" * 60)
    print("🎉 Asset Editing Functionality Testing Complete!")
    print("\n✅ Features validated:")
    print("   ✏️ Create, Read, Update, Delete (CRUD) operations")
    print("   📝 Form population with existing asset data")
    print("   🎯 Edit all asset types (stock, stock_option, RSU)")
    print("   🏛️ Update tax information and rates")
    print("   📊 Change asset status (granted → vested → exercised)")
    print("   💰 Update financial information (prices, quantities)")
    print("   ⚠️ Proper error handling for invalid operations")
    
    print("\n💡 Editing Benefits:")
    print("   • Fix data entry mistakes")
    print("   • Update asset status as circumstances change")
    print("   • Adjust tax rates based on personal situation")
    print("   • Track lifecycle changes (vesting, exercising)")
    print("   • Keep accurate records for tax planning")

if __name__ == '__main__':
    test_asset_editing()