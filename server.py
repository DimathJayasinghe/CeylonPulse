from flask import Flask, jsonify, request, send_from_directory, abort
from api.web_scraper import NewScraper
import tensorflow_hub as hub
import tf_keras as keras
import numpy as np
import zipfile
import json
import os

scraper = NewScraper()
app = Flask(__name__, static_folder='.')

# Load the model once at startup
model_path = os.path.join(os.path.dirname(__file__), 'api', 'news_pestle_model.keras')
with zipfile.ZipFile(model_path, 'r') as z:
    config_data = z.read('config.json')
    config = json.loads(config_data)
loaded_model = keras.Sequential.from_config(config['config'], custom_objects={'KerasLayer': hub.KerasLayer})
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

if __name__ == '__main__':
    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)
