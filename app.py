from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
from datetime import datetime, timedelta
import json

# Try to import optional dependencies
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("Warning: yfinance not available, using basic price fetching")

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    print("Warning: ccxt not available, using basic crypto price fetching")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not available, some analytics features may be limited")

try:
    from dateutil.parser import parse as dateparse
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    print("Warning: dateutil not available, CSV import may have limited date parsing")

import csv
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///asset_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    accounts = db.relationship('Account', backref='user', lazy=True)
    assets = db.relationship('Asset', backref='user', lazy=True)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)  # 'investment', 'bank', 'crypto', 'other'
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    assets = db.relationship('Asset', backref='account', lazy=True)

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    
    symbol = db.Column(db.String(20), nullable=False)  # Stock ticker, crypto symbol, etc.
    name = db.Column(db.String(200), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)  # 'stock', 'crypto', 'cash', 'real_estate', etc.
    
    quantity = db.Column(db.Float, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='USD')
    
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Equity compensation specific fields
    grant_date = db.Column(db.DateTime)
    vesting_date = db.Column(db.DateTime)
    expiration_date = db.Column(db.DateTime)
    strike_price = db.Column(db.Float)  # For stock options
    vest_fmv = db.Column(db.Float)  # Fair Market Value at vest (for tax calculations)
    status = db.Column(db.String(20), default='granted')  # granted, vested, exercised, expired
    
    # Tax tracking fields
    tax_country = db.Column(db.String(10), default='TW')  # Taiwan
    tax_rate = db.Column(db.Float)  # User-defined tax rate (no default)
    exercise_price = db.Column(db.Float)  # Price at which option was exercised
    exercise_date = db.Column(db.DateTime)  # When option was exercised
    vest_market_price = db.Column(db.Float)  # Market price when RSU vested
    estimated_tax_liability = db.Column(db.Float, default=0.0)  # Calculated tax owed
    
    notes = db.Column(db.Text)

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    asset_type = db.Column(db.String(50), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    
    symbol = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    
    transaction_type = db.Column(db.String(10), nullable=False)  # 'BUY' or 'SELL'
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)  # quantity * price_per_unit
    currency = db.Column(db.String(3), default='USD')
    
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    notes = db.Column(db.Text)
    
    # Relationship back to user
    user = db.relationship('User', backref='transactions')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully', 'user_id': user.id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful', 'user_id': user.id}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/users')
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat()
    } for user in users])

@app.route('/api/switch-user/<int:user_id>', methods=['POST'])
def switch_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    session['user_id'] = user_id
    return jsonify({'message': 'User switched successfully', 'user_id': user_id}), 200

@app.route('/api/accounts', methods=['GET', 'POST'])
def accounts():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        data = request.get_json()
        account = Account(
            user_id=user_id,
            name=data['name'],
            account_type=data['account_type'],
            currency=data.get('currency', 'USD')
        )
        db.session.add(account)
        db.session.commit()
        return jsonify({'message': 'Account created', 'account_id': account.id}), 201
    
    accounts = Account.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': acc.id,
        'name': acc.name,
        'account_type': acc.account_type,
        'currency': acc.currency,
        'created_at': acc.created_at.isoformat()
    } for acc in accounts])

