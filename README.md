# Asset Tracker

A comprehensive web-based asset tracking application that allows users to monitor their investment portfolios, cash holdings, cryptocurrencies, and real assets across multiple accounts and currencies.

## Features

### 🔐 User Management
- Multi-user support with authentication
- User switching functionality
- Secure password hashing

### 💼 Asset Categories
- **Investment Portfolio**: Stocks, ETFs, bonds, mutual funds
- **Cash Holdings**: Multi-currency bank accounts
- **Cryptocurrency**: Various crypto assets
- **Real Assets**: Real estate, commodities, collectibles

### 🏦 Account Management
- Multiple account support (401k, IRA, brokerage, bank accounts, crypto exchanges)
- Multi-currency support
- Account categorization

### 📊 Analytics & Visualization
- Portfolio allocation pie charts
- Account distribution charts
- Real-time portfolio value tracking
- Gain/loss calculations with percentages
- Asset performance monitoring

### 📈 Real-time Data
- Live stock price updates via Yahoo Finance
- Cryptocurrency price fetching
- Automatic portfolio value calculations

### 🌐 Multi-Currency Support
- Support for major currencies (USD, EUR, GBP, JPY, CAD, AUD)
- Currency-specific price display

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (jQuery)
- **Charts**: Chart.js
- **APIs**: Yahoo Finance (yfinance), CoinGecko

## Installation

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Quick Start (Simple Version)

For a quick start with minimal dependencies:

1. **Install minimal dependencies**
   ```bash
   pip install flask flask-cors requests
   ```

2. **Run the simple version**
   ```bash
   python simple_app.py
   ```

3. **Or use the batch file (Windows)**
   ```bash
   run_simple.bat
   ```

### Full Version Setup

For the complete version with all features:

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the full application**
   ```bash
   python app.py
   ```

3. **Or use the batch file (Windows)**
   ```bash
   run.bat
   ```

4. **Access the application**
   - Open your web browser
   - Navigate to: `http://localhost:5000`

### Version Differences

**Simple Version (`simple_app.py`)**
- Minimal dependencies (Flask, Flask-CORS, Requests)
- File-based JSON storage (no database required)
- Basic price fetching with fallback to demo prices
- Perfect for testing and light usage
- Quick setup and deployment

**Full Version (`app.py`)**
- Complete feature set with SQLAlchemy database
- Advanced price fetching with yfinance and ccxt
- Database migrations and proper data relationships
- Production-ready with better error handling
- Suitable for serious portfolio tracking

## Usage Guide

### Getting Started

1. **Create an Account**
   - Click "Create Account" on the login page
   - Fill in username, email, and password
   - Click "Create Account"

2. **Login**
   - Enter your username and password
   - Click "Login"

### Managing Accounts

1. **Add Investment/Bank Accounts**
   - Go to the "Accounts" tab
   - Click "Add Account"
   - Enter account name, type, and currency
   - Click "Add Account"

### Adding Assets

1. **Add Stocks**
   - Go to the "Assets" tab
   - Click "Add Asset"
   - Select "Stock" as asset type
   - Enter ticker symbol (e.g., AAPL, GOOGL)
   - Click "Search" to auto-fill details
   - Enter quantity and purchase price
   - Select account (optional)
   - Click "Add Asset"

2. **Add Cryptocurrency**
   - Select "Cryptocurrency" as asset type
   - Enter crypto symbol (e.g., bitcoin, ethereum)
   - Fill in quantity and purchase price
   - Click "Add Asset"

3. **Add Cash Holdings**
   - Select "Cash" as asset type
   - Enter description (e.g., "Savings Account")
   - Enter amount and currency
   - Click "Add Asset"

4. **Add Real Assets**
   - Select "Real Estate" or "Other" as asset type
   - Enter asset name and estimated value
   - Add notes if needed
   - Click "Add Asset"

### Dashboard Features

1. **Portfolio Overview**
   - View total portfolio value
   - See total gains/losses
   - Monitor asset count

2. **Charts**
   - Asset distribution pie chart
   - Account distribution pie chart

3. **Price Updates**
   - Click "Update Prices" to refresh stock and crypto prices
   - Automatic calculation of current portfolio value

### User Switching

1. **Switch Between Users**
   - Click "Switch User" in the header
   - Select from the list of registered users
   - Dashboard updates to show selected user's data

## API Endpoints

### Authentication
- `POST /api/users` - Create new user
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `POST /api/switch-user/<user_id>` - Switch to different user

### Accounts
- `GET /api/accounts` - Get user's accounts
- `POST /api/accounts` - Create new account

### Assets
- `GET /api/assets` - Get user's assets
- `POST /api/assets` - Add new asset
- `GET /api/search-symbol/<symbol>` - Search stock symbol

### Portfolio
- `GET /api/portfolio-summary` - Get portfolio summary
- `POST /api/update-prices` - Update asset prices

## Database Schema

### Users Table
- id, username, email, password_hash, created_at

### Accounts Table
- id, user_id, name, account_type, currency, created_at

### Assets Table
- id, user_id, account_id, symbol, name, asset_type, quantity, purchase_price, current_price, currency, purchase_date, last_updated, notes

### Price History Table
- id, symbol, price, timestamp, asset_type

## Supported Asset Types

- **stock**: Publicly traded stocks
- **crypto**: Cryptocurrencies
- **cash**: Cash holdings
- **real_estate**: Real estate properties
- **commodity**: Commodities (gold, silver, etc.)
- **other**: Other assets

## Supported Account Types

- **investment**: Investment accounts (brokerage, IRA, 401k)
- **bank**: Bank accounts
- **crypto**: Cryptocurrency exchanges/wallets
- **retirement**: Retirement accounts
- **other**: Other account types

## Price Data Sources

- **Stocks**: Yahoo Finance API via yfinance library
- **Crypto**: CoinGecko API (free tier)

## Security Features

- Password hashing using Werkzeug security
- Session-based authentication
- SQL injection prevention via SQLAlchemy ORM
- CORS protection

## Future Enhancements

- [ ] Import transactions from CSV files
- [ ] Historical price charts
- [ ] Performance analytics
- [ ] Goal tracking
- [ ] Mobile responsive design improvements
- [ ] Real-time price updates via WebSocket
- [ ] Portfolio rebalancing suggestions
- [ ] Tax reporting features
- [ ] API rate limiting
- [ ] User roles and permissions

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

2. **Price updates not working**
   - Check internet connection
   - Verify ticker symbols are correct
   - Some stocks may not be available in Yahoo Finance

3. **Database errors**
   - Delete `asset_tracker.db` file and restart the app to reset database

### Support

For issues or questions, please check the code comments or modify the application according to your needs.

## License

This project is open source and available under the MIT License.