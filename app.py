from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
from datetime import datetime
from pymongo import MongoClient
import bcrypt
from bson.objectid import ObjectId
from dotenv import load_dotenv
import random
import json
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'farming-assistant-secret-key-2024')

# Try to import optional modules (may fail on Vercel)
try:
    from crop_data import crop_dataset
except ImportError:
    crop_dataset = None

try:
    from fertilizer_data import fertilizer_dataset
except ImportError:
    fertilizer_dataset = None

# Skip SQLite-dependent blueprints on Vercel (no file system)
IS_VERCEL = os.environ.get('VERCEL', False)

# Define SQLite paths and functions (will be disabled on Vercel)
PROGRESS_DB_PATH = os.path.join(os.path.dirname(__file__), 'progress.db')
DB_PATH = os.path.join(os.path.dirname(__file__), 'dashboard_fertilizers.db')
sqlite3 = None

def ensure_progress_table():
    """Ensure SQLite progress DB and table exist"""
    if IS_VERCEL or sqlite3 is None:
        return  # Skip on Vercel
    try:
        conn = sqlite3.connect(PROGRESS_DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crop_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                crop_name TEXT,
                start_date TEXT,
                harvest_date TEXT,
                task_timeline TEXT,
                status TEXT,
                recommendation TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()

def ensure_table_exists():
    """Ensure SQLite fertilizers table exists"""
    if IS_VERCEL or sqlite3 is None:
        return  # Skip on Vercel
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_fertilizers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fertilizer_name TEXT,
                cost TEXT,
                yield_increase TEXT,
                application_time TEXT,
                date_added TEXT,
                status TEXT,
                selected_for TEXT,
                suitability TEXT,
                user_id TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()

if not IS_VERCEL:
    try:
        import sqlite3 as sqlite3_module
        sqlite3 = sqlite3_module
        from add_dashboard_fertilizer import dashboard_fertilizer_bp, DB_PATH as FERT_DB_PATH, ensure_table_exists as fert_ensure_table
        from crop_progress import progress_bp
        DB_PATH = FERT_DB_PATH
        ensure_table_exists = fert_ensure_table
        app.register_blueprint(dashboard_fertilizer_bp)
        app.register_blueprint(progress_bp)
    except Exception as e:
        print(f"Warning: Could not load SQLite blueprints: {e}")

# ------------------ MongoDB Configuration ------------------ #
db = None
users_collection = None
crops_collection = None
weather_collection = None
market_collection = None
client = None

try:
    # Get credentials from environment
    mongo_user = os.getenv('MONGO_USER', '')
    mongo_password = os.getenv('MONGO_PASSWORD', '')
    mongo_cluster = os.getenv('MONGO_CLUSTER', 'cluster0.c3ia7tt.mongodb.net')
    
    if not mongo_user or not mongo_password:
        print("⚠️ Warning: MONGO_USER or MONGO_PASSWORD not set")
    else:
        # Build connection string with encoded password
        encoded_password = quote_plus(mongo_password)
        mongo_uri = f"mongodb+srv://{mongo_user}:{encoded_password}@{mongo_cluster}/farmerdb?retryWrites=true&w=majority&appName=Cluster0"
        
        # Connect to MongoDB Atlas
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        
        # Test the connection
        client.admin.command('ping')
        
        db = client["farmerdb"]

        # Collections
        users_collection = db["users"]
        crops_collection = db["crops"]
        weather_collection = db["weather"]
        market_collection = db["market_prices"]

        print("✅ Connected to MongoDB Atlas farmerdb successfully!")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    # Don't crash - app will show "Database not available" message

# ------------------ Helper Functions ------------------ #
def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    """Check if password matches hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def init_db():
    """Initialize database with sample data"""
    if db is None:
        print("Database not connected, skipping init")
        return
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

        print("✅ Database initialized!")
    except Exception as e:
        print(f"❌ Database init error: {e}")

# ------------------ Routes ------------------ #
@app.route('/')
def index():
    return render_template('index.html')

# -------- Login -------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if users_collection is None:
        flash('Database not available', 'error')
        return render_template('login.html')
    
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

        # SQLite fertilizers (only on non-Vercel)
        sqlite_fertilizers = []
        if not IS_VERCEL and sqlite3:
            try:
                ensure_table_exists()
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, fertilizer_name, cost, yield_increase, application_time, date_added, status, selected_for, suitability, user_id
                    FROM dashboard_fertilizers
                    WHERE user_id = ?
                    ORDER BY id DESC
                """, (session['user_id'],))
                rows = cur.fetchall()
                for r in rows:
                    sqlite_fertilizers.append({
                        'id': r[0], 'name': r[1], 'cost': r[2], 'yield_increase': r[3],
                        'application_time': r[4], 'date_added': r[5], 'status': r[6],
                        'selected_for': r[7], 'suitability': r[8], 'user_id': r[9]
                    })
                conn.close()
            except Exception as e:
                print(f"SQLite error: {e}")

        # User crops from MongoDB
        user_crops = []
        try:
            cursor = crops_collection.find({"user_id": session['user_id']})
            for c in cursor:
                user_crops.append({
                    'id': str(c.get('_id')), 'name': c.get('name'),
                    'season': c.get('season'), 'created_at': c.get('created_at')
                })
        except Exception as e:
            print(f"Error loading user crops: {e}")

        return render_template('dashboard.html',
                               user_name=session.get('user_name'),
                               weather=weather_data,
                               crop_rec=crop_recommendation,
                               prices=market_prices,
                               sqlite_fertilizers=sqlite_fertilizers,
                               user_crops=user_crops)

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

