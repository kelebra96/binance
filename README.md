# Crypto Monitor with Bollinger Bands and Moving Average

A real-time cryptocurrency price monitoring dashboard built with Streamlit. Features candlestick charts with technical indicators (Bollinger Bands and 20-period Moving Average) and automated buy/sell signal detection.

## Features

- Real-time cryptocurrency price monitoring
- Interactive candlestick charts with Plotly
- Technical indicators:
  - Bollinger Bands (Upper and Lower)
  - 20-period Moving Average (MA20)
- Automated buy/sell signal detection
- Buy Signal: When close price touches or goes below the lower Bollinger Band
- Sell Signal: When close price touches or goes above the upper Bollinger Band
- Auto-refresh capability for live updates
- Clean and responsive UI

## Prerequisites

- Python 3.8+
- MongoDB server running locally or remotely
- Data pre-populated in MongoDB with the following schema:

```json
{
  "open_time": "2024-01-01 00:00:00",
  "open": 42000.00,
  "high": 42500.00,
  "low": 41800.00,
  "close": 42300.00,
  "Upper": 43000.00,
  "Lower": 41500.00,
  "MA20": 42200.00
}
```

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

## Usage

### Run the application

```bash
streamlit run main.py
```

The application will open in your default browser at `http://localhost:8501`.

### Using the Dashboard

1. **Enter Crypto Symbol**: Input the cryptocurrency trading pair (e.g., BTCUSDT, ETHUSDT)
2. **Select Interval**: Choose the timeframe for candlestick data (1m, 5m, 15m, 1h, 1d)
3. **Get Data**: Click the button to fetch and display data
4. **Auto-refresh**: Enable the checkbox to automatically update the dashboard every 60 seconds

### Interpreting Signals

- **Green Triangle Up (🟢)**: Buy Signal - Price touched/crossed below the lower Bollinger Band
- **Red Triangle Down (🔴)**: Sell Signal - Price touched/crossed above the upper Bollinger Band

## Project Structure

```
binance/
├── main.py              # Main Streamlit application
├── requirements.txt     # Python dependencies
├── .env.example        # Example environment variables
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

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

### MongoDB Connection Error

If you see "Error connecting to MongoDB":
- Ensure MongoDB is running: `sudo systemctl status mongod`
- Check the connection URI in `.env`
- Verify network connectivity and firewall settings

### No Data Available

If you see "No data available in MongoDB":
- Check that your MongoDB collection has data
- Verify the database and collection names in `.env` match your MongoDB setup
- Ensure the data has the required columns: `open_time`, `open`, `high`, `low`, `close`, `Upper`, `Lower`, `MA20`

### Missing Columns Error

If you see "Dados incompletos no MongoDB":
- Your MongoDB documents are missing required fields
- Ensure all documents have: `open_time`, `open`, `high`, `low`, `close`, `Upper`, `Lower`, `MA20`

## Dependencies

- **streamlit** (>=1.28.0): Web application framework
- **pandas** (>=2.0.0): Data manipulation
- **plotly** (>=5.17.0): Interactive charts
- **pymongo** (>=4.5.0): MongoDB driver
- **python-dotenv** (>=1.0.0): Environment variable management

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
