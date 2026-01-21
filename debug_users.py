from backend.app import create_app
from backend.models.all_models import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print("-" * 60)
    print(f"{'ID':<5} | {'Username':<20} | {'Role':<15} | {'Is Active'}")
    print("-" * 60)
    for u in users:
        print(f"{u.id:<5} | {u.username:<20} | {u.role:<15} | {u.is_active}")
    print("-" * 60)
