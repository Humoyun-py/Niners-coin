import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_login():
    try:
        # 1. Login
        print(f"Testing login for 'admin'...")
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if resp.status_code == 200:
            data = resp.json()
            print("Login SUCCESS!")
            print(f"Token: {data.get('access_token')[:20]}...")
            print(f"Role: {data.get('role')}")
            
            # 2. Test Admin Endpoint
            headers = {"Authorization": f"Bearer {data.get('access_token')}"}
            resp2 = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
            print(f"Access Admin Users: {resp2.status_code}")
            if resp2.status_code == 200:
                print(f"Users found: {len(resp2.json())}")
            else:
                print(f"Failed to access admin: {resp2.text}")
                
        else:
            print(f"Login FAILED: {resp.status_code} - {resp.text}")

    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    test_login()