@app.route('/api/assets', methods=['GET', 'POST'])
def assets():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Validate tax rate for equity compensation
        if data['asset_type'] in ['stock_option', 'rsu', 'espp']:
            tax_rate = data.get('tax_rate')
            if tax_rate is not None and tax_rate != '':
                try:
                    tax_rate_float = float(tax_rate)
                    if tax_rate_float < 0 or tax_rate_float > 100:
                        return jsonify({'error': '稅率必須在 0% 到 100% 之間'}), 400
                except ValueError:
                    return jsonify({'error': '稅率必須是有效的數字'}), 400
        
        # Get current price for the asset
        current_price = get_current_price(data['symbol'], data['asset_type'])
        
        asset = Asset(
            user_id=user_id,
            account_id=data.get('account_id'),
            symbol=data['symbol'],
            name=data['name'],
            asset_type=data['asset_type'],
            quantity=float(data['quantity']),
            purchase_price=float(data['purchase_price']),
            current_price=current_price,
            currency=data.get('currency', 'USD'),
            notes=data.get('notes', ''),
            # Equity compensation fields
            grant_date=datetime.fromisoformat(data['grant_date']) if data.get('grant_date') else None,
            vesting_date=datetime.fromisoformat(data['vesting_date']) if data.get('vesting_date') else None,
            expiration_date=datetime.fromisoformat(data['expiration_date']) if data.get('expiration_date') else None,
            strike_price=float(data['strike_price']) if data.get('strike_price') else None,
            vest_fmv=float(data['vest_fmv']) if data.get('vest_fmv') else None,
            status=data.get('status', 'granted'),
            # Tax tracking fields
            tax_country=data.get('tax_country', 'TW'),
            tax_rate=float(data['tax_rate']) if data.get('tax_rate') and data['tax_rate'] != '' else None,
            exercise_price=float(data['exercise_price']) if data.get('exercise_price') else None,
            exercise_date=datetime.fromisoformat(data['exercise_date']) if data.get('exercise_date') else None,
            vest_market_price=float(data['vest_market_price']) if data.get('vest_market_price') else None
        )
        
        db.session.add(asset)
        db.session.commit()
        
        return jsonify({'message': 'Asset added', 'asset_id': asset.id}), 201
    
    assets = Asset.query.filter_by(user_id=user_id).all()
    accounts = Account.query.filter_by(user_id=user_id).all()
    
    # Create account lookup dictionary
    account_lookup = {acc.id: acc.name for acc in accounts}
    
    assets_data = []
    for asset in assets:
        account_name = account_lookup.get(asset.account_id, 'No Account') if asset.account_id else 'No Account'
        
        # Calculate values based on asset type
        if asset.asset_type == 'stock_option':
            # For options, value is (current_price - strike_price) * quantity
            intrinsic_value = max(0, asset.current_price - (asset.strike_price or 0)) * asset.quantity
            total_value = intrinsic_value
            gain_loss = intrinsic_value  # Options typically have no purchase cost
            gain_loss_percent = 0 if asset.strike_price == 0 else (intrinsic_value / (asset.strike_price * asset.quantity) * 100)
        elif asset.asset_type == 'rsu':
            # For RSUs, use vest FMV as cost basis if available
            cost_basis = asset.vest_fmv or asset.purchase_price
            total_value = asset.quantity * asset.current_price
            gain_loss = (asset.current_price - cost_basis) * asset.quantity
            gain_loss_percent = ((asset.current_price - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0
        else:
            # Regular assets
            total_value = asset.quantity * asset.current_price
            gain_loss = (asset.current_price - asset.purchase_price) * asset.quantity
            gain_loss_percent = ((asset.current_price - asset.purchase_price) / asset.purchase_price * 100) if asset.purchase_price > 0 else 0
        
        # Calculate tax liabilities for equity compensation with custom tax rates
        current_tax_liability = 0
        potential_tax_liability = 0
        
        # Only calculate tax if tax rate is specified and asset is equity compensation
        if asset.asset_type in ['stock_option', 'rsu'] and asset.tax_rate is not None and asset.tax_rate > 0:
            tax_rate_decimal = asset.tax_rate / 100  # Convert percentage to decimal
            
            if asset.asset_type == 'stock_option':
                if asset.status == 'exercised' and asset.exercise_price:
                    # Tax on exercised options = tax_rate * (exercise_price - strike_price) * quantity
                    current_tax_liability = tax_rate_decimal * max(0, asset.exercise_price - (asset.strike_price or 0)) * asset.quantity
                else:
                    # Potential tax if exercised at current price
                    potential_tax_liability = tax_rate_decimal * max(0, asset.current_price - (asset.strike_price or 0)) * asset.quantity
                    
            elif asset.asset_type == 'rsu':
                if asset.status == 'vested' and asset.vest_market_price:
                    # Tax on vested RSUs = tax_rate * vest_market_price * quantity
                    current_tax_liability = tax_rate_decimal * asset.vest_market_price * asset.quantity
                else:
                    # Potential tax if vested at current price
                    potential_tax_liability = tax_rate_decimal * asset.current_price * asset.quantity
        
        assets_data.append({
            'id': asset.id,
            'account_id': asset.account_id,
            'account_name': account_name,
            'symbol': asset.symbol,
            'name': asset.name,
            'asset_type': asset.asset_type,
            'quantity': asset.quantity,
            'purchase_price': asset.purchase_price,
            'current_price': asset.current_price,
            'currency': asset.currency,
            'total_value': total_value,
            'gain_loss': gain_loss,
            'gain_loss_percent': gain_loss_percent,
            'purchase_date': asset.purchase_date.isoformat(),
            'notes': asset.notes,
            # Equity compensation fields
            'grant_date': asset.grant_date.isoformat() if asset.grant_date else None,
            'vesting_date': asset.vesting_date.isoformat() if asset.vesting_date else None,
            'expiration_date': asset.expiration_date.isoformat() if asset.expiration_date else None,
            'strike_price': asset.strike_price,
            'vest_fmv': asset.vest_fmv,
            'status': asset.status,
            # Tax tracking fields
            'tax_country': asset.tax_country,
            'tax_rate': asset.tax_rate,
            'exercise_price': asset.exercise_price,
            'exercise_date': asset.exercise_date.isoformat() if asset.exercise_date else None,
            'vest_market_price': asset.vest_market_price,
            'current_tax_liability': current_tax_liability,
            'potential_tax_liability': potential_tax_liability
        })
    
    return jsonify(assets_data)

@app.route('/api/assets/<int:asset_id>', methods=['GET', 'PUT', 'DELETE'])
def asset_detail(asset_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first()
    
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    if request.method == 'GET':
        # Return asset details for editing
        asset_data = {
            'id': asset.id,
            'account_id': asset.account_id,
            'symbol': asset.symbol,
            'name': asset.name,
            'asset_type': asset.asset_type,
            'quantity': asset.quantity,
            'purchase_price': asset.purchase_price,
            'current_price': asset.current_price,
            'currency': asset.currency,
            'notes': asset.notes,
            # Equity compensation fields
            'grant_date': asset.grant_date.isoformat() if asset.grant_date else None,
            'vesting_date': asset.vesting_date.isoformat() if asset.vesting_date else None,
            'expiration_date': asset.expiration_date.isoformat() if asset.expiration_date else None,
            'strike_price': asset.strike_price,
            'vest_fmv': asset.vest_fmv,
            'status': asset.status,
            # Tax tracking fields
            'tax_country': asset.tax_country,
            'tax_rate': asset.tax_rate,
            'exercise_price': asset.exercise_price,
            'exercise_date': asset.exercise_date.isoformat() if asset.exercise_date else None,
            'vest_market_price': asset.vest_market_price
        }
        return jsonify(asset_data)
    
    elif request.method == 'PUT':
        # Update asset
        data = request.get_json()
        
        # Validate tax rate for equity compensation
        if data['asset_type'] in ['stock_option', 'rsu', 'espp']:
            tax_rate = data.get('tax_rate')
            if tax_rate is not None and tax_rate != '':
                try:
                    tax_rate_float = float(tax_rate)
                    if tax_rate_float < 0 or tax_rate_float > 100:
                        return jsonify({'error': '稅率必須在 0% 到 100% 之間'}), 400
                except ValueError:
                    return jsonify({'error': '稅率必須是有效的數字'}), 400
        
        # Get current price for the asset if symbol changed
        current_price = asset.current_price  # Keep current price if symbol didn't change
        if data['symbol'] != asset.symbol:
            current_price = get_current_price(data['symbol'], data['asset_type'])
        
        # Update asset fields
        asset.account_id = data.get('account_id')
        asset.symbol = data['symbol']
        asset.name = data['name']
        asset.asset_type = data['asset_type']
        asset.quantity = float(data['quantity'])
        asset.purchase_price = float(data['purchase_price'])
        asset.current_price = current_price
        asset.currency = data.get('currency', 'USD')
        asset.notes = data.get('notes', '')
        asset.last_updated = datetime.utcnow()
        
        # Update equity compensation fields
        asset.grant_date = datetime.fromisoformat(data['grant_date']) if data.get('grant_date') else None
        asset.vesting_date = datetime.fromisoformat(data['vesting_date']) if data.get('vesting_date') else None
        asset.expiration_date = datetime.fromisoformat(data['expiration_date']) if data.get('expiration_date') else None
        asset.strike_price = float(data['strike_price']) if data.get('strike_price') else None
        asset.vest_fmv = float(data['vest_fmv']) if data.get('vest_fmv') else None
        asset.status = data.get('status', 'granted')
        
        # Update tax tracking fields
        asset.tax_country = data.get('tax_country', 'TW')
        asset.tax_rate = float(data['tax_rate']) if data.get('tax_rate') and data['tax_rate'] != '' else None
        asset.exercise_price = float(data['exercise_price']) if data.get('exercise_price') else None
        asset.exercise_date = datetime.fromisoformat(data['exercise_date']) if data.get('exercise_date') else None
        asset.vest_market_price = float(data['vest_market_price']) if data.get('vest_market_price') else None
        
        db.session.commit()
        return jsonify({'message': 'Asset updated successfully'})
    
    elif request.method == 'DELETE':
        # Delete asset
        db.session.delete(asset)
        db.session.commit()
        return jsonify({'message': 'Asset deleted successfully'})

@app.route('/api/portfolio-summary')
def portfolio_summary():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    assets = Asset.query.filter_by(user_id=user_id).all()
    
    # Convert all values to USD before summing
    total_value_usd = 0
    total_cost_usd = 0
    
    for asset in assets:
        # Convert current value to USD
        current_value_local = asset.quantity * asset.current_price
        current_value_usd = convert_to_usd(current_value_local, asset.currency)
        total_value_usd += current_value_usd
        
        # Convert cost to USD
        cost_local = asset.quantity * asset.purchase_price
        cost_usd = convert_to_usd(cost_local, asset.currency)
        total_cost_usd += cost_usd
    
    total_gain_loss = total_value_usd - total_cost_usd
    
    # Group by asset type for pie chart (in USD)
    asset_distribution = {}
    for asset in assets:
        asset_type = asset.asset_type
        value_local = asset.quantity * asset.current_price
        value_usd = convert_to_usd(value_local, asset.currency)
        asset_distribution[asset_type] = asset_distribution.get(asset_type, 0) + value_usd
    
    # Group by account (in USD)
    account_distribution = {}
    for asset in assets:
        account_name = asset.account.name if asset.account else 'No Account'
        value_local = asset.quantity * asset.current_price
        value_usd = convert_to_usd(value_local, asset.currency)
        account_distribution[account_name] = account_distribution.get(account_name, 0) + value_usd
    
    # Group by individual stock/symbol (in USD)
    stock_distribution = {}
    for asset in assets:
        symbol = asset.symbol
        value_local = asset.quantity * asset.current_price
        value_usd = convert_to_usd(value_local, asset.currency)
        stock_distribution[symbol] = stock_distribution.get(symbol, 0) + value_usd
    
    return jsonify({
        'total_value': total_value_usd,
        'total_cost': total_cost_usd,
        'total_gain_loss': total_gain_loss,
        'total_gain_loss_percent': (total_gain_loss / total_cost_usd * 100) if total_cost_usd > 0 else 0,
        'asset_distribution': asset_distribution,
        'account_distribution': account_distribution,
        'stock_distribution': stock_distribution,
        'asset_count': len(assets),
        'base_currency': 'USD'
    })

@app.route('/api/update-prices', methods=['POST'])
def update_prices():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    assets = Asset.query.filter_by(user_id=user_id).all()
    
    updated_count = 0
    for asset in assets:
        if asset.asset_type in ['stock', 'crypto']:
            new_price = get_current_price(asset.symbol, asset.asset_type)
            if new_price > 0:
                asset.current_price = new_price
                asset.last_updated = datetime.utcnow()
                updated_count += 1
    
    db.session.commit()
    return jsonify({'message': f'Updated prices for {updated_count} assets'})

def get_current_price(symbol, asset_type):
    print(f"Getting price for {symbol} (type: {asset_type})")
    try:
        if asset_type == 'stock':
            if YFINANCE_AVAILABLE:
                # Handle Taiwan stock symbols
                search_symbol = symbol
                if symbol.isdigit() and len(symbol) == 4:
                    search_symbol = f"{symbol}.TW"
                
                # Use yfinance for more reliable stock data
                print(f"Trying yfinance with symbol: {search_symbol}")
                ticker = yf.Ticker(search_symbol)
                data = ticker.history(period='5d')
                if not data.empty:
                    price = float(data['Close'].iloc[-1])
                    print(f"yfinance price found for {search_symbol}: ${price}")
                    return price
                
                # If Taiwan symbol didn't work, try original symbol
                if search_symbol != symbol:
                    print(f"Taiwan symbol failed, trying original: {symbol}")
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period='5d')
                    if not data.empty:
                        price = float(data['Close'].iloc[-1])
                        print(f"yfinance price found for {symbol}: ${price}")
                        return price
                        
                print(f"yfinance returned no data for {symbol}")
            else:
                # Fallback to Alpha Vantage API (free tier)
                url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=demo'
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'Global Quote' in data:
                        price = data['Global Quote'].get('05. price', '0')
                        if price and price != '0':
                            return float(price)
        
        elif asset_type == 'crypto':
            if CCXT_AVAILABLE:
                # Use ccxt for better crypto exchange support
                try:
                    exchange = ccxt.binance()
                    ticker = exchange.fetch_ticker(f'{symbol.upper()}/USDT')
                    return float(ticker['last'])
                except:
                    pass  # Fall back to CoinGecko
            
            # CoinGecko API for crypto prices
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'LTC': 'litecoin',
                'XRP': 'ripple',
                'ADA': 'cardano',
                'DOT': 'polkadot',
                'LINK': 'chainlink',
                'BCH': 'bitcoin-cash',
                'XLM': 'stellar',
                'DOGE': 'dogecoin'
            }
            
            coin_id = symbol_map.get(symbol.upper(), symbol.lower())
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    return float(data[coin_id]['usd'])
                    
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
    
    return 0

@app.route('/api/search-symbol/<symbol>')
def search_symbol(symbol):
    try:
        symbol_upper = symbol.upper()
        print(f"Searching for symbol: {symbol_upper}")
        
        # Check if this is a known crypto symbol first
        crypto_symbols = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum', 
            'LTC': 'litecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOT': 'polkadot',
            'LINK': 'chainlink',
            'BCH': 'bitcoin-cash',
            'XLM': 'stellar',
            'DOGE': 'dogecoin',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'AVAX': 'avalanche-2',
            'MATIC': 'matic-network'
        }
        
        if symbol_upper in crypto_symbols:
            # This is a crypto symbol, get crypto price
            crypto_price = get_current_price(symbol_upper, 'crypto')
            if crypto_price > 0:
                crypto_name_map = {
                    'BTC': 'Bitcoin',
                    'ETH': 'Ethereum',
                    'LTC': 'Litecoin', 
                    'XRP': 'XRP (Ripple)',
                    'ADA': 'Cardano',
                    'DOT': 'Polkadot',
                    'LINK': 'Chainlink',
                    'BCH': 'Bitcoin Cash',
                    'XLM': 'Stellar',
                    'DOGE': 'Dogecoin',
                    'USDT': 'Tether',
                    'USDC': 'USD Coin',
                    'BNB': 'Binance Coin',
                    'SOL': 'Solana',
                    'AVAX': 'Avalanche',
                    'MATIC': 'Polygon'
                }
                
                return jsonify({
                    'symbol': symbol_upper,
                    'name': crypto_name_map.get(symbol_upper, f"{symbol_upper} Cryptocurrency"),
                    'price': crypto_price,
                    'currency': 'USD'
                })
        
        if YFINANCE_AVAILABLE:
            try:
                # Use yfinance for detailed stock information
                ticker = yf.Ticker(symbol_upper)
                
                # Try to get current price first from info
                info = ticker.info
                current_price = info.get('currentPrice', 0)
                
                # If no current price in info, try history
                if not current_price or current_price == 0:
                    hist = ticker.history(period='5d')  # Get more days in case of weekend
                    if not hist.empty:
                        current_price = float(hist['Close'].iloc[-1])
                
                # If we still don't have a price, try our fallback method
                if not current_price or current_price == 0:
                    current_price = get_current_price(symbol_upper, 'stock')
                
                # Get company name
                company_name = info.get('longName') or info.get('shortName') or f"{symbol_upper} Stock"
                
                # Handle Taiwan stock symbols (add .TW if it's a Taiwan stock number)
                if symbol_upper.isdigit() and len(symbol_upper) == 4:
                    taiwan_symbol = f"{symbol_upper}.TW"
                    try:
                        taiwan_ticker = yf.Ticker(taiwan_symbol)
                        taiwan_info = taiwan_ticker.info
                        if taiwan_info and 'longName' in taiwan_info:
                            company_name = taiwan_info.get('longName', f"{symbol_upper} (Taiwan)")
                            current_price = taiwan_info.get('currentPrice', current_price)
                            if not current_price:
                                taiwan_hist = taiwan_ticker.history(period='5d')
                                if not taiwan_hist.empty:
                                    current_price = float(taiwan_hist['Close'].iloc[-1])
                    except:
                        pass
                
                print(f"Found symbol info: {company_name}, price: {current_price}")
                
                return jsonify({
                    'symbol': symbol_upper,
                    'name': company_name,
                    'price': current_price if current_price and current_price > 0 else 0,
                    'currency': info.get('currency', 'USD')
                })
                
            except Exception as yf_error:
                print(f"yfinance error for {symbol_upper}: {yf_error}")
                # Fall through to basic price lookup
        
        # Fallback to basic price lookup
        print(f"Using fallback price lookup for {symbol_upper}")
        try:
            current_price = get_current_price(symbol_upper, 'stock')
            if current_price:
                print(f"Fallback price found for {symbol_upper}: ${current_price}")
        except Exception as fallback_error:
            print(f"Fallback price lookup failed for {symbol_upper}: {fallback_error}")
            current_price = 0
        
        return jsonify({
            'symbol': symbol_upper,
            'name': f"{symbol_upper} Stock",
            'price': current_price if current_price > 0 else 100,  # Default demo price
            'currency': 'USD'
        })
        
    except Exception as e:
        print(f"Error searching symbol {symbol}: {e}")
        # Return a basic response instead of error for better UX
        return jsonify({
            'symbol': symbol.upper(),
            'name': f"{symbol.upper()} Stock",
            'price': 0,
            'currency': 'USD'
        })

