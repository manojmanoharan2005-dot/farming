import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'farming-assistant-secret-key-2024')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/farming_assistant')
    
class DevelopmentConfig(Config):
    DEBUG = True
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/farming_assistant_dev')

class ProductionConfig(Config):
    DEBUG = False
    # Use MongoDB Atlas for production
    MONGO_URI = os.getenv('MONGO_URI')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
