from app import create_app
from models.all_models import db, User

def fix_admins():
    app = create_app()
    with app.app_context():
        # Unblock all admins and directors
        users = User.query.filter(User.role.in_(['admin', 'director'])).all()
        for u in users:
            u.is_active = True
            u.block_reason = None
            u.debt_amount = 0.0
            print(f"Unblocked {u.role}: {u.username}")
        
        db.session.commit()
        print("Done.")

if __name__ == "__main__":
    fix_admins()
