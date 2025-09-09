#!/usr/bin/env python3
"""
Clear duplicate transactions from the database
"""
import os
import sys
import sqlite3

def clear_transactions():
    # Connect to database
    db_path = 'instance/asset_tracker.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current count
    cursor.execute('SELECT COUNT(*) FROM "transaction"')
    before_count = cursor.fetchone()[0]
    print(f"Transactions before cleanup: {before_count}")
    
    cursor.execute('SELECT COUNT(*) FROM "asset"')
    assets_before = cursor.fetchone()[0]
    print(f"Assets before cleanup: {assets_before}")
    
    # Clear all transactions and assets
    cursor.execute('DELETE FROM "transaction"')
    cursor.execute('DELETE FROM "asset"')
    
    # Reset auto-increment counters (if table exists)
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='transaction'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='asset'")
    except sqlite3.OperationalError:
        # sqlite_sequence table doesn't exist, skip
        pass
    
    conn.commit()
    
    # Check after cleanup
    cursor.execute('SELECT COUNT(*) FROM "transaction"')
    after_count = cursor.fetchone()[0]
    print(f"Transactions after cleanup: {after_count}")
    
    cursor.execute('SELECT COUNT(*) FROM "asset"')
    assets_after = cursor.fetchone()[0]
    print(f"Assets after cleanup: {assets_after}")
    
    conn.close()
    print("Database cleaned successfully!")

if __name__ == "__main__":
    clear_transactions()