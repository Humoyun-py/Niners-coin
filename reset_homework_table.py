import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from models.all_models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Dropping homeworks table...")
    try:
        db.session.execute(text("DROP TABLE homeworks"))
        db.session.commit()
        print("SUCCESS: homeworks table dropped.")
    except Exception as e:
        print(f"Error dropping table: {e}")

    print("You must restart the server (python app.py) to recreate it correctly.")