# Advanced Analytics Endpoints

@app.route('/api/portfolio-history')
def portfolio_history():
    """Get historical portfolio performance"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # For now, return sample data - in a real app you'd track historical values
    sample_data = []
    base_value = 10000
    
    for i in range(30):  # Last 30 days
        date = datetime.now() - timedelta(days=29-i)
        # Simulate some portfolio growth with random variation
        variation = (i * 50) + (hash(date.strftime('%Y%m%d')) % 1000 - 500)
        value = base_value + variation
        
        sample_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'value': max(value, base_value * 0.8)  # Don't go below 80% of base
        })
    
    return jsonify(sample_data)

@app.route('/api/asset-performance')
def asset_performance():
    """Get individual asset performance metrics"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    assets = Asset.query.filter_by(user_id=user_id).all()
    
    performance_data = []
    for asset in assets:
        total_value = asset.quantity * asset.current_price
        total_cost = asset.quantity * asset.purchase_price
        gain_loss = total_value - total_cost
        gain_loss_percent = (gain_loss / total_cost * 100) if total_cost > 0 else 0
        
        # Calculate days held
        days_held = (datetime.utcnow() - asset.purchase_date).days
        
        # Annual return calculation
        if days_held > 0:
            annual_return = (gain_loss_percent / days_held) * 365
        else:
            annual_return = 0
        
        performance_data.append({
            'id': asset.id,
            'symbol': asset.symbol,
            'name': asset.name,
            'asset_type': asset.asset_type,
            'total_value': total_value,
            'gain_loss': gain_loss,
            'gain_loss_percent': gain_loss_percent,
            'days_held': days_held,
            'annual_return': annual_return,
            'allocation_percent': 0  # Will be calculated after we get total portfolio value
        })
    
    # Calculate allocation percentages
    total_portfolio_value = sum(item['total_value'] for item in performance_data)
    for item in performance_data:
        if total_portfolio_value > 0:
            item['allocation_percent'] = (item['total_value'] / total_portfolio_value) * 100
    
    return jsonify(performance_data)

