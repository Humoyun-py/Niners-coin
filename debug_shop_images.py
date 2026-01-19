"""
Debug script to check and fix shop item image paths
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from models.all_models import db, ShopItem

app = create_app()

with app.app_context():
    print("=" * 60)
    print("SHOP ITEMS IN DATABASE:")
    print("=" * 60)
    
    items = ShopItem.query.all()
    
    if not items:
        print("No items found in database")
    else:
        for item in items:
            print(f"\nID: {item.id}")
            print(f"Name: {item.name}")
            print(f"Price: {item.price}")
            print(f"Image URL: {item.image_url}")
            
            # Check if file exists
            if item.image_url:
                # Remove leading slash if present
                url_path = item.image_url.lstrip('/')
                file_path = os.path.join('frontend', url_path)
                exists = os.path.exists(file_path)
                print(f"File exists: {exists} ({file_path})")
                
                if not exists:
                    # Set to placeholder
                    print(f"⚠️ File not found - will use placeholder")
                    item.image_url = None
        
        # Commit changes
        db.session.commit()
        print("\n" + "=" * 60)
        print("✅ Database updated - missing images set to placeholder")
        print("=" * 60)
