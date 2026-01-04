import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
