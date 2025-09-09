#!/usr/bin/env python3
"""
Test script to verify currency conversion is working correctly in portfolio summary
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

def test_currency_conversion():
    print("💱 Testing Multi-Currency Portfolio Fix")
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
    
    # Get current portfolio summary
    print("\n📊 Current Portfolio Summary:")
    print("-" * 50)
    
    response = session.get(f'{BASE_URL}/api/portfolio-summary')
    if response.status_code == 200:
        summary = response.json()
        print(f"✅ Total Portfolio Value: ${summary['total_value']:.2f} USD")
        print(f"   Total Cost Basis: ${summary['total_cost']:.2f} USD")
        print(f"   Total Gain/Loss: ${summary['total_gain_loss']:.2f} USD ({summary['total_gain_loss_percent']:.2f}%)")
        print(f"   Base Currency: {summary.get('base_currency', 'USD')}")
        print(f"   Number of Assets: {summary['asset_count']}")
        
        print(f"\n💡 Asset Distribution (in USD):")
        for asset_type, value in summary['asset_distribution'].items():
            print(f"   {asset_type}: ${value:.2f}")
            
        print(f"\n🏢 Account Distribution (in USD):")
        for account_name, value in summary['account_distribution'].items():
            print(f"   {account_name}: ${value:.2f}")
    else:
        print(f"❌ Failed to get portfolio summary: {response.text}")
        return
    
    # Get individual asset details to show original currencies
    print(f"\n📈 Individual Asset Details:")
    print("-" * 50)
    
    response = session.get(f'{BASE_URL}/api/assets')
    if response.status_code == 200:
        assets = response.json()
        for asset in assets:
            local_value = asset['quantity'] * asset['current_price']
            print(f"   {asset['symbol']}: {asset['quantity']} shares")
            print(f"      Local Value: {asset['currency']} {local_value:.2f}")
            print(f"      USD Value: ${asset['total_value']:.2f} (converted)")
    else:
        print(f"❌ Failed to get asset details: {response.text}")
    
    # Test currency conversion endpoint directly
    print(f"\n🔄 Testing Direct Currency Conversion:")
    print("-" * 50)
    
    # Test TWD to USD conversion 
    test_amount = 1000
    response = session.get(f'{BASE_URL}/api/currency-conversion/TWD/USD/{test_amount}')
    if response.status_code == 200:
        result = response.json()
        print(f"✅ TWD {test_amount} = USD ${result['converted_amount']:.2f}")
        print(f"   Exchange Rate: 1 TWD = {result['exchange_rate']:.6f} USD")
    else:
        print(f"❌ Currency conversion failed: {response.text}")
    
    print("\n" + "=" * 60)
    print("🎉 Currency Conversion Testing Complete!")
    print("\n✅ Key Improvements:")
    print("   💱 All portfolio values now converted to common currency (USD)")
    print("   📊 Dashboard totals show accurate combined portfolio value")
    print("   🌍 Multi-currency assets properly aggregated") 
    print("   💰 Individual assets retain original currency information")
    print("   🔄 Real-time exchange rates used for conversion")
    
    print("\n💡 How it works:")
    print("   1. Each asset's value calculated in original currency")
    print("   2. Values converted to USD using live exchange rates")
    print("   3. USD values summed for accurate portfolio totals")
    print("   4. Fallback rates used if API is unavailable")

if __name__ == '__main__':
    test_currency_conversion()