# Crypto Monitor with Bollinger Bands and Moving Average

A real-time cryptocurrency price monitoring dashboard built with Streamlit. Connects directly to **Binance API** to fetch live market data, calculates technical indicators (Bollinger Bands and 20-period Moving Average), and provides automated buy/sell signal detection.

## Features

### 📊 Price Monitor
- 🔴 **LIVE Data from Binance API** - Real-time cryptocurrency prices
- 💾 **MongoDB Integration** - Save and retrieve historical data
- 📊 **Interactive Candlestick Charts** with Plotly
- 📈 **Technical Indicators**:
  - Bollinger Bands (Upper and Lower)
  - 20-period Moving Average (MA20)
- 🎯 **Automated Trading Signals**:
  - Buy Signal: When close price touches or goes below the lower Bollinger Band
  - Sell Signal: When close price touches or goes above the upper Bollinger Band
- 🔄 **Auto-refresh** capability for live updates
- 🛠️ **Flexible Data Sources**: Choose between Binance API (live) or MongoDB (saved data)

### 🎯 Trading Simulator (NEW!)
- 💰 **Paper Trading** - Practice trading without real money
- 📝 **Multiple Order Types**:
  - Market Orders (instant execution)
  - Limit Orders (execute at specific price)
  - Stop Loss (automatic sell to limit losses)
  - Take Profit (automatic sell to secure profits)
- 📊 **Portfolio Management**:
  - Track balance and positions
  - Real-time P&L calculation
  - Win rate and statistics
- 📈 **Performance Dashboard**:
  - Total P&L (profit & loss)
  - Win/loss ratio
  - Best/worst trades
  - Trade history with charts
- 💾 **MongoDB Persistence** - Your simulator state is saved automatically
- 🎓 **Risk-Free Learning** - Perfect for testing strategies!

## Prerequisites

- Python 3.8+
- Internet connection (for Binance API)
- MongoDB server (optional - only needed if you want to save historical data)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd binance
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` with your MongoDB configuration:

```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=crypto_db
MONGODB_COLLECTION=crypto_data
DEFAULT_CRYPTO_SYMBOL=BTCUSDT
DEFAULT_INTERVAL=1m
DATA_LIMIT=100
AUTO_REFRESH_INTERVAL=60
```

### 5. Ensure MongoDB is running

Make sure your MongoDB service is running and accessible at the URI specified in `.env`.

```bash
# Check if MongoDB is running
mongosh --eval "db.adminCommand('ping')"
```

### 6. Populate MongoDB with sample data (Optional)

If you don't have data in MongoDB yet, use the provided script to generate sample data:

```bash
# Check your MongoDB data structure
python check_mongodb.py

# Populate with sample data (100 candlesticks with indicators)
python populate_sample_data.py
```

This will create realistic cryptocurrency data with Bollinger Bands and Moving Average for testing.

## Usage

### Run the application

```bash
streamlit run main.py
```

The application will open in your default browser at `http://localhost:8501`.

### Using the Price Monitor

1. **Select Page**: In the sidebar, choose "📊 Monitor de Preços"
2. **Enter Crypto Symbol**: Input the cryptocurrency trading pair (e.g., BTCUSDT, ETHUSDT, BNBUSDT)
3. **Select Interval**: Choose the timeframe for candlestick data (1m, 5m, 15m, 1h, 1d)
4. **Choose Data Source**:
   - **Binance API (Live)**: Fetches real-time data directly from Binance (recommended)
   - **MongoDB (Saved Data)**: Uses historical data saved in your MongoDB
5. **Get Data**: Click the button to fetch and display data
6. **Auto-refresh**: Enable the checkbox to automatically update the dashboard every 60 seconds

### Using the Trading Simulator

1. **Select Page**: In the sidebar, choose "🎯 Trading Simulator"
2. **Dashboard Tab**: View your portfolio, open positions, pending orders, and statistics
3. **New Order Tab**: Create trading orders
   - Enter symbol (e.g., BTCUSDT)
   - Choose order type (Market, Limit, Stop Loss, Take Profit)
   - Select side (BUY or SELL)
   - Enter quantity
   - Set price (for limit/stop orders)
   - Click "Send Order"