# Helper function for currency conversion
def convert_to_usd(amount, from_currency):
    """Convert any currency amount to USD"""
    if from_currency == 'USD':
        return amount
    
    # Handle Taiwan Dollar specifically
    if from_currency in ['TWD', 'NTD']:
        from_currency = 'TWD'
    
    try:
        # Using exchangerate-api.com (free tier)
        url = f'https://api.exchangerate-api.com/v4/latest/{from_currency}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'USD' in data['rates']:
                return amount * data['rates']['USD']
    except Exception as e:
        print(f"Currency conversion error: {e}")
    
    # Fallback rates if API fails
    fallback_rates = {
        'TWD': 0.031,  # 1 TWD = ~0.031 USD (approximate)
        'NTD': 0.031,  # Same as TWD
        'EUR': 1.1,    # 1 EUR = ~1.1 USD
        'GBP': 1.25,   # 1 GBP = ~1.25 USD
        'JPY': 0.0067, # 1 JPY = ~0.0067 USD
    }
    
    if from_currency in fallback_rates:
        print(f"Using fallback rate for {from_currency}")
        return amount * fallback_rates[from_currency]
    
    # If all else fails, return original amount (assumes USD)
    print(f"Warning: Could not convert {from_currency} to USD, using original amount")
    return amount

