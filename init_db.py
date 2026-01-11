import os
import sys

# Add backend to path so we can import models and app
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from models.all_models import db

def initialize():
    print("🚀 Starting Database Initialization...")
    
    # Create the Flask application instance
    app = create_app()
    
    with app.app_context():
        # 1. Create all tables
        print("Creating tables if they don't exist...")
        db.create_all()
        
        # 2. Seeding logic is already inside create_app() -> db.init_app(app)
        # but we can call it explicitly or just rely on the existing sync/seed logic in app.py
        # Since create_app() calls seed_data() and sync_schema(), we are good.
        
        print("✅ Database setup complete!")
        print("Note: admin and director accounts have been created if they were missing.")
        print("Admin: username='admin', password='admin123'")
        print("Director: username='director', password='director123'")

if __name__ == "__main__":
    initialize()
