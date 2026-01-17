import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app import create_app
from backend.models.all_models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

def check_user_status(username):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' NOT FOUND.")
            return

        print(f"--- User Status: {username} ---")
        print(f"ID: {user.id}")
        print(f"Role: {user.role}")
        print(f"Is Active: {user.is_active}")
        print(f"Block Reason: {user.block_reason}")
        print(f"Password Hash: {user.password_hash}")
        
        # Check default password
        default_pass = f"{username}09"
        is_valid = user.check_password(default_pass)
        print(f"Check Password ('{default_pass}'): {'✅ CORRECT' if is_valid else '❌ INVALID'}")
        
        if not is_valid:
            # Try plain hash check just in case algo differs
            print(f"Manual Hash Check: {check_password_hash(user.password_hash, default_pass)}")

if __name__ == '__main__':
    check_user_status('bilol')
    check_user_status('ilhom')