@app.route('/api/currency-conversion/<from_currency>/<to_currency>/<float:amount>')
def currency_conversion(from_currency, to_currency, amount):
    """Convert currency amounts"""
    try:
        # Using exchangerate-api.com (free tier)
        url = f'https://api.exchangerate-api.com/v4/latest/{from_currency}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if to_currency in data['rates']:
                converted_amount = amount * data['rates'][to_currency]
                return jsonify({
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'original_amount': amount,
                    'converted_amount': converted_amount,
                    'exchange_rate': data['rates'][to_currency]
                })
    except Exception as e:
        print(f"Currency conversion error: {e}")
    
    return jsonify({'error': 'Currency conversion failed'}), 400

@app.route('/api/portfolio-metrics')
def portfolio_metrics():
    """Get advanced portfolio metrics"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    assets = Asset.query.filter_by(user_id=user_id).all()
    
    if not assets:
        return jsonify({'error': 'No assets found'}), 404
    
    # Convert all values to USD before calculations
    total_value = 0
    total_cost = 0
    
    for asset in assets:
        # Convert current value to USD
        current_value_local = asset.quantity * asset.current_price
        current_value_usd = convert_to_usd(current_value_local, asset.currency)
        total_value += current_value_usd
        
        # Convert cost to USD
        cost_local = asset.quantity * asset.purchase_price
        cost_usd = convert_to_usd(cost_local, asset.currency)
        total_cost += cost_usd
    
    # Calculate metrics
    metrics = {
        'total_assets': len(assets),
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain_loss': total_value - total_cost,
        'total_gain_loss_percent': ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
        'best_performer': None,
        'worst_performer': None,
        'avg_days_held': 0,
        'diversification_score': 0
    }
    
    # Find best and worst performers
    best_gain_percent = float('-inf')
    worst_gain_percent = float('inf')
    total_days = 0
    
    asset_types = set()
    for asset in assets:
        gain_percent = ((asset.current_price - asset.purchase_price) / asset.purchase_price * 100) if asset.purchase_price > 0 else 0
        days_held = (datetime.utcnow() - asset.purchase_date).days
        total_days += days_held
        asset_types.add(asset.asset_type)
        
        if gain_percent > best_gain_percent:
            best_gain_percent = gain_percent
            metrics['best_performer'] = {
                'symbol': asset.symbol,
                'name': asset.name,
                'gain_percent': gain_percent
            }
        
        if gain_percent < worst_gain_percent:
            worst_gain_percent = gain_percent
            metrics['worst_performer'] = {
                'symbol': asset.symbol,
                'name': asset.name,
                'gain_percent': gain_percent
            }
    
    metrics['avg_days_held'] = total_days // len(assets) if assets else 0
    metrics['diversification_score'] = len(asset_types)  # Simple diversification metric
    metrics['base_currency'] = 'USD'  # All values converted to USD
    
    return jsonify(metrics)

@app.route('/api/delete-asset/<int:asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """Delete an asset"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    asset = Asset.query.filter_by(id=asset_id, user_id=user_id).first()
    
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    db.session.delete(asset)
    db.session.commit()
    
    return jsonify({'message': 'Asset deleted successfully'}), 200

# Transaction Management Endpoints

