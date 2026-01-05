import requests

def test_debug():
    url = "http://localhost:5000/api/auth/debug/env"
    try:
        r = requests.get(url)
        print(f"Status: {r.status_code}")
        print(r.json())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_debug()
