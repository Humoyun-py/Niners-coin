from app import create_app
from models.all_models import db, User

def verify_and_fix():
    app = create_app()
    with app.app_context():
        # 1. Unblock
        User.query.filter(User.role.in_(['admin', 'director'])).update({
            User.is_active: True,
            User.block_reason: None,
            User.debt_amount: 0.0
        }, synchronize_session=False)
        db.session.commit()
        print("Updated admin/director status.")

        # 2. Check some users
        users = User.query.limit(5).all()
        for u in users:
            print(f"ID: {u.id}, User: {u.username}, Role: {u.role}, Full: {u.full_name}, Active: {u.is_active}")

if __name__ == "__main__":
    verify_and_fix()
