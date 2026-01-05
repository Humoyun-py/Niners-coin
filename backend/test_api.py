from app import create_app
import traceback

def test_users_api():
    app = create_app()
    client = app.test_client()
    
    # Try calling without JWT first since I commented it out
    print("Testing /api/admin/users (assuming @jwt_required is commented out)...")
    try:
        response = client.get('/api/admin/users')
        print(f"Status Code: {response.status_code}")
        print("Response Data:")
        print(response.data.decode('utf-8'))
    except Exception as e:
        print(f"Call failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_users_api()
