from flask import Blueprint, request, jsonify, session
import sqlite3
import os
import json
from datetime import datetime

progress_bp = Blueprint('progress_bp', __name__)

# Use the same progress DB file used elsewhere
PROGRESS_DB_PATH = os.path.join(os.path.dirname(__file__), 'progress.db')

def ensure_progress_table():
    """
    Ensure the crop_progress table exists with the same schema used in app.py:
      id, user_id, crop_name, start_date, harvest_date, task_timeline, status, recommendation
    """
    conn = sqlite3.connect(PROGRESS_DB_PATH)
    try:
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

@progress_bp.route('/progress/add', methods=['POST'])
def add_progress():
    """
    Add a crop progress entry for the logged-in user.
    JSON payload: { crop_name, start_date, harvest_date, task_timeline (array), status, recommendation }
    Returns JSON with inserted id and stored row.
    """
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'error': 'Not authenticated'}), 401

    payload = request.get_json() or {}
    crop_name = (payload.get('crop_name') or '').strip()
    start_date = (payload.get('start_date') or '').strip()
    harvest_date = (payload.get('harvest_date') or '').strip()
    task_timeline = payload.get('task_timeline', [])
    status = payload.get('status', 'monitoring')
    recommendation = payload.get('recommendation', '')

    if not crop_name or not start_date or not harvest_date:
        return jsonify({'status': 'error', 'error': 'Missing required fields'}), 400

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
        inserted_id = cur.lastrowid
        return jsonify({'status': 'success', 'id': inserted_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        conn.close()

@progress_bp.route('/progress/list', methods=['GET'])
def list_progress():
    """
    Return list of progress entries for the logged-in user, shaped to match progress.js expectations.
    """
    if 'user_id' not in session:
        return jsonify([])

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
            # parse tasks
            tasks = []
            try:
                tasks = json.loads(r['task_timeline'] or '[]')
            except:
                tasks = []
            for t in tasks:
                if 'done' not in t:
                    t['done'] = bool(t.get('done', False))

            # determine recommendation / next task similar to app.get_progress logic
            rec = ''
            next_task = None
            harvest_date = None
            try:
                if r['harvest_date']:
                    harvest_date = datetime.fromisoformat(r['harvest_date']).date()
            except:
                try:
                    harvest_date = datetime.strptime(r['harvest_date'], '%Y-%m-%d').date()
                except:
                    harvest_date = None

            today_tasks = []
            for t in tasks:
                try:
                    if t.get('date') and datetime.fromisoformat(t['date']).date() == today:
                        today_tasks.append(t)
                except:
                    pass

            if today_tasks:
                rec = f"Perform today's task: {today_tasks[0].get('name')}"
                next_task = today_tasks[0]
            else:
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
                        try:
                            sd = datetime.fromisoformat(r['start_date']).date()
                            if (today - sd).days <= 3 or not tasks:
                                rec = "Land preparation ongoing."
                            else:
                                rec = "Monitoring in progress."
                        except:
                            rec = "Monitoring in progress."

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
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        conn.close()

@progress_bp.route('/progress/delete', methods=['POST'])
def delete_progress_json():
    """
    Delete progress entry by id (JSON). Expects { "id": <int> }.
    """
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'error': 'Not authenticated'}), 401

    payload = request.get_json() or {}
    pid = payload.get('id')
    if pid is None:
        return jsonify({'status': 'error', 'error': 'Missing id'}), 400

    ensure_progress_table()
    conn = sqlite3.connect(PROGRESS_DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM crop_progress WHERE id = ? AND user_id = ?", (pid, session['user_id']))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({'status': 'error', 'error': 'Not found or not permitted'}), 404
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        conn.close()
