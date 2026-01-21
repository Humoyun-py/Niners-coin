import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import create_app
from flask import url_for

app = create_app()

with app.app_context():
    print("-" * 60)
    print("REGISTERED ROUTES:")
    print("-" * 60)
    found_users = False
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> {rule.endpoint}")
        if '/api/admin/users' in str(rule):
            found_users = True
            
    print("-" * 60)
    if found_users:
        print("✅ /api/admin/users is REGISTERED")
    else:
        print("❌ /api/admin/users is NOT registered")
