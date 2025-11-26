from pymongo import MongoClient
from datetime import datetime, timezone
import bcrypt
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

def test_mongo_connection():
    try:
        # Get credentials from environment
        mongo_user = os.getenv('MONGO_USER', 'admin')
        mongo_password = os.getenv('MONGO_PASSWORD', '')
        mongo_cluster = os.getenv('MONGO_CLUSTER', 'cluster0.c3ia7tt.mongodb.net')
        
        # Build connection string with encoded password
        encoded_password = quote_plus(mongo_password)
        mongo_uri = f"mongodb+srv://{mongo_user}:{encoded_password}@{mongo_cluster}/farmerdb?retryWrites=true&w=majority&appName=Cluster0"
        
        print(f"🔗 Connecting to MongoDB Atlas...")
        client = MongoClient(mongo_uri)
        
        # Test connection
        client.admin.command('ping')
        
        db = client.farmerdb
        
        print("✅ Connected to MongoDB Atlas farmerdb successfully!")
        
        # List all collections
        collections = db.list_collection_names()
        print(f"📋 Available collections: {collections}")
        
        # Check users collection
        users_count = db.users.count_documents({})
        print(f"👥 Users in database: {users_count}")
        
        # If no users, let's see what's in the users collection
        if users_count > 0:
            sample_user = db.users.find_one()
            print(f"📄 Sample user structure: {list(sample_user.keys()) if sample_user else 'None'}")
        
        # Test inserting a sample user
        test_user = {
            "name": "Test Farmer",
            "email": "test@farmer.com",
            "password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()),
            "created_at": datetime.now(timezone.utc),
            "role": "farmer"
        }
        
        # Check if test user already exists
        existing_user = db.users.find_one({"email": "test@farmer.com"})
        if not existing_user:
            result = db.users.insert_one(test_user)
            print(f"✅ Test user inserted with ID: {result.inserted_id}")
        else:
            print("ℹ️  Test user already exists")
        
        # Verify connection is working
        server_info = client.server_info()
        print(f"📊 MongoDB version: {server_info['version']}")
        
        print("\n🎉 MongoDB connection test successful!")
        
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")

if __name__ == "__main__":
    test_mongo_connection()