4. **History Tab**: Review all executed trades and orders
5. **Update Prices**: Click "🔄 Atualizar Preço" to fetch latest prices and process pending orders
6. **Save Progress**: Your simulator state is automatically saved to MongoDB

**Trading Simulator Workflow Example:**
```
1. Start with $10,000 USDT balance
2. Update BTC price → $43,500
3. Create Market BUY order → 0.1 BTC
4. Position opens: 0.1 BTC @ $43,500
5. Set Stop Loss @ $42,000 (limit losses)
6. Set Take Profit @ $45,000 (secure profits)
7. Price updates trigger automatic execution
8. View P&L and statistics in Dashboard
```

### Data Sources Explained

**🔴 Binance API (Live)** - Recommended
- Fetches real-time market data from Binance
- Always up-to-date
- No MongoDB required (but data is auto-saved to MongoDB if available)
- Requires internet connection

**💾 MongoDB (Saved Data)**
- Uses historical data from your local MongoDB
- Useful for backtesting or offline analysis
- Requires MongoDB running with data
- Use `collect_data.py` to populate MongoDB continuously

### Interpreting Signals

- **Green Triangle Up (🟢)**: Buy Signal - Price touched/crossed below the lower Bollinger Band
- **Red Triangle Down (🔴)**: Sell Signal - Price touched/crossed above the upper Bollinger Band

## Project Structure

```
binance/
├── main.py                    # Main Streamlit application with navigation
├── pages_trading.py           # Trading Simulator UI (NEW!)
├── trading_simulator.py       # Trading logic and order management (NEW!)
├── binance_api.py             # Binance API client and indicators calculation
├── collect_data.py            # Data collection script (run in background)
├── check_mongodb.py           # MongoDB diagnostic tool
├── populate_sample_data.py    # Script to insert sample data
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

### Core Files

**main.py**
Main Streamlit application with multi-page navigation. Hosts both Price Monitor and Trading Simulator.

**pages_trading.py** (NEW!)
Trading Simulator UI with tabs for Dashboard, New Orders, and History. Handles user interactions and displays portfolio state.

**trading_simulator.py** (NEW!)
Core trading engine with order management, portfolio tracking, P&L calculation, and statistics. Supports Market, Limit, Stop Loss, and Take Profit orders.

**binance_api.py**
Module for connecting to Binance API, fetching klines (candlestick data), and calculating technical indicators (Bollinger Bands, MA20).

**collect_data.py**
Background script for continuously collecting data from Binance and saving to MongoDB. Useful for building historical datasets.

### Helper Scripts

**check_mongodb.py**
Diagnostic tool that checks your MongoDB connection and data structure. Use this when troubleshooting data issues.

**populate_sample_data.py**
Generates and inserts 100 sample candlestick records with Bollinger Bands and Moving Average. Perfect for testing the application.

## Advanced Usage

### Collecting Data Continuously

To build a historical dataset, run the `collect_data.py` script in the background:

```bash
# Collect BTCUSDT 1-minute candles, update every 60 seconds
python collect_data.py --symbol BTCUSDT --interval 1m --update-interval 60

# Collect ETHUSDT 5-minute candles
python collect_data.py --symbol ETHUSDT --interval 5m

# Run once (no loop)
python collect_data.py --symbol BTCUSDT --interval 1m --once
```

**Options:**
- `--symbol`: Cryptocurrency symbol (default: BTCUSDT)
- `--interval`: Candle interval (1m, 5m, 15m, 1h, 1d)
- `--limit`: Number of candles to fetch (default: 100, max: 1000)
- `--update-interval`: Seconds between updates (default: 60)
- `--once`: Run once and exit (no continuous loop)

**Example: Run in background**
```bash
# Windows
start /B python collect_data.py

# Linux/Mac
nohup python collect_data.py &
```

The script will:
1. Connect to Binance API
2. Fetch candlestick data
3. Calculate Bollinger Bands and MA20
4. Save to MongoDB
5. Repeat every N seconds

Logs are saved to `collect_data.log`.

## Configuration

All configuration is done through environment variables in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017/` |
| `MONGODB_DATABASE` | Database name | `crypto_db` |
| `MONGODB_COLLECTION` | Collection name | `crypto_data` |
| `DEFAULT_CRYPTO_SYMBOL` | Default trading pair | `BTCUSDT` |
| `DEFAULT_INTERVAL` | Default timeframe | `1m` |
| `DATA_LIMIT` | Number of data points to fetch | `100` |
| `AUTO_REFRESH_INTERVAL` | Refresh interval in seconds | `60` |