@app.route('/api/transactions', methods=['GET', 'POST'])
def transactions():
    """Get user transactions or add new transaction"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['symbol', 'name', 'asset_type', 'transaction_type', 'quantity', 'price_per_unit']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate transaction type
        if data['transaction_type'].upper() not in ['BUY', 'SELL']:
            return jsonify({'error': 'Transaction type must be BUY or SELL'}), 400
        
        quantity = float(data['quantity'])
        price_per_unit = float(data['price_per_unit'])
        total_amount = quantity * price_per_unit
        
        # For SELL transactions, check if user has enough quantity
        if data['transaction_type'].upper() == 'SELL':
            current_holdings = get_current_holdings(user_id, data['symbol'])
            if current_holdings < quantity:
                return jsonify({'error': f'Insufficient holdings. You have {current_holdings} {data["symbol"]}'}), 400
        
        transaction = Transaction(
            user_id=user_id,
            account_id=data.get('account_id'),
            symbol=data['symbol'].upper(),
            name=data['name'],
            asset_type=data['asset_type'],
            transaction_type=data['transaction_type'].upper(),
            quantity=quantity,
            price_per_unit=price_per_unit,
            total_amount=total_amount,
            currency=data.get('currency', 'USD'),
            transaction_date=datetime.fromisoformat(data['transaction_date']) if 'transaction_date' in data else datetime.utcnow(),
            notes=data.get('notes', '')
        )
        
        db.session.add(transaction)
        
        # Update or create asset holding
        update_asset_holding(user_id, transaction)
        
        db.session.commit()
        
        return jsonify({'message': 'Transaction added successfully', 'transaction_id': transaction.id}), 201
    
    # GET request - return user's transactions with account information
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.transaction_date.desc()).all()
    accounts = Account.query.filter_by(user_id=user_id).all()
    
    # Create account lookup dictionary
    account_lookup = {acc.id: acc.name for acc in accounts}
    
    transactions_data = []
    for txn in transactions:
        account_name = account_lookup.get(txn.account_id, 'No Account') if txn.account_id else 'No Account'
        
        transactions_data.append({
            'id': txn.id,
            'symbol': txn.symbol,
            'name': txn.name,
            'asset_type': txn.asset_type,
            'transaction_type': txn.transaction_type,
            'quantity': txn.quantity,
            'price_per_unit': txn.price_per_unit,
            'total_amount': txn.total_amount,
            'currency': txn.currency,
            'transaction_date': txn.transaction_date.isoformat(),
            'account_id': txn.account_id,
            'account_name': account_name,
            'notes': txn.notes
        })
    
    return jsonify(transactions_data)

@app.route('/api/holdings')
def get_holdings():
    """Get current holdings calculated from transactions"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    holdings = calculate_holdings_from_transactions(user_id)
    
    # Get current prices for each holding
    for symbol, holding in holdings.items():
        current_price = get_current_price(symbol, holding['asset_type'])
        holding['current_price'] = current_price
        holding['current_value'] = holding['quantity'] * current_price
        holding['unrealized_gain_loss'] = holding['current_value'] - (holding['average_cost'] * holding['quantity'])
        holding['unrealized_gain_loss_percent'] = (holding['unrealized_gain_loss'] / (holding['average_cost'] * holding['quantity']) * 100) if holding['average_cost'] > 0 else 0
    
    return jsonify(holdings)

@app.route('/api/realized-gains')
def get_realized_gains():
    """Calculate realized gains/losses from sell transactions"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    realized_gains = calculate_realized_gains(user_id)
    
    return jsonify(realized_gains)

@app.route('/api/transaction-summary/<symbol>')
def get_transaction_summary(symbol):
    """Get transaction summary for a specific symbol"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    transactions = Transaction.query.filter_by(user_id=user_id, symbol=symbol.upper()).order_by(Transaction.transaction_date.asc()).all()
    
    if not transactions:
        return jsonify({'error': 'No transactions found for this symbol'}), 404
    
    summary = {
        'symbol': symbol.upper(),
        'name': transactions[0].name,
        'total_buy_quantity': 0,
        'total_sell_quantity': 0,
        'total_buy_amount': 0,
        'total_sell_amount': 0,
        'current_holdings': 0,
        'average_cost_basis': 0,
        'realized_gain_loss': 0,
        'transaction_count': len(transactions),
        'first_purchase_date': transactions[0].transaction_date.isoformat(),
        'transactions': []
    }
    
    running_quantity = 0
    running_cost_basis = 0
    
    for txn in transactions:
        txn_data = {
            'id': txn.id,
            'transaction_type': txn.transaction_type,
            'quantity': txn.quantity,
            'price_per_unit': txn.price_per_unit,
            'total_amount': txn.total_amount,
            'transaction_date': txn.transaction_date.isoformat(),
            'notes': txn.notes
        }
        
        if txn.transaction_type == 'BUY':
            summary['total_buy_quantity'] += txn.quantity
            summary['total_buy_amount'] += txn.total_amount
            running_quantity += txn.quantity
            running_cost_basis += txn.total_amount
        else:  # SELL
            summary['total_sell_quantity'] += txn.quantity
            summary['total_sell_amount'] += txn.total_amount
            running_quantity -= txn.quantity
            
            # Calculate realized gain/loss for this sale
            if running_quantity >= 0 and summary['total_buy_quantity'] > 0:
                avg_cost = running_cost_basis / (running_quantity + txn.quantity) if (running_quantity + txn.quantity) > 0 else 0
                realized_gain = txn.total_amount - (avg_cost * txn.quantity)
                summary['realized_gain_loss'] += realized_gain
                txn_data['realized_gain_loss'] = realized_gain
        
        summary['transactions'].append(txn_data)
    
    summary['current_holdings'] = max(0, running_quantity)
    if summary['current_holdings'] > 0 and summary['total_buy_amount'] > 0:
        summary['average_cost_basis'] = running_cost_basis / summary['current_holdings']
    
    return jsonify(summary)

def get_current_holdings(user_id, symbol):
    """Get current holdings for a symbol"""
    transactions = Transaction.query.filter_by(user_id=user_id, symbol=symbol.upper()).all()
    
    total_quantity = 0
    for txn in transactions:
        if txn.transaction_type == 'BUY':
            total_quantity += txn.quantity
        else:  # SELL
            total_quantity -= txn.quantity
    
    return max(0, total_quantity)

def calculate_holdings_from_transactions(user_id):
    """Calculate current holdings from all transactions"""
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.transaction_date.asc()).all()
    
    holdings = {}
    
    for txn in transactions:
        symbol = txn.symbol
        
        if symbol not in holdings:
            holdings[symbol] = {
                'symbol': symbol,
                'name': txn.name,
                'asset_type': txn.asset_type,
                'quantity': 0,
                'total_cost': 0,
                'average_cost': 0,
                'first_purchase_date': txn.transaction_date.isoformat()
            }
        
        if txn.transaction_type == 'BUY':
            holdings[symbol]['quantity'] += txn.quantity
            holdings[symbol]['total_cost'] += txn.total_amount
        else:  # SELL
            holdings[symbol]['quantity'] -= txn.quantity
            # Reduce total cost proportionally
            if holdings[symbol]['quantity'] >= 0:
                cost_per_share = holdings[symbol]['total_cost'] / (holdings[symbol]['quantity'] + txn.quantity) if (holdings[symbol]['quantity'] + txn.quantity) > 0 else 0
                holdings[symbol]['total_cost'] -= cost_per_share * txn.quantity
    
    # Remove holdings with zero or negative quantity
    holdings = {k: v for k, v in holdings.items() if v['quantity'] > 0}
    
    # Calculate average cost
    for symbol, holding in holdings.items():
        if holding['quantity'] > 0:
            holding['average_cost'] = holding['total_cost'] / holding['quantity']
    
    return holdings

