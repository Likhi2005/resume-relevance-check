from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db
import logging
import os

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=["http://localhost:8501"])  # Allow Streamlit frontend
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    
    # Register blueprints
    from routes import upload_bp, evaluation_bp
    app.register_blueprint(upload_bp)
    app.register_blueprint(evaluation_bp)
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Resume Relevance Check API is running',
            'version': '1.0.0'
        }), 200
    
    # Authentication endpoint for placement team
    @app.route('/auth/placement', methods=['POST'])
    def authenticate_placement():
        from flask import request
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Simple authentication (replace with proper auth in production)
        placement_users = app.config.get('PLACEMENT_USERS', {})
        
        if username in placement_users and placement_users[username] == password:
            return jsonify({
                'success': True,
                'message': 'Authentication successful',
                'user': {
                    'username': username,
                    'role': 'placement_team'
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Error creating database tables: {str(e)}")
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)