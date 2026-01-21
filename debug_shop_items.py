from backend.app import create_app
from backend.models.all_models import ShopItem

app = create_app()

with app.app_context():
    items = ShopItem.query.all()
    print("-" * 50)
    print(f"{'ID':<5} | {'Name':<20} | {'Image URL'}")
    print("-" * 50)
    for i in items:
        print(f"{i.id:<5} | {i.name:<20} | {i.image_url}")
    print("-" * 50)
