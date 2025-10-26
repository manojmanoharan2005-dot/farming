import pandas as pd
import numpy as np
from typing import List, Dict, Any
import os

class FertilizerDataset:
    def __init__(self):
        # Load the actual fertilizer dataset
        self.dataset = self._load_dataset()
        self.fertilizer_database = self._create_fertilizer_database()
        self.crop_nutrient_mapping = self._create_crop_nutrient_mapping()
    
    def _load_dataset(self) -> pd.DataFrame:
        """Load fertilizer recommendation dataset from CSV"""
        try:
            dataset_path = os.path.join(os.path.dirname(__file__), 'fertilizer_recommendation_dataset.csv')
            if os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
                # Clean column names
                df.columns = df.columns.str.strip()
                return df
            else:
                print(f"Dataset file not found: {dataset_path}")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading fertilizer dataset: {e}")
            return pd.DataFrame()
    
    def _create_fertilizer_database(self) -> Dict[str, Dict]:
        """Create comprehensive fertilizer database with detailed information"""
        return {
            'Urea': {
                'full_name': 'Urea (46-0-0)',
                'type': 'Nitrogen Fertilizer',
                'npk': [46, 0, 0],
                'cost_per_kg': 27,
                'description': 'Provides high nitrogen for rapid leafy growth',
                'application_method': 'Broadcasting and side dressing',
                'frequency': '2-3 split applications',
                'best_time': 'Early morning or evening',
                'yield_increase': 12
            },
            'DAP': {
                'full_name': 'DAP (18-46-0)',
                'type': 'Phosphate Fertilizer',
                'npk': [18, 46, 0],
                'cost_per_kg': 50,
                'description': 'Rich in phosphorus, essential for root development',
                'application_method': 'Deep placement at sowing',
                'frequency': 'Once at sowing time',
                'best_time': 'Before sowing',
                'yield_increase': 15
            },
            'Balanced NPK Fertilizer': {
                'full_name': 'Balanced NPK (17-17-17)',
                'type': 'Complex Fertilizer',
                'npk': [17, 17, 17],
                'cost_per_kg': 55,
                'description': 'Balanced nutrition for overall plant health',
                'application_method': 'Broadcasting and incorporation',
                'frequency': 'Once per season',
                'best_time': 'During land preparation',
                'yield_increase': 18
            },
            'Compost': {
                'full_name': 'Organic Compost',
                'type': 'Organic Fertilizer',
                'npk': [2, 1, 2],
                'cost_per_kg': 8,
                'description': 'Enhances organic matter and improves soil structure',
                'application_method': 'Incorporation during land preparation',
                'frequency': 'Once per season',
                'best_time': 'Before sowing',
                'yield_increase': 10
            },
            'Water Retaining Fertilizer': {
                'full_name': 'Water Retention Complex',
                'type': 'Specialized Fertilizer',
                'npk': [12, 20, 16],
                'cost_per_kg': 65,
                'description': 'Improves water retention in dry soils',
                'application_method': 'Deep placement',
                'frequency': 'Once per season',
                'best_time': 'Before monsoon',
                'yield_increase': 14
            },
            'Lime': {
                'full_name': 'Agricultural Lime',
                'type': 'pH Modifier',
                'npk': [0, 0, 0],
                'cost_per_kg': 12,
                'description': 'Neutralizes acidic soil and improves pH balance',
                'application_method': 'Broadcasting',
                'frequency': 'Once per year',
                'best_time': 'Before land preparation',
                'yield_increase': 8
            },
            'Organic Fertilizer': {
                'full_name': 'General Organic Fertilizer',
                'type': 'Organic Fertilizer',
                'npk': [3, 2, 3],
                'cost_per_kg': 15,
                'description': 'Enhances fertility naturally, ideal for organic farming',
                'application_method': 'Incorporation',
                'frequency': 'Twice per season',
                'best_time': 'Before sowing and mid-season',
                'yield_increase': 12
            },
            'Muriate of Potash': {
                'full_name': 'Muriate of Potash (0-0-60)',
                'type': 'Potash Fertilizer',
                'npk': [0, 0, 60],
                'cost_per_kg': 35,
                'description': 'High potassium content, improves fruit and flower quality',
                'application_method': 'Broadcasting before flowering',
                'frequency': 'Once per season',
                'best_time': 'Before flowering stage',
                'yield_increase': 16
            },
            'Gypsum': {
                'full_name': 'Agricultural Gypsum',
                'type': 'Soil Conditioner',
                'npk': [0, 0, 0],
                'cost_per_kg': 18,
                'description': 'Corrects alkaline soil, adds calcium and sulfur',
                'application_method': 'Broadcasting',
                'frequency': 'Once per year',
                'best_time': 'Before land preparation',
                'yield_increase': 7
            },
            'General Purpose Fertilizer': {
                'full_name': 'General Purpose NPK',
                'type': 'Complex Fertilizer',
                'npk': [15, 15, 15],
                'cost_per_kg': 45,
                'description': 'Suitable for general use across various crops',
                'application_method': 'Broadcasting',
                'frequency': 'Once per season',
                'best_time': 'At sowing',
                'yield_increase': 10
            }
        }
    
    def _create_crop_nutrient_mapping(self) -> Dict[str, Dict]:
        """Create crop-specific nutrient requirements based on dataset analysis"""
        return {
            'rice': {'n_req': 75, 'p_req': 45, 'k_req': 50, 'ideal_ph': 6.5, 'season': 'Kharif'},
            'wheat': {'n_req': 60, 'p_req': 40, 'k_req': 40, 'ideal_ph': 6.8, 'season': 'Rabi'},
            'maize': {'n_req': 58, 'p_req': 50, 'k_req': 55, 'ideal_ph': 6.2, 'season': 'Kharif'},
            'mung bean': {'n_req': 55, 'p_req': 35, 'k_req': 45, 'ideal_ph': 7.0, 'season': 'Kharif'},
            'tea': {'n_req': 68, 'p_req': 38, 'k_req': 52, 'ideal_ph': 4.8, 'season': 'Year round'},
            'millet': {'n_req': 52, 'p_req': 30, 'k_req': 48, 'ideal_ph': 6.5, 'season': 'Kharif'},
            'lentil': {'n_req': 54, 'p_req': 42, 'k_req': 50, 'ideal_ph': 6.8, 'season': 'Rabi'},
            'jute': {'n_req': 70, 'p_req': 48, 'k_req': 58, 'ideal_ph': 6.5, 'season': 'Kharif'},
            'coffee': {'n_req': 65, 'p_req': 45, 'k_req': 55, 'ideal_ph': 6.8, 'season': 'Year round'},
        }
    
    def get_fertilizer_recommendations(self, nitrogen: str, phosphorus: str, potassium: str, 
                                    crop: str, temperature: str, humidity: str, moisture: str) -> List[Dict[str, Any]]:
        """Get AI-powered fertilizer recommendations using the actual dataset"""
        try:
            # Convert inputs to float
            current_n = float(nitrogen)
            current_p = float(phosphorus)
            current_k = float(potassium)
            temp = float(temperature)
            humid = float(humidity)
            soil_moisture = float(moisture)
            
            if self.dataset.empty:
                return self._get_fallback_recommendations(crop.lower())
            
            # Normalize crop name
            crop_normalized = crop.lower().replace(' ', '').replace('_', '')
            
            # Find similar conditions in the dataset
            similar_conditions = self._find_similar_conditions_advanced(
                temp, humid, soil_moisture, current_n, current_p, current_k, crop_normalized
            )
            
            if similar_conditions.empty:
                return self._get_fallback_recommendations(crop_normalized)
            
            # Get fertilizer recommendations from dataset
            fertilizer_counts = similar_conditions['Fertilizer'].value_counts()
            top_fertilizers = fertilizer_counts.head(5).index.tolist()
            
            # Get crop nutrient requirements
            crop_req = self.crop_nutrient_mapping.get(crop_normalized, {
                'n_req': 60, 'p_req': 40, 'k_req': 45, 'ideal_ph': 6.5, 'season': 'General'
            })
            
            # Calculate nutrient deficiencies
            n_deficit = max(0, crop_req['n_req'] - current_n)
            p_deficit = max(0, crop_req['p_req'] - current_p)
            k_deficit = max(0, crop_req['k_req'] - current_k)
            
            recommendations = []
            
            for fertilizer_name in top_fertilizers:
                if fertilizer_name in self.fertilizer_database:
                    fert_info = self.fertilizer_database[fertilizer_name]
                    
                    # Calculate suitability based on dataset frequency and nutrient match
                    frequency_score = (fertilizer_counts[fertilizer_name] / len(similar_conditions)) * 40
                    nutrient_match_score = self._calculate_nutrient_match(
                        fert_info, n_deficit, p_deficit, k_deficit
                    )
                    environmental_score = self._calculate_environmental_suitability(
                        temp, humid, soil_moisture
                    )
                    
                    total_suitability = min(98, frequency_score + nutrient_match_score + environmental_score)
                    
                    if total_suitability > 50:
                        # Calculate application rate based on deficiency
                        app_rate = self._calculate_optimal_application_rate(
                            fert_info, n_deficit, p_deficit, k_deficit, crop_normalized
                        )
                        
                        # Calculate cost
                        cost = app_rate * fert_info['cost_per_kg']
                        
                        # Get optimal timing
                        timing = self._get_optimal_timing_from_dataset(
                            similar_conditions, crop_normalized, temp
                        )
                        
                        recommendation = {
                            'name': fert_info['full_name'],
                            'type': fert_info['type'],
                            'suitability': int(total_suitability),
                            'application_rate': f"{app_rate:.1f} kg/acre",
                            'cost': int(cost),
                            'timing': timing,
                            'yield_increase': fert_info['yield_increase'],
                            'application_method': fert_info['application_method'],
                            'frequency': fert_info['frequency'],
                            'best_time': self._get_optimal_time(temp, humid, fert_info['best_time'])
                        }
                        
                        recommendations.append(recommendation)
            
            # If we have fewer than 3 recommendations, add more from database based on nutrient needs
            if len(recommendations) < 3:
                additional_ferts = self._get_additional_recommendations(
                    n_deficit, p_deficit, k_deficit, temp, humid, 
                    self.fertilizer_database, recommendations
                )
                recommendations.extend(additional_ferts)
            
            # Sort by suitability and return top 5
            recommendations.sort(key=lambda x: x['suitability'], reverse=True)
            return recommendations[:5]
            
        except Exception as e:
            print(f"Error in fertilizer recommendation: {e}")
            return self._get_fallback_recommendations(crop.lower())
    
    def _find_similar_conditions_advanced(self, temp: float, humid: float, moisture: float,
                                        nitrogen: float, phosphorus: float, potassium: float,
                                        crop: str) -> pd.DataFrame:
        """Find similar conditions using advanced matching algorithm"""
        if self.dataset.empty:
            return pd.DataFrame()
        
        # Filter by crop first (if crop exists in dataset)
        crop_data = self.dataset[self.dataset['Crop'].str.lower().str.contains(crop, na=False)]
        
        if crop_data.empty:
            # If crop not found, use all data
            search_data = self.dataset.copy()
        else:
            search_data = crop_data.copy()
        
        # Calculate similarity scores for environmental conditions
        temp_diff = abs(search_data['Temperature'] - temp) / temp if temp > 0 else 0
        moisture_diff = abs(search_data['Moisture'] - moisture) / moisture if moisture > 0 else 0
        
        # Calculate similarity for nutrients (normalized)
        n_diff = abs(search_data['Nitrogen'] - nitrogen) / max(nitrogen, 1)
        p_diff = abs(search_data['Phosphorous'] - phosphorus) / max(phosphorus, 1)
        k_diff = abs(search_data['Potassium'] - potassium) / max(potassium, 1)
        
        # Combined similarity score (lower is better)
        similarity_score = (
            temp_diff * 0.25 + 
            moisture_diff * 0.20 + 
            n_diff * 0.20 + 
            p_diff * 0.20 + 
            k_diff * 0.15
        )
        
        # Get top 10 most similar conditions
        top_indices = similarity_score.nsmallest(10).index
        return search_data.loc[top_indices]
    
    def _calculate_nutrient_match(self, fert_info: Dict, n_deficit: float, 
                                p_deficit: float, k_deficit: float) -> float:
        """Calculate how well fertilizer matches nutrient deficiency"""
        fert_n, fert_p, fert_k = fert_info['npk']
        match_score = 0
        
        total_deficit = n_deficit + p_deficit + k_deficit
        if total_deficit == 0:
            return 25  # Base score if no deficiency
        
        # Score based on nutrient contribution to deficit
        if n_deficit > 0 and fert_n > 0:
            match_score += min(15, (fert_n / max(n_deficit, 10)) * 10)
        if p_deficit > 0 and fert_p > 0:
            match_score += min(15, (fert_p / max(p_deficit, 10)) * 10)
        if k_deficit > 0 and fert_k > 0:
            match_score += min(15, (fert_k / max(k_deficit, 10)) * 10)
        
        return min(35, match_score)
    
    def _calculate_environmental_suitability(self, temp: float, humid: float, 
                                          moisture: float) -> float:
        """Calculate environmental suitability score"""
        score = 25  # Base environmental score
        
        # Temperature adjustments
        if 20 <= temp <= 30:
            score += 5
        elif temp < 15 or temp > 35:
            score -= 3
        
        # Humidity adjustments
        if 50 <= humid <= 80:
            score += 3
        elif humid < 40 or humid > 90:
            score -= 2
        
        # Moisture adjustments
        if moisture >= 0.4:
            score += 2
        elif moisture < 0.3:
            score -= 2
        
        return max(15, min(35, score))
    
    def _calculate_optimal_application_rate(self, fert_info: Dict, n_deficit: float,
                                          p_deficit: float, k_deficit: float, crop: str) -> float:
        """Calculate optimal application rate based on deficiency and fertilizer type"""
        fert_type = fert_info['type']
        
        # Base rates by fertilizer type
        base_rates = {
            'Nitrogen Fertilizer': 35,
            'Phosphate Fertilizer': 30,
            'Potash Fertilizer': 25,
            'Complex Fertilizer': 40,
            'Organic Fertilizer': 200,
            'pH Modifier': 100,
            'Soil Conditioner': 80,
            'Specialized Fertilizer': 35
        }
        
        base_rate = base_rates.get(fert_type, 30)
        
        # Adjust based on deficiency
        max_deficit = max(n_deficit, p_deficit, k_deficit)
        if max_deficit > 30:
            base_rate *= 1.3
        elif max_deficit > 15:
            base_rate *= 1.1
        elif max_deficit < 5:
            base_rate *= 0.8
        
        # Crop-specific adjustments
        if crop in ['rice', 'wheat', 'maize']:
            base_rate *= 1.1
        elif crop in ['tea', 'coffee']:
            base_rate *= 0.9
        
        return min(60, max(15, base_rate))
    
    def _get_optimal_timing_from_dataset(self, similar_conditions: pd.DataFrame, 
                                       crop: str, temp: float) -> str:
        """Get optimal timing based on dataset and conditions"""
        crop_seasons = {
            'rice': 'Kharif season (June-October)',
            'wheat': 'Rabi season (November-April)',
            'maize': 'Kharif season (June-October)',
            'mung bean': 'Kharif season (June-September)',
            'tea': 'Year-round application',
            'millet': 'Kharif season (June-September)',
            'lentil': 'Rabi season (October-March)',
            'jute': 'Kharif season (April-July)',
            'coffee': 'Post-monsoon (October-December)'
        }
        
        base_timing = crop_seasons.get(crop, 'Season appropriate')
        
        if temp > 32:
            return f"{base_timing} - Apply during cooler periods"
        elif temp < 18:
            return f"{base_timing} - Apply during warmer hours"
        else:
            return base_timing
    
    def _get_optimal_time(self, temp: float, humid: float, default_time: str) -> str:
        """Get optimal time of day for application"""
        if temp > 30:
            return "Early morning (6-8 AM) or evening (5-7 PM)"
        elif humid > 85:
            return "During dry weather conditions"
        else:
            return default_time
    
    def _get_additional_recommendations(self, n_deficit: float, p_deficit: float, k_deficit: float,
                                       temp: float, humid: float, fert_db: Dict, 
                                       existing_recs: List[Dict]) -> List[Dict[str, Any]]:
        """Get additional recommendations from database to supplement dataset matches"""
        additional = []
        already_recommended = {rec['name'] for rec in existing_recs}
        
        # Prioritize fertilizers based on nutrient deficiencies
        priority_list = []
        
        if n_deficit > p_deficit and n_deficit > k_deficit:
            priority_list = ['Urea', 'Organic Fertilizer', 'Balanced NPK Fertilizer']
        elif p_deficit > n_deficit and p_deficit > k_deficit:
            priority_list = ['DAP', 'Balanced NPK Fertilizer', 'Water Retaining Fertilizer']
        elif k_deficit > n_deficit and k_deficit > p_deficit:
            priority_list = ['Muriate of Potash', 'Balanced NPK Fertilizer', 'Water Retaining Fertilizer']
        else:
            priority_list = ['Balanced NPK Fertilizer', 'DAP', 'Urea']
        
        for fert_name in priority_list:
            if len(additional) >= 2:
                break
            if fert_name not in already_recommended and fert_name in fert_db:
                fert_info = fert_db[fert_name]
                suitability = 70 - (len(additional) * 5)  # Decrease suitability for additional recommendations
                
                app_rate = self._calculate_optimal_application_rate(
                    fert_info, n_deficit, p_deficit, k_deficit, ''
                )
                cost = app_rate * fert_info['cost_per_kg']
                
                recommendation = {
                    'name': fert_info['full_name'],
                    'type': fert_info['type'],
                    'suitability': suitability,
                    'application_rate': f"{app_rate:.1f} kg/acre",
                    'cost': int(cost),
                    'timing': 'Season appropriate',
                    'yield_increase': fert_info['yield_increase'],
                    'application_method': fert_info['application_method'],
                    'frequency': fert_info['frequency'],
                    'best_time': self._get_optimal_time(temp, humid, fert_info['best_time'])
                }
                additional.append(recommendation)
        
        return additional
    
    def _get_fallback_recommendations(self, crop: str) -> List[Dict[str, Any]]:
        """Get fallback recommendations when dataset is unavailable"""
        fallback_fertilizers = ['DAP', 'Urea', 'Balanced NPK Fertilizer']
        recommendations = []
        
        for fert_name in fallback_fertilizers:
            if fert_name in self.fertilizer_database:
                fert_info = self.fertilizer_database[fert_name]
                recommendations.append({
                    'name': fert_info['full_name'],
                    'type': fert_info['type'],
                    'suitability': 75,
                    'application_rate': '30.0 kg/acre',
                    'cost': 1200,
                    'timing': 'Season appropriate',
                    'yield_increase': fert_info['yield_increase'],
                    'application_method': fert_info['application_method'],
                    'frequency': fert_info['frequency'],
                    'best_time': fert_info['best_time']
                })
        
        return recommendations

# Global instance
fertilizer_dataset = FertilizerDataset()
