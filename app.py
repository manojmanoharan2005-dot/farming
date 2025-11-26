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
from add_dashboard_fertilizer import dashboard_fertilizer_bp, DB_PATH, ensure_table_exists
from crop_progress import progress_bp
import sqlite3
import json
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'farming-assistant-secret-key-2024')
app.register_blueprint(dashboard_fertilizer_bp)
app.register_blueprint(progress_bp)

# ------------------ MongoDB Configuration ------------------ #
try:
    # Get credentials from environment
    mongo_user = os.getenv('MONGO_USER', 'admin')
    mongo_password = os.getenv('MONGO_PASSWORD', '')
    mongo_cluster = os.getenv('MONGO_CLUSTER', 'cluster0.c3ia7tt.mongodb.net')
    
    if not mongo_password:
        raise Exception("MONGO_PASSWORD environment variable not set. Please check your .env file.")
    
    # Build connection string with encoded password
    encoded_password = quote_plus(mongo_password)
    mongo_uri = f"mongodb+srv://{mongo_user}:{encoded_password}@{mongo_cluster}/farmerdb?retryWrites=true&w=majority&appName=Cluster0"
    
    # Connect to MongoDB Atlas
    client = MongoClient(mongo_uri)
    
    # Test the connection
    client.admin.command('ping')
    
    db = client["farmerdb"]   # Ensure the database name is farmerdb

    # Collections
    users_collection = db["users"]
    crops_collection = db["crops"]
    weather_collection = db["weather"]
    market_collection = db["market_prices"]

    print("✅ Connected to MongoDB Atlas farmerdb successfully!")
    print(f"Available collections: {db.list_collection_names()}")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    raise e  # Stop the app if DB connection fails

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

# New: Progress DB path
PROGRESS_DB_PATH = os.path.join(os.path.dirname(__file__), 'progress.db')

