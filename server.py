from flask import Flask, jsonify, request, send_from_directory
from api.web_scraper import NewScraper
scraper = NewScraper()
import os

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/api/news', methods=['GET'])
def get_news():
    """API endpoint to fetch news with optional limit parameter"""
    try:
        # Get limit from query params, default to 10, max 1000
        limit = request.args.get('limit', default=10, type=int)
        limit = max(1, min(1000, limit))  # Clamp between 1 and 50
        
        # Create scraper and fetch news
        news_items = scraper.scrape_page(limit)
        
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

if __name__ == '__main__':
    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)
