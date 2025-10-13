from pymongo import MongoClient
from datetime import datetime
import bcrypt

def test_mongo_connection():
    try:
        # Connect to your farmerdb
        client = MongoClient('mongodb://localhost:27017/farmerdb')
        db = client.farmerdb
        
        print("✅ Connected to MongoDB farmerdb successfully!")
        
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
            "created_at": datetime.utcnow(),
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