## Technical Indicators

### Bollinger Bands

Bollinger Bands consist of:
- **Middle Band**: 20-period Simple Moving Average (MA20)
- **Upper Band**: MA20 + (2 × standard deviation)
- **Lower Band**: MA20 - (2 × standard deviation)

The bands widen during high volatility and narrow during low volatility periods.

### Trading Signals

- **Buy Signal**: Triggered when the close price is at or below the lower Bollinger Band, indicating potential oversold conditions
- **Sell Signal**: Triggered when the close price is at or above the upper Bollinger Band, indicating potential overbought conditions

**Note**: These signals are for informational purposes only and should not be considered financial advice. Always do your own research before making trading decisions.

## Troubleshooting

### KeyError: 'close' (or other column name)

**Symptom:** Application crashes with `KeyError: 'close'` or similar error.

**Cause:** Your MongoDB data doesn't have the required column structure.

**Solution:**
```bash
# Step 1: Diagnose the problem
python check_mongodb.py

# Step 2: If data is missing or incorrect, populate with sample data
python populate_sample_data.py

# Step 3: Run the application
streamlit run main.py
```

### MongoDB Connection Error

If you see "Error connecting to MongoDB":

**Windows:**
```bash
# Check if MongoDB is running
tasklist | findstr mongo

# Start MongoDB service
net start MongoDB
```

**Linux/Mac:**
```bash
# Check MongoDB status
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod
```

- Verify the connection URI in `.env` is correct
- Check firewall settings

### No Data Available

If you see "No data available in MongoDB":

1. **Check MongoDB has data:**
   ```bash
   python check_mongodb.py
   ```

2. **Populate with sample data:**
   ```bash
   python populate_sample_data.py
   ```

3. **Verify database/collection names in `.env`:**
   - `MONGODB_DATABASE=crypto_db`
   - `MONGODB_COLLECTION=crypto_data`

### Missing Columns Error

If you see "Dados incompletos no MongoDB" or "Colunas ausentes":

**Required columns in MongoDB documents:**
- `open_time` (string): Timestamp in format "YYYY-MM-DD HH:MM:SS"
- `open` (number): Opening price
- `high` (number): Highest price
- `low` (number): Lowest price
- `close` (number): Closing price
- `Upper` (number): Upper Bollinger Band
- `Lower` (number): Lower Bollinger Band
- `MA20` (number): 20-period Moving Average

**Solution:** Use `populate_sample_data.py` to create correctly structured data.

## Dependencies

- **streamlit** (>=1.28.0): Web application framework
- **pandas** (>=2.0.0): Data manipulation and DataFrames
- **plotly** (>=5.17.0): Interactive charts and candlestick visualization
- **pymongo** (>=4.5.0): MongoDB driver
- **python-dotenv** (>=1.0.0): Environment variable management
- **requests** (>=2.31.0): HTTP client for Binance API
- **numpy** (>=1.24.0): Numerical computing for indicators calculation

## Development

### Logging

The application uses Python's built-in logging module. Logs are printed to the console with timestamps.

To change log level, edit `main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more verbose logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Code Structure

The application follows a modular structure with separate functions:

- `get_mongodb_client()`: Creates and tests MongoDB connection
- `fetch_data_from_mongodb()`: Retrieves data from MongoDB
- `identify_trade_signals()`: Identifies buy/sell signals
- `create_candlestick_chart()`: Creates the interactive chart

All functions include type hints and docstrings for better maintainability.

## Security Notes

- Never commit `.env` files to version control
- Use strong authentication for MongoDB in production
- Consider using MongoDB Atlas or other managed services for production
- Implement rate limiting for production deployments

## License

This project is provided as-is for educational purposes.

## Contributing

Feel free to open issues or submit pull requests for improvements.

## Disclaimer

This software is for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses incurred from using this software. Always consult with a financial advisor before making investment decisions.