def calculate_realized_gains(user_id):
    """Calculate realized gains from all sell transactions"""
    sell_transactions = Transaction.query.filter_by(user_id=user_id, transaction_type='SELL').order_by(Transaction.transaction_date.desc()).all()
    
    realized_gains = []
    
    for sell_txn in sell_transactions:
        # Get all buy transactions for this symbol before this sell date
        buy_transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.symbol == sell_txn.symbol,
            Transaction.transaction_type == 'BUY',
            Transaction.transaction_date <= sell_txn.transaction_date
        ).order_by(Transaction.transaction_date.asc()).all()
        
        if buy_transactions:
            # Calculate average cost basis
            total_buy_cost = sum(txn.total_amount for txn in buy_transactions)
            total_buy_quantity = sum(txn.quantity for txn in buy_transactions)
            
            if total_buy_quantity > 0:
                avg_cost_basis = total_buy_cost / total_buy_quantity
                realized_gain_loss = sell_txn.total_amount - (avg_cost_basis * sell_txn.quantity)
                realized_gain_loss_percent = (realized_gain_loss / (avg_cost_basis * sell_txn.quantity)) * 100
                
                realized_gains.append({
                    'transaction_id': sell_txn.id,
                    'symbol': sell_txn.symbol,
                    'name': sell_txn.name,
                    'sell_date': sell_txn.transaction_date.isoformat(),
                    'quantity_sold': sell_txn.quantity,
                    'sell_price': sell_txn.price_per_unit,
                    'sell_amount': sell_txn.total_amount,
                    'average_cost_basis': avg_cost_basis,
                    'cost_basis_total': avg_cost_basis * sell_txn.quantity,
                    'realized_gain_loss': realized_gain_loss,
                    'realized_gain_loss_percent': realized_gain_loss_percent
                })
    
    return realized_gains

def update_asset_holding(user_id, transaction):
    """Update the Asset table based on transaction (for backward compatibility)"""
    # Check if asset exists
    asset = Asset.query.filter_by(user_id=user_id, symbol=transaction.symbol).first()
    
    if transaction.transaction_type == 'BUY':
        if asset:
            # Update existing asset
            new_quantity = asset.quantity + transaction.quantity
            new_total_cost = (asset.quantity * asset.purchase_price) + transaction.total_amount
            asset.quantity = new_quantity
            asset.purchase_price = new_total_cost / new_quantity  # Average cost
            asset.last_updated = datetime.utcnow()
        else:
            # Create new asset
            current_price = get_current_price(transaction.symbol, transaction.asset_type)
            asset = Asset(
                user_id=user_id,
                account_id=transaction.account_id,
                symbol=transaction.symbol,
                name=transaction.name,
                asset_type=transaction.asset_type,
                quantity=transaction.quantity,
                purchase_price=transaction.price_per_unit,
                current_price=current_price,
                currency=transaction.currency,
                notes=f"Created from transaction {transaction.id}"
            )
            db.session.add(asset)
    
    elif transaction.transaction_type == 'SELL' and asset:
        # Update existing asset (reduce quantity)
        asset.quantity -= transaction.quantity
        asset.last_updated = datetime.utcnow()
        
        if asset.quantity <= 0:
            # Remove asset if fully sold
            db.session.delete(asset)

# CSV Import Functions
def parse_firstrade_csv(csv_content):
    """Parse Firstrade CSV transaction format"""
    transactions = []
    reader = csv.DictReader(io.StringIO(csv_content))
    
    for row in reader:
        try:
            # Firstrade CSV format (actual columns):
            # Symbol,Quantity,Price,Action,Description,TradeDate,SettledDate,Interest,Amount,Commission,Fee,CUSIP,RecordType
            
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
            if DATEUTIL_AVAILABLE:
                transaction_date = dateparse(date_str)
            else:
                # Fallback date parsing
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y']:
                    try:
                        transaction_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    continue
            
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
            if DATEUTIL_AVAILABLE:
                try:
                    # If date has " as of " format, take the first date
                    if " as of " in date_str:
                        date_str = date_str.split(" as of ")[0].strip()
                    transaction_date = dateparse(date_str)
                except:
                    continue
            else:
                # Fallback date parsing
                if " as of " in date_str:
                    date_str = date_str.split(" as of ")[0].strip()
                for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                    try:
                        transaction_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
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

