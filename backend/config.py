import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@localhost/resume_relevance_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
    
    # LLM Configuration
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Vector Store
    CHROMA_PERSIST_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vector_store')
    
    # Scoring Weights
    SEMANTIC_WEIGHT = 0.6
    KEYWORD_WEIGHT = 0.4
    
    # Placement Team Auth (Simple - replace with proper auth in production)
    PLACEMENT_USERS = {
        'placement': 'admin123',
        'hr_team': 'hr2024',
        'admin': 'admin2024'
    }
    
    # Thresholds
    HIGH_RELEVANCE_THRESHOLD = 75
    MEDIUM_RELEVANCE_THRESHOLD = 50