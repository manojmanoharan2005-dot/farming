import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'farming-assistant-secret-key-2024')
    # Default to Atlas URI from environment
    MONGO_URI = os.getenv('MONGO_URI')
    
class DevelopmentConfig(Config):
    DEBUG = True
    # Use same Atlas URI for development (or set a different one in .env)
    MONGO_URI = os.getenv('MONGO_URI')

class ProductionConfig(Config):
    DEBUG = False
    # Use MongoDB Atlas for production
    MONGO_URI = os.getenv('MONGO_URI')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
