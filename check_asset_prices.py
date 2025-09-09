#!/usr/bin/env python3
"""
Check asset prices in the database
"""
import os
import sys
import sqlite3

def check_asset_prices():
    # Connect to database
    db_path = 'instance/asset_tracker.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check assets with zero current_price
    cursor.execute('''
        SELECT symbol, name, current_price, quantity, purchase_price 
        FROM asset 
        WHERE current_price = 0 OR current_price IS NULL
        ORDER BY symbol
    ''')
    
    zero_price_assets = cursor.fetchall()
    
    if zero_price_assets:
        print(f"Assets with missing prices ({len(zero_price_assets)}):")
        for symbol, name, current_price, quantity, purchase_price in zero_price_assets:
            print(f"  {symbol}: {name} (qty: {quantity}, purchase: ${purchase_price}, current: ${current_price or 0})")
    else:
        print("All assets have current prices!")
    
    # Check all assets
    cursor.execute('''
        SELECT symbol, name, current_price, quantity, purchase_price 
        FROM asset 
        ORDER BY symbol
    ''')
    
    all_assets = cursor.fetchall()
    
    print(f"\nAll assets ({len(all_assets)}):")
    for symbol, name, current_price, quantity, purchase_price in all_assets:
        print(f"  {symbol}: {name} (qty: {quantity}, purchase: ${purchase_price}, current: ${current_price or 0})")
    
    conn.close()

if __name__ == "__main__":
    check_asset_prices()