#!/usr/bin/env python3
"""
Test script to verify the Schwab CSV parser
"""
import csv
import io
from datetime import datetime
from dateutil.parser import parse as dateparse

def parse_schwab_csv(csv_content):
    """Parse Charles Schwab CSV transaction format"""
    transactions = []
    reader = csv.DictReader(io.StringIO(csv_content))
    
    print("CSV Columns found:", reader.fieldnames)
    
    for i, row in enumerate(reader):
        try:
            if i < 10:  # Print first 10 rows for debugging
                print(f"Row {i+1}: {row}")
            
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
            
            # Parse date
            transaction_date = dateparse(date_str)
            
            # Clean and parse numeric values
            quantity = float(quantity_str.replace(',', '')) if quantity_str else 0
            price = float(price_str.replace('$', '').replace(',', '')) if price_str else 0
            amount = float(amount_str.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')) if amount_str else 0
            
            # Skip if quantity or price is 0 for regular trades
            action_upper = action.upper()
            if action_upper in ['BUY', 'SELL'] and (quantity == 0 or price == 0):
                continue
            
            # Map Schwab actions to transaction types
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
                # Skip other actions like dividends, fees, interest, etc.
                print(f"Skipping action: {action}")
                continue
            
            # Skip if still no valid quantity
            if quantity == 0:
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
                'action': action,
                'broker': 'Charles Schwab'
            })
            
        except (ValueError, KeyError) as e:
            print(f"Error parsing Schwab row: {row}, Error: {e}")
            continue
    
    return transactions

if __name__ == "__main__":
    # Read the CSV file
    with open("Individual_XXX411_Transactions_20250909-152640.csv", "r", encoding="utf-8") as f:
        csv_content = f.read()
    
    # Parse the transactions
    transactions = parse_schwab_csv(csv_content)
    
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
    
    # Group by action
    actions = {}
    for t in transactions:
        action = t['action']
        actions[action] = actions.get(action, 0) + 1
    print(f"Actions found: {actions}")
    
    # Show first few transactions
    print(f"\n=== FIRST 5 TRANSACTIONS ===")
    for i, txn in enumerate(transactions[:5]):
        print(f"{i+1}. {txn['transaction_type']} {txn['quantity']} {txn['symbol']} @ ${txn['price']} on {txn['date'].strftime('%Y-%m-%d')}")
        print(f"   Action: {txn['action']}")
        print(f"   Name: {txn['name']}")
        print(f"   Amount: ${txn['amount']}")
        print()