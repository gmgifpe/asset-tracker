from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
CORS(app)

# Simple file-based data storage
DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'users': [], 'accounts': [], 'assets': []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_current_price_simple(symbol, asset_type):
    """Simplified price fetching without yfinance dependency"""
    try:
        if asset_type == 'stock':
            # Using Alpha Vantage free API (demo key)
            url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=demo'
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'Global Quote' in data:
                    price = data['Global Quote'].get('05. price', '0')
                    return float(price)
        elif asset_type == 'crypto':
            # Using CoinGecko API
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'LTC': 'litecoin',
                'XRP': 'ripple',
                'ADA': 'cardano'
            }
            coin_id = symbol_map.get(symbol.upper(), symbol.lower())
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd'
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    return float(data[coin_id]['usd'])
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
    
    return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    storage = load_data()
    
    # Check if user exists
    for user in storage['users']:
        if user['username'] == data['username']:
            return jsonify({'error': 'Username already exists'}), 400
        if user['email'] == data['email']:
            return jsonify({'error': 'Email already exists'}), 400
    
    user = {
        'id': len(storage['users']) + 1,
        'username': data['username'],
        'email': data['email'],
        'password_hash': generate_password_hash(data['password']),
        'created_at': datetime.now().isoformat()
    }
    
    storage['users'].append(user)
    save_data(storage)
    
    return jsonify({'message': 'User created successfully', 'user_id': user['id']}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    storage = load_data()
    
    user = None
    for u in storage['users']:
        if u['username'] == data['username']:
            user = u
            break
    
    if user and check_password_hash(user['password_hash'], data['password']):
        session['user_id'] = user['id']
        return jsonify({'message': 'Login successful', 'user_id': user['id']}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/users')
def get_users():
    storage = load_data()
    return jsonify([{
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'created_at': user['created_at']
    } for user in storage['users']])

@app.route('/api/switch-user/<int:user_id>', methods=['POST'])
def switch_user(user_id):
    storage = load_data()
    user = None
    for u in storage['users']:
        if u['id'] == user_id:
            user = u
            break
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    session['user_id'] = user_id
    return jsonify({'message': 'User switched successfully', 'user_id': user_id}), 200

@app.route('/api/accounts', methods=['GET', 'POST'])
def accounts():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    storage = load_data()
    
    if request.method == 'POST':
        data = request.get_json()
        account = {
            'id': len(storage['accounts']) + 1,
            'user_id': user_id,
            'name': data['name'],
            'account_type': data['account_type'],
            'currency': data.get('currency', 'USD'),
            'created_at': datetime.now().isoformat()
        }
        storage['accounts'].append(account)
        save_data(storage)
        return jsonify({'message': 'Account created', 'account_id': account['id']}), 201
    
    user_accounts = [acc for acc in storage['accounts'] if acc['user_id'] == user_id]
    return jsonify(user_accounts)

@app.route('/api/assets', methods=['GET', 'POST'])
def assets():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    storage = load_data()
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Get current price for the asset
        current_price = get_current_price_simple(data['symbol'], data['asset_type'])
        if current_price == 0:
            current_price = float(data['purchase_price'])  # Fallback to purchase price
        
        asset = {
            'id': len(storage['assets']) + 1,
            'user_id': user_id,
            'account_id': data.get('account_id'),
            'symbol': data['symbol'],
            'name': data['name'],
            'asset_type': data['asset_type'],
            'quantity': float(data['quantity']),
            'purchase_price': float(data['purchase_price']),
            'current_price': current_price,
            'currency': data.get('currency', 'USD'),
            'purchase_date': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'notes': data.get('notes', '')
        }
        
        storage['assets'].append(asset)
        save_data(storage)
        
        return jsonify({'message': 'Asset added', 'asset_id': asset['id']}), 201
    
    user_assets = [asset for asset in storage['assets'] if asset['user_id'] == user_id]
    
    # Calculate derived values
    for asset in user_assets:
        asset['total_value'] = asset['quantity'] * asset['current_price']
        asset['gain_loss'] = (asset['current_price'] - asset['purchase_price']) * asset['quantity']
        if asset['purchase_price'] > 0:
            asset['gain_loss_percent'] = ((asset['current_price'] - asset['purchase_price']) / asset['purchase_price'] * 100)
        else:
            asset['gain_loss_percent'] = 0
    
    return jsonify(user_assets)

@app.route('/api/portfolio-summary')
def portfolio_summary():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    storage = load_data()
    
    user_assets = [asset for asset in storage['assets'] if asset['user_id'] == user_id]
    user_accounts = [acc for acc in storage['accounts'] if acc['user_id'] == user_id]
    
    total_value = sum(asset['quantity'] * asset['current_price'] for asset in user_assets)
    total_cost = sum(asset['quantity'] * asset['purchase_price'] for asset in user_assets)
    total_gain_loss = total_value - total_cost
    
    # Group by asset type for pie chart
    asset_distribution = {}
    for asset in user_assets:
        asset_type = asset['asset_type']
        value = asset['quantity'] * asset['current_price']
        asset_distribution[asset_type] = asset_distribution.get(asset_type, 0) + value
    
    # Group by account
    account_distribution = {}
    for asset in user_assets:
        account_name = 'No Account'
        if asset.get('account_id'):
            for acc in user_accounts:
                if acc['id'] == asset['account_id']:
                    account_name = acc['name']
                    break
        
        value = asset['quantity'] * asset['current_price']
        account_distribution[account_name] = account_distribution.get(account_name, 0) + value
    
    return jsonify({
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain_loss': total_gain_loss,
        'total_gain_loss_percent': (total_gain_loss / total_cost * 100) if total_cost > 0 else 0,
        'asset_distribution': asset_distribution,
        'account_distribution': account_distribution,
        'asset_count': len(user_assets)
    })

@app.route('/api/update-prices', methods=['POST'])
def update_prices():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    storage = load_data()
    
    updated_count = 0
    for asset in storage['assets']:
        if asset['user_id'] == user_id and asset['asset_type'] in ['stock', 'crypto']:
            new_price = get_current_price_simple(asset['symbol'], asset['asset_type'])
            if new_price > 0:
                asset['current_price'] = new_price
                asset['last_updated'] = datetime.now().isoformat()
                updated_count += 1
    
    save_data(storage)
    return jsonify({'message': f'Updated prices for {updated_count} assets'})

@app.route('/api/search-symbol/<symbol>')
def search_symbol(symbol):
    try:
        # Simple symbol lookup - in a real app you'd use a proper API
        current_price = get_current_price_simple(symbol, 'stock')
        return jsonify({
            'symbol': symbol.upper(),
            'name': f"{symbol.upper()} Stock",  # Simplified - would lookup real name
            'price': current_price if current_price > 0 else 100,  # Default demo price
            'currency': 'USD'
        })
    except:
        return jsonify({'error': 'Symbol not found'}), 404

if __name__ == '__main__':
    print("Starting Asset Tracker...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)