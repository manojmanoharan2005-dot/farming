from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
from datetime import datetime
from pymongo import MongoClient
import bcrypt
from bson.objectid import ObjectId
from dotenv import load_dotenv
import random
from crop_data import crop_dataset
from fertilizer_data import fertilizer_dataset

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'farming-assistant-secret-key-2024')

# ------------------ MongoDB Configuration ------------------ #
try:
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)
    db = client["farmerdb"]   # Ensure the database name is farmerdb

    # Collections
    users_collection = db["users"]
    crops_collection = db["crops"]
    weather_collection = db["weather"]
    market_collection = db["market_prices"]

    print("✅ Connected to MongoDB farmerdb successfully!")
    print(f"Available collections: {db.list_collection_names()}")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")

# ------------------ Helper Functions ------------------ #
def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    """Check if password matches hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def init_db():
    """Initialize database with sample data"""
    try:
        # Ensure unique email index
        users_collection.create_index("email", unique=True)

        # Weather sample data
        if weather_collection.count_documents({}) == 0:
            sample_weather = {
                "temperature": 28,
                "humidity": 65,
                "rain_chance": 20,
                "location": "default",
                "updated_at": datetime.utcnow()
            }
            weather_collection.insert_one(sample_weather)
            print("🌦 Sample weather data added")

        # Crop sample data
        if crops_collection.count_documents({}) == 0:
            sample_crops = [
                {"name": "Rice (Basmati)", "season": "Kharif", "price": 2850, "recommended": True, "created_at": datetime.utcnow()},
                {"name": "Wheat", "season": "Rabi", "price": 2150, "recommended": False, "created_at": datetime.utcnow()},
                {"name": "Cotton", "season": "Kharif", "price": 5200, "recommended": False, "created_at": datetime.utcnow()}
            ]
            crops_collection.insert_many(sample_crops)
            print("🌱 Sample crop data added")

        # Market sample data
        if market_collection.count_documents({}) == 0:
            market_data = [
                {"crop_name": "Rice", "price_per_quintal": 2850, "market_location": "Delhi Mandi", "date": datetime.utcnow()},
                {"crop_name": "Wheat", "price_per_quintal": 2150, "market_location": "Delhi Mandi", "date": datetime.utcnow()},
                {"crop_name": "Cotton", "price_per_quintal": 5200, "market_location": "Delhi Mandi", "date": datetime.utcnow()}
            ]
            market_collection.insert_many(market_data)
            print("📈 Sample market data added")

        print("✅ Database farmerdb initialized successfully!")

    except Exception as e:
        print(f"❌ Database initialization error: {e}")

# ------------------ Routes ------------------ #
@app.route('/')
def index():
    return render_template('index.html')

# -------- Login -------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please fill in all fields!', 'error')
            return render_template('login.html')

        try:
            user = users_collection.find_one({"email": email})
            if user and check_password(password, user['password']):
                session['user_id'] = str(user['_id'])
                session['user_name'] = user['name']
                session['user_email'] = user['email']

                users_collection.update_one(
                    {"_id": user['_id']},
                    {"$set": {"last_login": datetime.utcnow()}}
                )

                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials!', 'error')

        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')

    return render_template('login.html')

# -------- Register -------- #
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([name, email, password, confirm_password]):
            flash('Please fill in all fields!', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('register.html')

        try:
            if users_collection.find_one({"email": email}):
                flash('Email already exists!', 'error')
                return render_template('register.html')

            new_user = {
                "name": name,
                "email": email,
                "password": hash_password(password),
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }

            result = users_collection.insert_one(new_user)

            session['user_id'] = str(result.inserted_id)
            session['user_name'] = name
            session['user_email'] = email

            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f'Registration error: {str(e)}', 'error')

    return render_template('register.html')

# -------- Dashboard -------- #
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access dashboard', 'error')
        return redirect(url_for('login'))

    try:
        weather_data = weather_collection.find_one({}, sort=[("updated_at", -1)]) or {"temperature": 28, "humidity": 65, "rain_chance": 20}
        recommended_crop = crops_collection.find_one({"recommended": True})

        crop_recommendation = {
            "crop": recommended_crop['name'] if recommended_crop else "Rice (Basmati)",
            "reason": f"Recommended for {recommended_crop['season']} season" if recommended_crop else "Perfect for current season"
        }

        crops = list(crops_collection.find({}).limit(3))
        market_prices = [{'crop': c['name'].split(' ')[0], 'price': f"₹{c['price']}/quintal"} for c in crops]

        return render_template('dashboard.html',
                               user_name=session.get('user_name'),
                               weather=weather_data,
                               crop_rec=crop_recommendation,
                               prices=market_prices)

    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'error')
        return redirect(url_for('index'))

# -------- Logout -------- #
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# ------------------ API Endpoints ------------------ #
@app.route('/api/weather')
def api_weather():
    try:
        new_weather = {
            'temperature': random.randint(25, 35),
            'humidity': random.randint(60, 80),
            'rain_chance': random.randint(10, 40),
            'location': 'default',
            'updated_at': datetime.utcnow()
        }

        weather_collection.update_one({"location": "default"}, {"$set": new_weather}, upsert=True)
        return jsonify(new_weather)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/market-prices')
def api_market_prices():
    try:
        crops = list(crops_collection.find({}))
        updated_prices = {}

        for crop in crops:
            base_price = crop['price']
            fluctuation = random.uniform(-0.05, 0.05)
            new_price = int(base_price * (1 + fluctuation))

            crops_collection.update_one({"_id": crop['_id']}, {"$set": {"price": new_price}})
            updated_prices[crop['name'].split(' ')[0].lower()] = new_price

        return jsonify(updated_prices)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------- Profile -------- #
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to access profile', 'error')
        return redirect(url_for('login'))

    try:
        user = users_collection.find_one({"_id": ObjectId(session['user_id'])})
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('logout'))

        return render_template('profile.html', user=user)
    except Exception as e:
        flash(f'Profile error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# -------- Crop Suggestion -------- #
@app.route('/crop-suggestion', methods=['GET', 'POST'])
def crop_suggestion():
    if 'user_id' not in session:
        flash('Please log in to access crop suggestions', 'error')
        return redirect(url_for('login'))
    
    recommendations = []
    form_data = {}
    
    if request.method == 'POST':
        try:
            # Get form data based on CSV structure
            form_data = {
                'nitrogen': request.form.get('nitrogen'),
                'phosphorus': request.form.get('phosphorus'),
                'potassium': request.form.get('potassium'),
                'temperature': request.form.get('temperature'),
                'humidity': request.form.get('humidity'),
                'ph': request.form.get('ph'),
                'rainfall': request.form.get('rainfall')
            }
            
            # Validate form data
            required_fields = ['nitrogen', 'phosphorus', 'potassium', 'temperature', 'humidity', 'ph', 'rainfall']
            if not all([form_data[field] for field in required_fields]):
                flash('Please fill in all required fields!', 'error')
                return render_template('crop_suggestion.html', 
                                     user_name=session.get('user_name'),
                                     recommendations=[],
                                     form_data=form_data)
            
            # Get crop recommendations using the dataset
            recommendations = crop_dataset.get_crop_recommendations(
                nitrogen=form_data['nitrogen'],
                phosphorus=form_data['phosphorus'],
                potassium=form_data['potassium'],
                temperature=form_data['temperature'],
                humidity=form_data['humidity'],
                ph=form_data['ph'],
                rainfall=form_data['rainfall']
            )
            
            # Store recommendation in database for future reference
            try:
                recommendation_data = {
                    'user_id': session['user_id'],
                    'input_parameters': form_data,
                    'recommendations': recommendations,
                    'created_at': datetime.utcnow()
                }
                db.crop_recommendations.insert_one(recommendation_data)
                
                if recommendations:
                    flash(f'Found {len(recommendations)} crop recommendations based on your soil and climate conditions!', 'success')
                else:
                    flash('No suitable crops found for the given conditions. Please adjust your parameters.', 'warning')
                    
            except Exception as e:
                print(f"Error saving recommendation: {e}")
                
        except ValueError as e:
            flash('Please enter valid numeric values for all fields!', 'error')
        except Exception as e:
            flash(f'Error processing recommendations: {str(e)}', 'error')
    
    return render_template('crop_suggestion.html', 
                         user_name=session.get('user_name'),
                         recommendations=recommendations,
                         form_data=form_data)

# -------- Start Growing -------- #
@app.route('/start_growing/<crop_name>')
def start_growing(crop_name):
    # Mock data - replace with actual data from your database
    growing_data = {
        'crop_name': crop_name,
        'crop_type': 'Food Crop',
        'match_percentage': 85,
        'expected_yield': '2500 kg',
        'estimated_profit': '75000',
        'land_preparation': [
            'Clear the field of weeds and debris',
            'Plow the soil to a depth of 20-30 cm',
            'Add organic matter and level the field',
            'Create proper drainage system'
        ],
        'soil_ph': '6.5-7.5',
        'soil_n': '1.5',
        'soil_p': '1.0',
        'soil_k': '1.2',
        'seed_varieties': [
            {'name': 'Variety A', 'description': 'High yielding, disease resistant'},
            {'name': 'Variety B', 'description': 'Drought tolerant, early maturing'}
        ],
        'seed_rate': '25',
        'sowing_season': 'June-July',
        'sowing_method': 'Row sowing',
        'growing_steps': [
            {
                'title': 'Irrigation Management',
                'content': '<p>Regular irrigation at 7-10 day intervals...</p>'
            },
            {
                'title': 'Pest Management',
                'content': '<p>Monitor for common pests and apply IPM practices...</p>'
            },
            {
                'title': 'Fertilizer Application',
                'content': '<p>Apply balanced NPK fertilizers as per soil test...</p>'
            },
            {
                'title': 'Harvesting',
                'content': '<p>Harvest when crop shows proper maturity signs...</p>'
            }
        ]
    }
    return render_template('start_growing.html', **growing_data)

# -------- Fertilizer Advice -------- #
@app.route('/fertilizer-advice', methods=['GET', 'POST'])
def fertilizer_advice():
    if 'user_id' not in session:
        flash('Please log in to access fertilizer advice', 'error')
        return redirect(url_for('login'))
    
    recommendations = []
    form_data = {}
    crop_name = ""
    
    if request.method == 'POST':
        try:
            # Get form data
            form_data = {
                'nitrogen': request.form.get('nitrogen'),
                'phosphorus': request.form.get('phosphorus'),
                'potassium': request.form.get('potassium'),
                'crop': request.form.get('crop'),
                'temperature': request.form.get('temperature'),
                'humidity': request.form.get('humidity'),
                'moisture': request.form.get('moisture')
            }
            
            # Validate form data
            required_fields = ['nitrogen', 'phosphorus', 'potassium', 'crop', 'temperature', 'humidity', 'moisture']
            if not all([form_data[field] for field in required_fields]):
                flash('Please fill in all required fields!', 'error')
                return render_template('fertilizer_advice.html', 
                                     user_name=session.get('user_name'),
                                     recommendations=[],
                                     form_data=form_data)
            
            crop_name = form_data['crop'].title()
            
            # Get AI-powered fertilizer recommendations using the dataset
            recommendations = fertilizer_dataset.get_fertilizer_recommendations(
                nitrogen=form_data['nitrogen'],
                phosphorus=form_data['phosphorus'],
                potassium=form_data['potassium'],
                crop=form_data['crop'],
                temperature=form_data['temperature'],
                humidity=form_data['humidity'],
                moisture=form_data['moisture']
            )
            
            if not recommendations:
                flash('No suitable fertilizer recommendations found for your conditions. Please check your inputs.', 'warning')
            else:
                flash(f'Found {len(recommendations)} AI-powered fertilizer recommendations for {crop_name}!', 'success')
            
            # Store recommendation in database
            try:
                recommendation_data = {
                    'user_id': session['user_id'],
                    'input_parameters': form_data,
                    'recommendations': recommendations,
                    'crop_name': crop_name,
                    'recommendation_type': 'fertilizer',
                    'created_at': datetime.utcnow()
                }
                db.fertilizer_recommendations.insert_one(recommendation_data)
            except Exception as e:
                print(f"Error saving fertilizer recommendation: {e}")
                
        except ValueError as e:
            flash('Please enter valid numeric values for all fields!', 'error')
        except Exception as e:
            flash(f'Error processing recommendations: {str(e)}', 'error')
            print(f"Fertilizer recommendation error: {e}")
    
    return render_template('fertilizer_advice.html', 
                         user_name=session.get('user_name'),
                         recommendations=recommendations,
                         form_data=form_data,
                         crop_name=crop_name)

# ------------------ Run App ------------------ #
if __name__ == '__main__':
    print("🚀 Starting Farming Assistant Application with MongoDB...")
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
