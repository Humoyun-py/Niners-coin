from app import create_app
from models.all_models import db, User
import traceback

def diagnose():
    app = create_app()
    with app.app_context():
        try:
            users = User.query.all()
            print(f"Total users found: {len(users)}")
            
            for u in users:
                print(f"Testing User ID: {u.id}, Username: {u.username}...", end=" ")
                try:
                    # Simulate the exact dict used in the API
                    d = {
                        "id": u.id,
                        "username": u.username,
                        "email": u.email,
                        "role": u.role,
                        "full_name": u.full_name,
                        "is_active": u.is_active,
                        "block_reason": u.block_reason,
                        "debt_amount": u.debt_amount,
                        "daily_limit": u.teacher_profile.daily_limit if (u.role == 'teacher' and u.teacher_profile) else None
                    }
                    print("OK")
                except Exception as e:
                    print(f"FAILED!")
                    print(f"Error: {e}")
                    traceback.print_exc()
                    
        except Exception as e:
            print(f"GLOBAL FAILURE: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    diagnose()