# ---------------- Delete fertilizer (form redirect) ------------------
@app.route('/delete_fertilizer/<int:fertilizer_id>', methods=['POST'])
def delete_fertilizer(fertilizer_id):
    # Delete only if the fertilizer belongs to this user
    if 'user_id' not in session:
        flash('Not authenticated', 'error')
        return redirect(url_for('login'))

    if IS_VERCEL or not sqlite3:
        flash('Feature not available', 'error')
        return redirect(url_for('dashboard'))

    try:
        ensure_table_exists()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM dashboard_fertilizers WHERE id = ? AND user_id = ?", (fertilizer_id, session['user_id']))
        conn.commit()
        if cur.rowcount == 0:
            flash('Fertilizer not found or not permitted to delete', 'error')
        else:
            flash('Fertilizer deleted', 'success')
        conn.close()
    except Exception as e:
        flash(f'Error deleting fertilizer: {e}', 'error')

    return redirect(url_for('dashboard'))

# ---------------- Delete crop (form redirect) ------------------
@app.route('/delete_crop/<crop_id>', methods=['POST'])
def delete_crop(crop_id):
    # Delete a MongoDB crop only if it belongs to the logged-in user
    if 'user_id' not in session:
        flash('Not authenticated', 'error')
        return redirect(url_for('login'))

    try:
        obj_id = ObjectId(crop_id)
        res = crops_collection.delete_one({"_id": obj_id, "user_id": session['user_id']})
        if res.deleted_count == 0:
            flash('Crop not found or not permitted to delete', 'error')
        else:
            flash('Crop deleted', 'success')
    except Exception as e:
        flash(f'Error deleting crop: {e}', 'error')

    return redirect(url_for('dashboard'))

# ---------------- Tighten existing AJAX delete (keeps JSON behavior) ------------------
@app.route('/delete_dashboard_fertilizer', methods=['POST'])
def delete_dashboard_fertilizer():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'error': 'Not authenticated'}), 401

    if IS_VERCEL or not sqlite3:
        return jsonify({'status': 'error', 'error': 'Feature not available'}), 400

    try:
        payload = request.get_json() or {}
        fid = payload.get('id')
        if not fid:
            return jsonify({'status': 'error', 'error': 'Missing id'}), 400

        ensure_table_exists()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM dashboard_fertilizers WHERE id = ? AND user_id = ?", (fid, session['user_id']))
        conn.commit()
        if cur.rowcount == 0:
            conn.close()
            return jsonify({'status': 'error', 'error': 'Not found or not permitted'}), 404
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

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
    
    if request.method == 'POST' and crop_dataset:
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
            else:
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
                
                if recommendations:
                    flash(f'Found {len(recommendations)} crop recommendations!', 'success')
                else:
                    flash('No suitable crops found.', 'warning')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
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
    
    if request.method == 'POST' and fertilizer_dataset:
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
            else:
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
                
                if recommendations:
                    flash(f'Found {len(recommendations)} AI-powered fertilizer recommendations for {crop_name}!', 'success')
                else:
                    flash('No suitable fertilizer recommendations found for your conditions. Please check your inputs.', 'warning')
            
        except Exception as e:
            flash(f'Error processing recommendations: {str(e)}', 'error')
            print(f"Fertilizer recommendation error: {e}")
    
    return render_template('fertilizer_advice.html', 
                         user_name=session.get('user_name'),
                         recommendations=recommendations,
                         form_data=form_data,
                         crop_name=crop_name)

