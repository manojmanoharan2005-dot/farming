from flask import Blueprint, request, jsonify, session
import sqlite3
import os
from datetime import datetime

dashboard_fertilizer_bp = Blueprint('dashboard_fertilizer_bp', __name__)

# DB path next to this file
DB_PATH = os.path.join(os.path.dirname(__file__), 'dashboard_fertilizers.db')

def ensure_table_exists():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_fertilizers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fertilizer_name TEXT,
                cost REAL,
                yield_increase TEXT,
                application_time TEXT,
                date_added TEXT,
                status TEXT DEFAULT 'Purchased',
                selected_for TEXT,
                suitability REAL,
                user_id TEXT
            )
        """)
        conn.commit()

        # Ensure backward-compatible migration: if table existed without new columns, add them.
        cur.execute("PRAGMA table_info('dashboard_fertilizers')")
        existing_cols = {row[1] for row in cur.fetchall()}  # row[1] is column name

        # Add selected_for column if missing
        if 'selected_for' not in existing_cols:
            try:
                cur.execute("ALTER TABLE dashboard_fertilizers ADD COLUMN selected_for TEXT")
            except Exception:
                pass

        # Add suitability column if missing
        if 'suitability' not in existing_cols:
            try:
                cur.execute("ALTER TABLE dashboard_fertilizers ADD COLUMN suitability REAL")
            except Exception:
                pass

        # Add user_id column if missing (to keep fertilizers user-specific)
        if 'user_id' not in existing_cols:
            try:
                cur.execute("ALTER TABLE dashboard_fertilizers ADD COLUMN user_id TEXT")
            except Exception:
                pass

        conn.commit()
    finally:
        conn.close()

@dashboard_fertilizer_bp.route('/add_dashboard_fertilizer', methods=['POST'])
def add_dashboard_fertilizer():
    # Require login: only logged-in users can save fertilizers
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'error': 'Not authenticated'}), 401

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    cost = data.get('cost', 0)
    yield_increase = data.get('yield_increase', '').strip()
    application_time = data.get('application_time', '').strip()
    selected_for = data.get('selected_for', '').strip()
    suitability = data.get('suitability', None)
    date_added = datetime.utcnow().isoformat()

    if not name:
        return jsonify({'status': 'error', 'error': 'Missing fertilizer name'}), 400

    ensure_table_exists()

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        # Save user_id so records are per-user
        cur.execute("""
            INSERT INTO dashboard_fertilizers
            (fertilizer_name, cost, yield_increase, application_time, date_added, status, selected_for, suitability, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, cost, yield_increase, application_time, date_added, 'Purchased', selected_for, suitability, session['user_id']))
        conn.commit()
        inserted_id = cur.lastrowid

        # Return the inserted id and saved data so frontend can confirm the insert
        return jsonify({
            'status': 'success',
            'id': inserted_id,
            'fertilizer': {
                'id': inserted_id,
                'fertilizer_name': name,
                'cost': cost,
                'yield_increase': yield_increase,
                'application_time': application_time,
                'date_added': date_added,
                'status': 'Purchased',
                'selected_for': selected_for,
                'suitability': suitability,
                'user_id': session['user_id']
            }
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        conn.close()
