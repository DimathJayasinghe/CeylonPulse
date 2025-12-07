from flask import Flask, jsonify, request, send_from_directory, abort
from api.web_scraper import NewScraper
import os

scraper = NewScraper()
app = Flask(__name__, static_folder='.')

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