def ensure_progress_table():
    """Ensure SQLite progress DB and table exist"""
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

        # Ensure table exists and load SQLite-saved fertilizers for this user only
        ensure_table_exists()
        sqlite_fertilizers = []
        try:
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
                    'id': r[0],
                    'name': r[1],
                    'cost': r[2],
                    'yield_increase': r[3],
                    'application_time': r[4],
                    'date_added': r[5],
                    'status': r[6],
                    'selected_for': r[7],
                    'suitability': r[8],
                    'user_id': r[9]
                })
        finally:
            try:
                conn.close()
            except:
                pass

        # Load only the crops that belong to the logged-in user (MongoDB)
        user_crops = []
        try:
            cursor = crops_collection.find({"user_id": session['user_id']})
            for c in cursor:
                user_crops.append({
                    'id': str(c.get('_id')),
                    'name': c.get('name'),
                    'season': c.get('season'),
                    'created_at': c.get('created_at')
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

    try:
        ensure_table_exists()
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM dashboard_fertilizers WHERE id = ? AND user_id = ?", (fertilizer_id, session['user_id']))
            conn.commit()
            if cur.rowcount == 0:
                flash('Fertilizer not found or not permitted to delete', 'error')
            else:
                flash('Fertilizer deleted', 'success')
        finally:
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
        try:
            obj_id = ObjectId(crop_id)
        except Exception:
            flash('Invalid crop id', 'error')
            return redirect(url_for('dashboard'))

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
    try:
        payload = request.get_json() or {}
        fid = payload.get('id')
        if not fid:
            return jsonify({'status': 'error', 'error': 'Missing id'}), 400

        if 'user_id' not in session:
            return jsonify({'status': 'error', 'error': 'Not authenticated'}), 401

        ensure_table_exists()
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM dashboard_fertilizers WHERE id = ? AND user_id = ?", (fid, session['user_id']))
            conn.commit()
            if cur.rowcount == 0:
                return jsonify({'status': 'error', 'error': 'Not found or not permitted'}), 404
            return jsonify({'status': 'success'})
        finally:
            conn.close()
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

@app.route('/save_progress', methods=['POST'])
def save_progress():
    if 'user_id' not in session:
        return jsonify({'status':'error','error':'Not authenticated'}), 401
    try:
        payload = request.get_json() or {}
        crop_name = payload.get('crop_name')
        start_date = payload.get('start_date')
        harvest_date = payload.get('harvest_date')
        task_timeline = payload.get('task_timeline', [])
        status = payload.get('status', 'monitoring')
        recommendation = payload.get('recommendation', '')

        if not crop_name or not start_date or not harvest_date:
            return jsonify({'status':'error','error':'Missing required fields'}), 400

        ensure_progress_table()
        conn = sqlite3.connect(PROGRESS_DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO crop_progress (user_id, crop_name, start_date, harvest_date, task_timeline, status, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session['user_id'],
                crop_name,
                start_date,
                harvest_date,
                json.dumps(task_timeline, default=str),
                status,
                recommendation
            ))
            conn.commit()
            return jsonify({'status':'success', 'id': cur.lastrowid})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({'status':'error','error': str(e)}), 500

@app.route('/get_progress')
def get_progress():
    if 'user_id' not in session:
        return jsonify([])  # return empty for anonymous
    try:
        ensure_progress_table()
        conn = sqlite3.connect(PROGRESS_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM crop_progress WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
            rows = cur.fetchall()
            out = []
            today = datetime.utcnow().date()
            for r in rows:
                tasks = []
                try:
                    tasks = json.loads(r['task_timeline'] or '[]')
                except:
                    tasks = []
                # Normalize tasks: expect {'name':..,'date': 'YYYY-MM-DD', 'done': bool}
                for t in tasks:
                    if 'done' not in t:
                        t['done'] = bool(t.get('done', False))

                # Determine next task and recommendation
                next_task = None
                rec = ''
                harvest_date = None
                try:
                    harvest_date = datetime.fromisoformat(r['harvest_date']).date()
                except:
                    try:
                        harvest_date = datetime.strptime(r['harvest_date'], '%Y-%m-%d').date()
                    except:
                        harvest_date = None

                # If any task date == today
                today_tasks = [t for t in tasks if t.get('date') and datetime.fromisoformat(t['date']).date() == today]
                if today_tasks:
                    rec = f"Perform today's task: {today_tasks[0].get('name')}"
                    next_task = today_tasks[0]
                else:
                    # upcoming tasks > today
                    future = []
                    for t in tasks:
                        try:
                            td = datetime.fromisoformat(t['date']).date()
                            if td > today and not t.get('done'):
                                future.append((td, t))
                        except:
                            continue
                    if future:
                        future.sort(key=lambda x: x[0])
                        next_task = future[0][1]
                        rec = f"Next upcoming task: {next_task.get('name')} on {future[0][0].isoformat()}"
                    else:
                        if harvest_date and today > harvest_date:
                            rec = "Harvest completed — check final yield."
                        else:
                            # If started recently or no clear tasks
                            try:
                                start_date = datetime.fromisoformat(r['start_date']).date()
                                if (today - start_date).days <= 3 or not tasks:
                                    rec = "Land preparation ongoing."
                                else:
                                    rec = "Monitoring in progress."
                            except:
                                rec = "Monitoring in progress."

                # progress percent
                total_tasks = len(tasks) or 0
                done_tasks = sum(1 for t in tasks if t.get('done'))
                progress_percent = int((done_tasks / total_tasks) * 100) if total_tasks else 0

                out.append({
                    'id': r['id'],
                    'crop_name': r['crop_name'],
                    'start_date': r['start_date'],
                    'harvest_date': r['harvest_date'],
                    'tasks': tasks,
                    'status': r['status'],
                    'recommendation': rec,
                    'next_task': next_task,
                    'progress_percent': progress_percent
                })
            return jsonify(out)
        finally:
            conn.close()
    except Exception as e:
        return jsonify({'status':'error','error': str(e)}), 500

@app.route('/mark_task_done', methods=['POST'])
def mark_task_done():
    if 'user_id' not in session:
        return jsonify({'status':'error','error':'Not authenticated'}), 401
    try:
        payload = request.get_json() or {}
        pid = payload.get('progress_id')
        task_index = payload.get('task_index')
        if pid is None or task_index is None:
            return jsonify({'status':'error','error':'Missing progress_id or task_index'}), 400

        ensure_progress_table()
        conn = sqlite3.connect(PROGRESS_DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute("SELECT task_timeline FROM crop_progress WHERE id = ? AND user_id = ?", (pid, session['user_id']))
            row = cur.fetchone()
            if not row:
                return jsonify({'status':'error','error':'Not found'}), 404
            tasks = json.loads(row[0] or '[]')
            if task_index < 0 or task_index >= len(tasks):
                return jsonify({'status':'error','error':'Invalid task index'}), 400
            tasks[task_index]['done'] = True
            # Update status if all done
            all_done = all(t.get('done') for t in tasks) if tasks else False
            new_status = 'completed' if all_done else 'monitoring'
            cur.execute("UPDATE crop_progress SET task_timeline = ?, status = ? WHERE id = ?", (json.dumps(tasks), new_status, pid))
            conn.commit()
            return jsonify({'status':'success','new_status': new_status})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({'status':'error','error': str(e)}), 500

# Ensure progress table on startup
ensure_progress_table()

# ------------------ Run App ------------------ #
if __name__ == '__main__':
    print("🚀 Starting Farming Assistant Application with MongoDB...")
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
