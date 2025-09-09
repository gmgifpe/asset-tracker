#!/usr/bin/env python3
"""
Test script to verify the fixed Firstrade CSV parser
"""
import csv
import io
from datetime import datetime
from dateutil.parser import parse as dateparse

def parse_firstrade_csv(csv_content):
    """Parse Firstrade CSV transaction format"""
    transactions = []
    reader = csv.DictReader(io.StringIO(csv_content))
    
    print("CSV Columns found:", reader.fieldnames)
    
    for i, row in enumerate(reader):
        try:
            # Firstrade CSV format (actual columns):
            # Symbol,Quantity,Price,Action,Description,TradeDate,SettledDate,Interest,Amount,Commission,Fee,CUSIP,RecordType
            
            if i < 5:  # Print first 5 rows for debugging
                print(f"Row {i+1}: {row}")
            
            # Only process Trade records, skip Financial records
            record_type = row.get('RecordType', '').strip()
            if record_type != 'Trade':
                continue
                
            date_str = row.get('TradeDate', '').strip()
            symbol = row.get('Symbol', '').strip().upper()
            action = row.get('Action', '').strip().upper()
            description = row.get('Description', '').strip()
            quantity_str = row.get('Quantity', '0').strip()
            price_str = row.get('Price', '0').strip()
            amount_str = row.get('Amount', '0').strip()
            
            # Skip rows without symbol or date (like interest, transfers, etc.)
            if not symbol or not date_str:
                continue
                
            # Parse date (Firstrade uses YYYY-MM-DD format)
            transaction_date = dateparse(date_str)
            
            # Clean and parse numeric values
            quantity = float(quantity_str.replace(',', '')) if quantity_str else 0
            price = float(price_str.replace('$', '').replace(',', '')) if price_str else 0
            amount = float(amount_str.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')) if amount_str else 0
            
            # Skip if quantity or price is 0
            if quantity == 0 or price == 0:
                continue
            
            # Determine transaction type from Action column first, then from description
            transaction_type = 'BUY'
            if action == 'SELL' or 'sell' in action.lower():
                transaction_type = 'SELL'
                quantity = abs(quantity)  # Ensure positive quantity
            elif action == 'BUY' or 'buy' in action.lower():
                transaction_type = 'BUY'  
                quantity = abs(quantity)
            elif 'sell' in description.lower() or 'sold' in description.lower():
                transaction_type = 'SELL'
                quantity = abs(quantity)
            elif 'buy' in description.lower() or 'bought' in description.lower():
                transaction_type = 'BUY'
                quantity = abs(quantity)
            
            # Extract company name from description if available
            name = symbol  # Default to symbol
            if description:
                # Try to extract company name from description
                parts = description.split()
                if len(parts) > 0:
                    # Take first few words as company name, but clean it up
                    name_parts = []
                    for part in parts[:3]:  # Take first 3 words max
                        if part.upper() not in ['UNSOLICITED', 'COMMON', 'STOCK', 'INC', 'CORP', 'LTD']:
                            name_parts.append(part)
                    if name_parts:
                        name = ' '.join(name_parts)
            
            transactions.append({
                'date': transaction_date,
                'symbol': symbol,
                'name': name,
                'description': description,
                'quantity': quantity,
                'price': price,
                'amount': abs(amount),
                'transaction_type': transaction_type,
                'broker': 'Firstrade'
            })
            
        except (ValueError, KeyError) as e:
            print(f"Error parsing Firstrade row: {row}, Error: {e}")
            continue
    
    return transactions

if __name__ == "__main__":
    # Read the CSV file
    with open("FT_CSV_90112646.csv", "r", encoding="utf-8") as f:
        csv_content = f.read()
    
    # Parse the transactions
    transactions = parse_firstrade_csv(csv_content)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total transactions parsed: {len(transactions)}")
    
    # Group by transaction type
    buy_count = sum(1 for t in transactions if t['transaction_type'] == 'BUY')
    sell_count = sum(1 for t in transactions if t['transaction_type'] == 'SELL')
    
    print(f"BUY transactions: {buy_count}")
    print(f"SELL transactions: {sell_count}")
    
    # Show unique symbols
    symbols = set(t['symbol'] for t in transactions)
    print(f"Unique symbols: {len(symbols)}")
    print("Symbols found:", sorted(symbols))
    
    # Show first few transactions
    print(f"\n=== FIRST 5 TRANSACTIONS ===")
    for i, txn in enumerate(transactions[:5]):
        print(f"{i+1}. {txn['transaction_type']} {txn['quantity']} {txn['symbol']} @ ${txn['price']} on {txn['date'].strftime('%Y-%m-%d')}")
        print(f"   Name: {txn['name']}")
        print(f"   Amount: ${txn['amount']}")
        print()