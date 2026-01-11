import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from models.all_models import db, Class

app = create_app()

with app.app_context():
    print("Checking Classes...")
    try:
        classes = Class.query.all()
        print(f"Found {len(classes)} classes.")
        for c in classes:
            print(f"Class: {c.name}")
            print(f"  Days: {c.schedule_days}")
            print(f"  Time: {c.schedule_time}")
            print(f"  Dict: {c.to_dict()}")
        print("SUCCESS: Classes queried and dict conversion working.")
    except Exception as e:
        print(f"ERROR: {e}")