@app.route('/save_progress', methods=['POST'])
def save_progress():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'error': 'Not authenticated'}), 401
    if IS_VERCEL or not sqlite3:
        return jsonify({'status': 'error', 'error': 'Feature not available on this platform'}), 400
    try:
        payload = request.get_json() or {}
        crop_name = payload.get('crop_name')
        start_date = payload.get('start_date')
        harvest_date = payload.get('harvest_date')
        task_timeline = payload.get('task_timeline', [])
        status = payload.get('status', 'monitoring')
        recommendation = payload.get('recommendation', '')
        if not crop_name or not start_date or not harvest_date:
            return jsonify({'status': 'error', 'error': 'Missing required fields'}), 400
        ensure_progress_table()
        conn = sqlite3.connect(PROGRESS_DB_PATH)
        cur = conn.cursor()
        cur.execute("""INSERT INTO crop_progress (user_id, crop_name, start_date, harvest_date, task_timeline, status, recommendation)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (session['user_id'], crop_name, start_date, harvest_date, json.dumps(task_timeline), status, recommendation))
        conn.commit()
        lastid = cur.lastrowid
        conn.close()
        return jsonify({'status': 'success', 'id': lastid})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/get_progress')
def get_progress():
    if 'user_id' not in session:
        return jsonify([])
    if IS_VERCEL or not sqlite3:
        return jsonify([])
    try:
        ensure_progress_table()
        conn = sqlite3.connect(PROGRESS_DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM crop_progress WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
        rows = cur.fetchall()
        out = []
        today = datetime.utcnow().date()
        for r in rows:
            tasks = json.loads(r['task_timeline'] or '[]') if r['task_timeline'] else []
            progress_percent = 0
            if tasks:
                done = sum(1 for t in tasks if t.get('done'))
                progress_percent = int((done / len(tasks)) * 100)
            out.append({'id': r['id'], 'crop_name': r['crop_name'], 'start_date': r['start_date'],
                        'harvest_date': r['harvest_date'], 'tasks': tasks, 'status': r['status'],
                        'recommendation': r['recommendation'] or '', 'progress_percent': progress_percent})
        conn.close()
        return jsonify(out)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/mark_task_done', methods=['POST'])
def mark_task_done():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'error': 'Not authenticated'}), 401
    if IS_VERCEL or not sqlite3:
        return jsonify({'status': 'error', 'error': 'Feature not available'}), 400
    try:
        payload = request.get_json() or {}
        pid = payload.get('progress_id')
        task_index = payload.get('task_index')
        if pid is None or task_index is None:
            return jsonify({'status': 'error', 'error': 'Missing fields'}), 400
        ensure_progress_table()
        conn = sqlite3.connect(PROGRESS_DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT task_timeline FROM crop_progress WHERE id = ? AND user_id = ?", (pid, session['user_id']))
        row = cur.fetchone()
        if not row:
            conn.close()
            return jsonify({'status': 'error', 'error': 'Not found'}), 404
        tasks = json.loads(row[0] or '[]')
        if task_index < 0 or task_index >= len(tasks):
            conn.close()
            return jsonify({'status': 'error', 'error': 'Invalid index'}), 400
        tasks[task_index]['done'] = True
        all_done = all(t.get('done') for t in tasks)
        new_status = 'completed' if all_done else 'monitoring'
        cur.execute("UPDATE crop_progress SET task_timeline = ?, status = ? WHERE id = ?", (json.dumps(tasks), new_status, pid))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'new_status': new_status})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# Initialize on startup (only for non-Vercel)
if not IS_VERCEL and sqlite3 is not None:
    ensure_progress_table()

# ------------------ Run App ------------------ #
if __name__ == '__main__':
    print("🚀 Starting Farming Assistant Application with MongoDB...")
    init_db()
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