@app.route('/api/preview-csv', methods=['POST'])
def preview_csv():
    """Preview transactions from brokerage CSV files without importing"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # Read CSV content
        csv_content = file.read().decode('utf-8')
        
        # Detect format and parse
        csv_format = detect_csv_format(csv_content)
        print(f"Preview - Detected CSV format: {csv_format}")
        
        if csv_format == 'schwab':
            transactions = parse_schwab_csv(csv_content)
        else:  # Default to firstrade
            transactions = parse_firstrade_csv(csv_content)
        
        print(f"Preview - Parsed {len(transactions)} transactions from CSV")
        
        if not transactions:
            return jsonify({'error': 'No valid transactions found in CSV'}), 400
        
        # Prepare preview data (limit to first 10 transactions for display)
        preview_transactions = []
        for trans_data in transactions[:10]:
            preview_transactions.append({
                'date': trans_data['date'].strftime('%Y-%m-%d'),
                'symbol': trans_data['symbol'],
                'type': trans_data['transaction_type'],
                'quantity': trans_data['quantity'],
                'price': trans_data['price'],
                'amount': trans_data['amount'],
                'description': trans_data['description']
            })
        
        return jsonify({
            'success': True,
            'transactions': preview_transactions,
            'total_count': len(transactions),
            'broker': csv_format.title()
        })
        
    except Exception as e:
        print(f"Preview error: {str(e)}")
        return jsonify({'error': f'Failed to preview CSV: {str(e)}'}), 500

@app.route('/api/import-csv', methods=['POST'])
def import_csv():
    """Import transactions from brokerage CSV files"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # Read CSV content
        csv_content = file.read().decode('utf-8')
        
        # Detect format and parse
        csv_format = detect_csv_format(csv_content)
        print(f"Detected CSV format: {csv_format}")
        
        if csv_format == 'schwab':
            transactions = parse_schwab_csv(csv_content)
        else:  # Default to firstrade
            transactions = parse_firstrade_csv(csv_content)
        
        print(f"Parsed {len(transactions)} transactions from CSV")
        if not transactions:
            print("No valid transactions found in CSV")
            return jsonify({'error': 'No valid transactions found in CSV'}), 400
        
        # Get account for import - create broker-specific account if needed
        broker = transactions[0]['broker'] if transactions else csv_format.title()
        account_name = f"{broker} Account"
        
        # Look for existing broker account
        account = Account.query.filter_by(user_id=user_id, name=account_name).first()
        if not account:
            # Create new broker-specific account
            account = Account(
                name=account_name,
                account_type='brokerage',
                currency='USD',
                user_id=user_id
            )
            db.session.add(account)
            print(f"Created new account: {account_name}")
            db.session.commit()
        
        imported_count = 0
        updated_count = 0
        
        for trans_data in transactions:
            try:
                # Check if similar transaction already exists (prevent duplicates)
                existing = Transaction.query.filter_by(
                    user_id=user_id,
                    symbol=trans_data['symbol'],
                    transaction_date=trans_data['date'],
                    quantity=trans_data['quantity'],
                    price_per_unit=trans_data['price']
                ).first()
                
                if existing:
                    continue
                
                # Create new transaction
                transaction = Transaction(
                    user_id=user_id,
                    account_id=account.id,
                    symbol=trans_data['symbol'],
                    name=trans_data.get('name', trans_data['symbol']),
                    asset_type='stock',  # Default to stock for now
                    transaction_type=trans_data['transaction_type'],
                    quantity=trans_data['quantity'],
                    price_per_unit=trans_data['price'],
                    total_amount=trans_data['amount'],
                    currency='USD',  # Assume USD for now
                    transaction_date=trans_data['date'],
                    notes=f"Imported from {trans_data['broker']}: {trans_data['description']}"
                )
                
                db.session.add(transaction)
                imported_count += 1
                
                # Update or create corresponding asset
                asset = Asset.query.filter_by(
                    user_id=user_id,
                    symbol=trans_data['symbol'],
                    account_id=account.id
                ).first()
                
                if transaction.transaction_type == 'BUY':
                    if asset:
                        # Update existing asset
                        old_total_value = asset.quantity * asset.purchase_price
                        new_total_value = trans_data['quantity'] * trans_data['price']
                        total_quantity = asset.quantity + trans_data['quantity']
                        
                        if total_quantity > 0:
                            asset.purchase_price = (old_total_value + new_total_value) / total_quantity
                        asset.quantity = total_quantity
                        asset.last_updated = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Create new asset
                        asset = Asset(
                            user_id=user_id,
                            account_id=account.id,
                            symbol=trans_data['symbol'],
                            name=trans_data.get('name', trans_data['symbol']),
                            asset_type='stock',
                            quantity=trans_data['quantity'],
                            purchase_price=trans_data['price'],
                            currency='USD',
                            purchase_date=trans_data['date'],
                            notes=f"Imported from {trans_data['broker']}"
                        )
                        db.session.add(asset)
                        imported_count += 1
                
                elif transaction.transaction_type == 'SELL' and asset:
                    # Reduce quantity for sells
                    asset.quantity -= trans_data['quantity']
                    asset.last_updated = datetime.utcnow()
                    
                    if asset.quantity <= 0:
                        db.session.delete(asset)
                    
                    updated_count += 1
                
            except Exception as e:
                print(f"Error processing transaction: {trans_data}, Error: {e}")
                continue
        
        db.session.commit()
        
        # Auto-update prices for newly imported assets
        print("Auto-updating prices for imported assets...")
        updated_assets = Asset.query.filter_by(user_id=user_id).all()
        price_update_count = 0
        for asset in updated_assets:
            try:
                print(f"Updating price for {asset.symbol}...")
                price_info = get_asset_info(asset.symbol)
                if price_info['current_price'] > 0:
                    asset.current_price = price_info['current_price']
                    if price_info.get('name') and price_info['name'] != f"{asset.symbol} Stock":
                        asset.name = price_info['name']  # Update name if we got a better one
                    price_update_count += 1
                    print(f"Updated {asset.symbol}: ${price_info['current_price']}")
                else:
                    print(f"No price found for {asset.symbol}")
            except Exception as e:
                print(f"Failed to update price for {asset.symbol}: {e}")
        
        if price_update_count > 0:
            db.session.commit()
            print(f"Updated prices for {price_update_count} assets")
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {imported_count} transactions and updated {updated_count} assets from {csv_format.title()}. Prices updated for {price_update_count} assets.',
            'transactions_imported': imported_count,
            'assets_updated': updated_count,
            'prices_updated': price_update_count,
            'broker': csv_format.title()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to import CSV: {str(e)}'}), 500

@app.route('/api/backup-data')
def backup_data():
    """Export user data as JSON backup"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    
    # Get user data
    user = User.query.get(user_id)
    accounts = Account.query.filter_by(user_id=user_id).all()
    assets = Asset.query.filter_by(user_id=user_id).all()
    
    backup_data = {
        'user': {
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat()
        },
        'accounts': [{
            'name': acc.name,
            'account_type': acc.account_type,
            'currency': acc.currency,
            'created_at': acc.created_at.isoformat()
        } for acc in accounts],
        'assets': [{
            'symbol': asset.symbol,
            'name': asset.name,
            'asset_type': asset.asset_type,
            'quantity': asset.quantity,
            'purchase_price': asset.purchase_price,
            'currency': asset.currency,
            'purchase_date': asset.purchase_date.isoformat(),
            'notes': asset.notes
        } for asset in assets],
        'export_date': datetime.utcnow().isoformat()
    }
    
    return jsonify(backup_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create test user if it doesn't exist
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('testpass123')
            )
            db.session.add(test_user)
            db.session.commit()
            print("Test user created (testuser/testpass123)")
    print("Starting Advanced Asset Tracker...")
    print("Features available:")
    print(f"- yfinance: {'OK' if YFINANCE_AVAILABLE else 'NO'}")
    print(f"- ccxt: {'OK' if CCXT_AVAILABLE else 'NO'}")
    print(f"- pandas: {'OK' if PANDAS_AVAILABLE else 'NO'}")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)