import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from models.all_models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Attempting to fix database schema...")
    
    # List of columns to check/add
    updates = [
        ("classes", "schedule_days", "VARCHAR(50)"),
        ("classes", "schedule_time", "VARCHAR(10)")
    ]
    
    for table, col, type_ in updates:
        try:
            print(f"Adding {col} to {table}...")
            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {type_}"))
            print(f"SUCCESS: Added {col}")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "exists" in str(e).lower():
                print(f"INFO: {col} already exists.")
            else:
                print(f"ERROR: Could not add {col}: {e}")
    
    db.session.commit()
    print("Database fix completed.")
