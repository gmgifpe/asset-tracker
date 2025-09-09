#!/usr/bin/env python3
"""
Test the complete updated Schwab parser (simulating the actual app function)
"""
import csv
import io
from datetime import datetime
from dateutil.parser import parse as dateparse

def parse_schwab_csv(csv_content):
    """Parse Charles Schwab CSV transaction format"""
    transactions = []
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        try:
            # Schwab CSV format (actual columns):
            # Date, Action, Symbol, Description, Quantity, Price, Fees & Comm, Amount
            date_str = row.get('Date', '').strip()
            action = row.get('Action', '').strip()
            symbol = row.get('Symbol', '').strip().upper()
            description = row.get('Description', '').strip()
            quantity_str = row.get('Quantity', '0').strip()
            price_str = row.get('Price', '0').strip()
            amount_str = row.get('Amount', '0').strip()
            
            # Skip rows without symbol, date, or action
            if not symbol or not date_str or not action:
                continue
            
            # Parse date (handle complex formats like "06/13/2024 as of 06/10/2024")
            try:
                # If date has " as of " format, take the first date
                if " as of " in date_str:
                    date_str = date_str.split(" as of ")[0].strip()
                transaction_date = dateparse(date_str)
            except:
                continue
            
            # Clean and parse numeric values
            quantity = float(quantity_str.replace(',', '')) if quantity_str else 0
            price = float(price_str.replace('$', '').replace(',', '')) if price_str else 0
            amount = float(amount_str.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')) if amount_str else 0
            
            # Map Schwab actions to transaction types
            action_upper = action.upper()
            transaction_type = None
            name = description  # Default to full description
            
            if action_upper in ['SELL', 'SELL SHORT', 'SELL TO CLOSE']:
                transaction_type = 'SELL'
                quantity = abs(quantity)
            elif action_upper in ['BUY', 'BUY TO OPEN', 'BUY TO COVER']:
                transaction_type = 'BUY'
                quantity = abs(quantity)
            elif action_upper in ['REINVEST SHARES', 'REINVEST DIVIDEND']:
                # Treat reinvest as BUY
                transaction_type = 'BUY'
                quantity = abs(quantity)
                # For reinvest, the amount is typically negative, so we use abs of amount divided by price
                if price > 0 and amount != 0:
                    calculated_quantity = abs(amount) / price
                    if quantity == 0:
                        quantity = calculated_quantity
            else:
                # Skip other actions like dividends, fees, interest, tax adjustments, etc.
                continue
            
            # Skip if still no valid quantity or price
            if quantity == 0 or price == 0:
                continue
            
            transactions.append({
                'date': transaction_date,
                'symbol': symbol,
                'name': name,
                'description': description,
                'quantity': quantity,
                'price': price,
                'amount': abs(amount),
                'transaction_type': transaction_type,
                'broker': 'Charles Schwab'
            })
            
        except (ValueError, KeyError) as e:
            print(f"Error parsing Schwab row: {row}, Error: {e}")
            continue
    
    return transactions

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

if __name__ == "__main__":
    # Read the Schwab CSV file
    with open("Individual_XXX411_Transactions_20250909-152640.csv", "r", encoding="utf-8") as f:
        csv_content = f.read()
    
    # Detect format
    detected_format = detect_csv_format(csv_content)
    print(f"Detected format: {detected_format}")
    
    # Parse the transactions
    if detected_format == 'schwab':
        transactions = parse_schwab_csv(csv_content)
    else:
        print("This test is for Schwab format only")
        exit(1)
    
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
    print(f"\n=== SAMPLE TRANSACTIONS ===")
    for i, txn in enumerate(transactions[:10]):
        print(f"{i+1}. {txn['transaction_type']} {txn['quantity']} {txn['symbol']} @ ${txn['price']:.2f} on {txn['date'].strftime('%Y-%m-%d')}")
        print(f"   Company: {txn['name']}")
        print(f"   Amount: ${txn['amount']:.2f}")
        print()