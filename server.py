from flask import Flask, jsonify, request, send_from_directory, abort
from api.web_scraper import NewScraper, CSEScraper, EconomicIndicatorsScraper
import tensorflow_hub as hub
import tf_keras as keras
import numpy as np
import zipfile
import json
import os
import yfinance as yf

scraper = NewScraper()
cse_scraper = CSEScraper()
econ_scraper = EconomicIndicatorsScraper()
app = Flask(__name__, static_folder='.')

# Load the model once at startup
model_path = os.path.join(os.path.dirname(__file__), 'api', 'news_pestle_model.keras')
with zipfile.ZipFile(model_path, 'r') as z:
    config_data = z.read('config.json')
    config = json.loads(config_data)
# loaded_model = keras.Sequential.from_config(config['config'], custom_objects={'KerasLayer': hub.KerasLayer})
print("Model loaded successfully (without weights - using for demo)")

# Define the pages directory
PAGES_DIR = os.path.join(os.path.dirname(__file__), 'pages')

@app.route('/')
def index():
    """Serve the main HTML page from pages folder"""
    return send_from_directory(PAGES_DIR, 'index.html')

@app.route('/<path:page_name>')
def serve_page(page_name):
    """Serve requested pages from the pages folder"""
    # Skip API routes - they should be handled by API endpoints
    if page_name.startswith('api/'):
        abort(404)
    
    try:
        # If no extension, assume .html
        if '.' not in page_name:
            page_name = f"{page_name}.html"
        
        # Check if file exists in pages directory
        file_path = os.path.join(PAGES_DIR, page_name)
        if os.path.isfile(file_path):
            return send_from_directory(PAGES_DIR, page_name)
        else:
            abort(404)
    except Exception:
        abort(404)

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error handler"""
    return send_from_directory(PAGES_DIR, '404.html'), 404

@app.route('/api/news', methods=['GET'])
def get_news():
    """API endpoint to fetch news with optional limit parameter"""
    try:
        # Get limit from query params, default to 10, max 1000
        limit = request.args.get('limit', default=10, type=int)
        limit = max(1, min(1000, limit))  # Clamp between 1 and 1000
        
        # Scrape news
        df = scraper.scrape_page(limit)
        
        # Analyze news with model
        preds = loaded_model.predict(df['headline'], verbose=0)
        pred_classes = np.argmax(preds, axis=1)
        class_names = ['Economic', 'Environmental', 'Legal', 'Political', 'Social', 'Technological']
        df['category'] = [class_names[i] for i in pred_classes]
        # Convert to list of dicts for JSON response
        news_items = df.to_dict('records')
        
        # Return JSON response
        return jsonify({
            'status': 'success',
            'count': len(news_items),
            'items': news_items
        }), 200
        
    except Exception as e:
        # Handle errors and return error response
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/currency', methods=['GET'])
def get_currency():
    """API endpoint to fetch USD/LKR exchange rate data"""
    try:
        # Get period from query params (default 1 month)
        period = request.args.get('period', default='1mo', type=str)
        
        # Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
        valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']
        if period not in valid_periods:
            period = '1mo'
        
        # Fetch USD/LKR data from Yahoo Finance
        ticker = yf.Ticker('LKR=X')
        hist = ticker.history(period=period)
        
        if hist.empty:
            return jsonify({
                'status': 'error',
                'message': 'Unable to fetch currency data for the selected period.'
            }), 200
        
        # Convert to list of dicts
        data = []
        for date, row in hist.iterrows():
            # Handle NaN values
            close_val = float(row['Close']) if not np.isnan(row['Close']) else 0
            open_val = float(row['Open']) if not np.isnan(row['Open']) else close_val
            high_val = float(row['High']) if not np.isnan(row['High']) else close_val
            low_val = float(row['Low']) if not np.isnan(row['Low']) else close_val
            volume_val = int(row['Volume']) if not np.isnan(row['Volume']) and row['Volume'] > 0 else 0
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'rate': round(close_val, 4),
                'open': round(open_val, 4),
                'high': round(high_val, 4),
                'low': round(low_val, 4),
                'volume': volume_val
            })
        
        # Filter out entries with 0 values
        data = [d for d in data if d['rate'] > 0]
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No valid data available for the selected period.'
            }), 200
        
        # Get current rate
        current_rate = data[-1]['rate']
        previous_rate = data[-2]['rate'] if len(data) > 1 else current_rate
        change = current_rate - previous_rate
        change_percent = (change / previous_rate * 100) if previous_rate != 0 else 0
        
        return jsonify({
            'status': 'success',
            'current_rate': current_rate,
            'change': round(change, 4),
            'change_percent': round(change_percent, 2),
            'period': period,
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stock', methods=['GET'])
def get_stock():
    """API endpoint to fetch ASPI (Colombo Stock Exchange All Share Price Index) data"""
    try:
        # Get period from query params (default 1 month)
        period = request.args.get('period', default='1mo', type=str)
        
        # Map our periods to CSE periods
        period_map = {
            '1d': '1D',
            '5d': '1W',
            '1mo': '1M',
            '3mo': '1Q',
            '6mo': '1Q',  # CSE doesn't have 6mo, use 1Q
            '1y': '1Y',
            '2y': '1Y',   # CSE doesn't have 2y, use 1Y
            '5y': '1Y',   # CSE doesn't have 5y, use 1Y
            'max': '1Y'
        }
        
        cse_period = period_map.get(period, '1M')
        
        # Fetch data from CSE
        data = cse_scraper.get_aspi_data(cse_period)
        
        if not data or len(data) == 0:
            return jsonify({
                'status': 'error',
                'message': 'Unable to fetch ASPI data from Colombo Stock Exchange. Please try again later.'
            }), 200
        
        # Get current index
        current_index = data[-1]['index']
        previous_index = data[-2]['index'] if len(data) > 1 else current_index
        change = current_index - previous_index
        change_percent = (change / previous_index * 100) if previous_index != 0 else 0
        
        return jsonify({
            'status': 'success',
            'current_index': current_index,
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'period': period,
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/economic', methods=['GET'])
def get_economic_indicators():
    """API endpoint to fetch economic indicators (GDP, CCPI, NCPI)"""
    try:
        # Fetch data from Trading Economics
        data = econ_scraper.fetch_economic_indicators()
        
        if not data or len(data) == 0:
            return jsonify({
                'status': 'error',
                'message': 'Unable to fetch economic indicators. Please try again later.'
            }), 200
        
        return jsonify({
            'status': 'success',
            'count': len(data),
            'indicators': data
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)
