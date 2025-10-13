import pandas as pd
import numpy as np
from datetime import datetime
import os

class CropDataset:
    def __init__(self):
        # Load the CSV dataset
        self.df = None
        self.load_dataset()
        
    def load_dataset(self):
        """Load the crop recommendation dataset from CSV"""
        try:
            csv_path = os.path.join(os.path.dirname(__file__), 'Crop_recommendation.csv')
            self.df = pd.read_csv(csv_path)
            print(f"Dataset loaded successfully with {len(self.df)} records")
        except Exception as e:
            print(f"Error loading dataset: {e}")
            # Fallback to empty dataframe
            self.df = pd.DataFrame()
    
    def get_crop_recommendations(self, nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall):
        """Get crop recommendations based on input parameters using ML approach"""
        if self.df.empty:
            return []
        
        try:
            # Convert inputs to float
            nitrogen = float(nitrogen)
            phosphorus = float(phosphorus)
            potassium = float(potassium)
            temperature = float(temperature)
            humidity = float(humidity)
            ph = float(ph)
            rainfall = float(rainfall)
            
            # Calculate similarity scores for each crop
            crop_scores = {}
            
            # Get unique crops from dataset
            unique_crops = self.df['label'].unique()
            
            for crop in unique_crops:
                crop_data = self.df[self.df['label'] == crop]
                
                # Calculate average values for this crop
                avg_n = crop_data['N'].mean()
                avg_p = crop_data['P'].mean()
                avg_k = crop_data['K'].mean()
                avg_temp = crop_data['temperature'].mean()
                avg_humidity = crop_data['humidity'].mean()
                avg_ph = crop_data['ph'].mean()
                avg_rainfall = crop_data['rainfall'].mean()
                
                # Calculate similarity score (lower is better)
                score = (
                    abs(nitrogen - avg_n) / 100 +
                    abs(phosphorus - avg_p) / 100 +
                    abs(potassium - avg_k) / 100 +
                    abs(temperature - avg_temp) / 30 +
                    abs(humidity - avg_humidity) / 100 +
                    abs(ph - avg_ph) / 7 +
                    abs(rainfall - avg_rainfall) / 200
                )
                
                # Convert to suitability percentage (higher is better)
                suitability = max(0, min(100, int(100 - (score * 20))))
                
                if suitability > 0:
                    crop_scores[crop] = {
                        'suitability': suitability,
                        'avg_values': {
                            'nitrogen': round(avg_n, 1),
                            'phosphorus': round(avg_p, 1),
                            'potassium': round(avg_k, 1),
                            'temperature': round(avg_temp, 1),
                            'humidity': round(avg_humidity, 1),
                            'ph': round(avg_ph, 1),
                            'rainfall': round(avg_rainfall, 1)
                        }
                    }
            
            # Sort by suitability and return top recommendations
            sorted_crops = sorted(crop_scores.items(), key=lambda x: x[1]['suitability'], reverse=True)
            
            recommendations = []
            crop_info = self.get_crop_info()
            
            for crop_name, data in sorted_crops[:6]:  # Top 6 recommendations
                crop_details = crop_info.get(crop_name, {})
                
                recommendations.append({
                    'name': crop_name.title(),
                    'suitability': data['suitability'],
                    'expected_yield': crop_details.get('yield_range', [20, 40]),
                    'expected_profit': crop_details.get('profit', 45000),
                    'growth_duration': crop_details.get('duration', 90),
                    'water_requirement': crop_details.get('water', 'Medium'),
                    'fertilizer_npk': crop_details.get('npk', '10:26:26'),
                    'category': crop_details.get('category', 'Crop'),
                    'avg_requirements': data['avg_values']
                })
            
            return recommendations
            
        except Exception as e:
            print(f"Error in get_crop_recommendations: {e}")
            return []
    
    def get_crop_info(self):
        """Return additional information about crops"""
        return {
            'rice': {
                'category': 'Cereal',
                'yield_range': [45, 60],
                'profit': 75000,
                'duration': 120,
                'water': 'High',
                'npk': '10:26:26'
            },
            'maize': {
                'category': 'Cereal',
                'yield_range': [30, 50],
                'profit': 45000,
                'duration': 100,
                'water': 'Medium',
                'npk': '18:46:0'
            },
            'chickpea': {
                'category': 'Pulse',
                'yield_range': [8, 15],
                'profit': 35000,
                'duration': 110,
                'water': 'Low',
                'npk': '18:46:0'
            },
            'kidneybeans': {
                'category': 'Pulse',
                'yield_range': [6, 12],
                'profit': 40000,
                'duration': 90,
                'water': 'Medium',
                'npk': '12:32:16'
            },
            'pigeonpeas': {
                'category': 'Pulse',
                'yield_range': [10, 18],
                'profit': 38000,
                'duration': 150,
                'water': 'Low',
                'npk': '12:32:16'
            },
            'mothbeans': {
                'category': 'Pulse',
                'yield_range': [5, 10],
                'profit': 25000,
                'duration': 75,
                'water': 'Very Low',
                'npk': '10:20:10'
            },
            'mungbean': {
                'category': 'Pulse',
                'yield_range': [8, 12],
                'profit': 32000,
                'duration': 65,
                'water': 'Medium',
                'npk': '12:32:16'
            },
            'blackgram': {
                'category': 'Pulse',
                'yield_range': [6, 10],
                'profit': 35000,
                'duration': 80,
                'water': 'Medium',
                'npk': '12:32:16'
            },
            'lentil': {
                'category': 'Pulse',
                'yield_range': [8, 15],
                'profit': 30000,
                'duration': 95,
                'water': 'Low',
                'npk': '18:46:0'
            },
            'pomegranate': {
                'category': 'Fruit',
                'yield_range': [100, 150],
                'profit': 150000,
                'duration': 365,
                'water': 'Medium',
                'npk': '19:19:19'
            },
            'banana': {
                'category': 'Fruit',
                'yield_range': [200, 300],
                'profit': 120000,
                'duration': 365,
                'water': 'High',
                'npk': '8:10:8'
            },
            'mango': {
                'category': 'Fruit',
                'yield_range': [80, 120],
                'profit': 100000,
                'duration': 365,
                'water': 'Medium',
                'npk': '10:10:20'
            },
            'grapes': {
                'category': 'Fruit',
                'yield_range': [150, 250],
                'profit': 200000,
                'duration': 365,
                'water': 'Medium',
                'npk': '10:10:10'
            },
            'watermelon': {
                'category': 'Fruit',
                'yield_range': [200, 400],
                'profit': 80000,
                'duration': 90,
                'water': 'High',
                'npk': '8:24:24'
            },
            'muskmelon': {
                'category': 'Fruit',
                'yield_range': [150, 300],
                'profit': 70000,
                'duration': 85,
                'water': 'High',
                'npk': '8:24:24'
            },
            'apple': {
                'category': 'Fruit',
                'yield_range': [100, 200],
                'profit': 180000,
                'duration': 365,
                'water': 'Medium',
                'npk': '10:10:10'
            },
            'orange': {
                'category': 'Fruit',
                'yield_range': [120, 180],
                'profit': 90000,
                'duration': 365,
                'water': 'Medium',
                'npk': '8:8:8'
            },
            'papaya': {
                'category': 'Fruit',
                'yield_range': [300, 500],
                'profit': 110000,
                'duration': 365,
                'water': 'High',
                'npk': '14:14:14'
            },
            'coconut': {
                'category': 'Tree Crop',
                'yield_range': [40, 80],
                'profit': 85000,
                'duration': 365,
                'water': 'High',
                'npk': '8:2:12'
            },
            'cotton': {
                'category': 'Cash Crop',
                'yield_range': [15, 25],
                'profit': 65000,
                'duration': 180,
                'water': 'Medium',
                'npk': '17:17:17'
            },
            'jute': {
                'category': 'Fiber Crop',
                'yield_range': [20, 30],
                'profit': 40000,
                'duration': 120,
                'water': 'High',
                'npk': '10:5:5'
            },
            'coffee': {
                'category': 'Beverage Crop',
                'yield_range': [8, 15],
                'profit': 120000,
                'duration': 365,
                'water': 'Medium',
                'npk': '10:5:20'
            }
        }
    
    def get_input_ranges(self):
        """Get the input parameter ranges from the dataset"""
        if self.df.empty:
            return {}
        
        return {
            'nitrogen': {'min': int(self.df['N'].min()), 'max': int(self.df['N'].max()), 'avg': int(self.df['N'].mean())},
            'phosphorus': {'min': int(self.df['P'].min()), 'max': int(self.df['P'].max()), 'avg': int(self.df['P'].mean())},
            'potassium': {'min': int(self.df['K'].min()), 'max': int(self.df['K'].max()), 'avg': int(self.df['K'].mean())},
            'temperature': {'min': int(self.df['temperature'].min()), 'max': int(self.df['temperature'].max()), 'avg': int(self.df['temperature'].mean())},
            'humidity': {'min': int(self.df['humidity'].min()), 'max': int(self.df['humidity'].max()), 'avg': int(self.df['humidity'].mean())},
            'ph': {'min': round(self.df['ph'].min(), 1), 'max': round(self.df['ph'].max(), 1), 'avg': round(self.df['ph'].mean(), 1)},
            'rainfall': {'min': int(self.df['rainfall'].min()), 'max': int(self.df['rainfall'].max()), 'avg': int(self.df['rainfall'].mean())}
        }

# Initialize dataset
crop_dataset = CropDataset()
