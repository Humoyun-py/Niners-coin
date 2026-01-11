import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from models.all_models import db

app = create_app()

with app.app_context():
    print("Creating all tables (including new ones)...")
    db.create_all()
    print("Done.")
