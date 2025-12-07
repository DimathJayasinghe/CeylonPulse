from web_scraper import NewScraper
import pandas as pd
import tensorflow_hub as hub
import tf_keras as keras
import numpy as np
import os
import zipfile

model_path = os.path.join(os.path.dirname(__file__), "news_pestle_model.keras")

# Extract and load keras model
with zipfile.ZipFile(model_path, 'r') as z:
    config_data = z.read('config.json')
    import json
    config = json.loads(config_data)

# Rebuild model from config only (without weights)
loaded_model = keras.Sequential.from_config(config['config'], custom_objects={'KerasLayer': hub.KerasLayer})
print("WARNING: Model loaded without weights - predictions will be random!")

scraper = NewScraper()
df = scraper.scrape_page(100)
preds = loaded_model.predict(df['headline'])
pred_classes = np.argmax(preds, axis=1)
class_names = ['Economic', 'Environmental', 'Legal', 'Political', 'Social', 'Technological']
pred_classes = [class_names[i] for i in pred_classes]
df['category'] = pred_classes
print(df[['headline', 'category']].head())