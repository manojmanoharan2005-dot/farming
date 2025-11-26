import sys
import os

# Set Vercel environment flag
os.environ['VERCEL'] = '1'

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, init_db

# Initialize database
init_db()

# Export for Vercel
application = app

# Vercel serverless handler
app.debug = False
