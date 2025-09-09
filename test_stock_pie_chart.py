#!/usr/bin/env python3
"""
Test script to verify the new stock comparison pie chart functionality
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

def test_stock_pie_chart():
    print("📊 Testing Stock Comparison Pie Chart")
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
    
    # Get portfolio summary to see the new stock distribution
    print("\n📊 Portfolio Summary with Stock Distribution:")
    print("-" * 50)
    
    response = session.get(f'{BASE_URL}/api/portfolio-summary')
    if response.status_code == 200:
        summary = response.json()
        print(f"✅ Total Portfolio Value: ${summary['total_value']:.2f} USD")
        print(f"   Number of Assets: {summary['asset_count']}")
        
        # Show all three distributions
        print(f"\n🎯 Asset Type Distribution (Pie Chart 1):")
        for asset_type, value in summary['asset_distribution'].items():
            percentage = (value / summary['total_value']) * 100
            print(f"   {asset_type}: ${value:.2f} ({percentage:.1f}%)")
        
        print(f"\n🏢 Account Distribution (Pie Chart 2):")
        for account_name, value in summary['account_distribution'].items():
            percentage = (value / summary['total_value']) * 100
            print(f"   {account_name}: ${value:.2f} ({percentage:.1f}%)")
        
        print(f"\n📈 Stock Holdings Distribution (Pie Chart 3 - NEW!):")
        if 'stock_distribution' in summary:
            # Sort by value for better display
            sorted_stocks = sorted(summary['stock_distribution'].items(), key=lambda x: x[1], reverse=True)
            for symbol, value in sorted_stocks:
                percentage = (value / summary['total_value']) * 100
                print(f"   {symbol}: ${value:.2f} ({percentage:.1f}%)")
        else:
            print("   ❌ Stock distribution data not available")
    else:
        print(f"❌ Failed to get portfolio summary: {response.text}")
        return
    
    # Get individual assets to show the data source
    print(f"\n📋 Individual Asset Breakdown:")
    print("-" * 50)
    
    response = session.get(f'{BASE_URL}/api/assets')
    if response.status_code == 200:
        assets = response.json()
        print(f"Found {len(assets)} individual assets:")
        
        for asset in assets:
            local_value = asset['quantity'] * asset['current_price']
            print(f"   {asset['symbol']}: {asset['quantity']} shares")
            print(f"      Current Price: {asset['currency']} {asset['current_price']:.2f}")
            print(f"      Local Value: {asset['currency']} {local_value:.2f}")
            print(f"      USD Value: ${asset['total_value']:.2f}")
            print()
    else:
        print(f"❌ Failed to get asset details: {response.text}")
    
    print("=" * 60)
    print("🎉 Stock Comparison Pie Chart Testing Complete!")
    print("\n✅ New Features Added:")
    print("   📊 Third pie chart showing individual stock holdings")
    print("   🎯 Stocks sorted by portfolio value (largest first)")
    print("   💰 All values converted to USD for accurate comparison")
    print("   🌈 Diverse color palette for many stocks")
    print("   📱 Responsive design for mobile devices")
    print("   💡 Detailed tooltips with percentages")
    
    print("\n📈 Dashboard Now Has Three Pie Charts:")
    print("   1. Asset Type Distribution (stock, crypto, real-asset, etc.)")
    print("   2. Account Distribution (by brokerage account)")
    print("   3. Stock Holdings Distribution (by individual ticker)")
    
    print("\n💡 Benefits:")
    print("   • See which individual stocks dominate your portfolio")
    print("   • Identify concentration risk in specific stocks")
    print("   • Visual representation of diversification")
    print("   • Quick identification of largest holdings")

if __name__ == '__main__':
    test_stock_pie_chart()