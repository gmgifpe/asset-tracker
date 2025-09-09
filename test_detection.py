#!/usr/bin/env python3
"""
Test CSV format detection
"""

def detect_csv_format(csv_content):
    """Detect if CSV is from Firstrade or Charles Schwab"""
    first_line = csv_content.split('\n')[0].lower()
    
    # Look for characteristic column names
    if 'fees & comm' in first_line or 'fees &amp; comm' in first_line:
        # Schwab has "Fees & Comm" column
        return 'schwab'
    elif 'recordtype' in first_line or 'tradedate' in first_line:
        # Firstrade has "RecordType" and "TradeDate" columns
        return 'firstrade'
    elif 'action' in first_line and 'amount' in first_line and 'description' in first_line:
        # Generic format that could be either, but more likely Schwab
        return 'schwab'
    
    # Default to firstrade if unclear
    return 'firstrade'

# Test Firstrade CSV
with open("FT_CSV_90112646.csv", "r", encoding="utf-8") as f:
    firstrade_content = f.read()

print(f"Firstrade CSV detected as: {detect_csv_format(firstrade_content)}")
print(f"First line: {firstrade_content.split()[0]}")

# Test Schwab CSV  
with open("Individual_XXX411_Transactions_20250909-152640.csv", "r", encoding="utf-8") as f:
    schwab_content = f.read()

print(f"Schwab CSV detected as: {detect_csv_format(schwab_content)}")
print(f"First line: {schwab_content.split()[0]}")