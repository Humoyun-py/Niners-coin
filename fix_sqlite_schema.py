import sqlite3
import os

# Connect to database
db_path = os.path.join(os.getcwd(), 'backend', 'instance', 'niners.db')
print(f"Connecting to: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Check entries in 'users' table regarding profile_image
    print("Checking users table...")
    try:
        cursor.execute("SELECT profile_image FROM users LIMIT 1")
        print("✅ Column 'profile_image' already exists.")
    except sqlite3.OperationalError as e:
        print(f"❌ Column 'profile_image' missing: {e}")
        print("🛠️ Adding column 'profile_image'...")
        cursor.execute("ALTER TABLE users ADD COLUMN profile_image TEXT")
        conn.commit()
        print("✅ Added 'profile_image' column.")

    # 2. Check entries in 'homework_submissions' table regarding image_url
    print("\nChecking homework_submissions table...")
    try:
        cursor.execute("SELECT image_url FROM homework_submissions LIMIT 1")
    except sqlite3.OperationalError:
       pass
       # If it exists, we want to ensure it is TEXT type?
       # SQLite doesn't let us easily check type, but if it exists, it's dynamic.
       # The error in app.py was about ALTERING type, which is unnecessary in SQLite usually.
    
    # 3. Check for teachers.daily_limit
    print("\nChecking teachers table...")
    try:
        cursor.execute("SELECT daily_limit FROM teachers LIMIT 1")
        print("✅ Column 'daily_limit' already exists.")
    except sqlite3.OperationalError:
        print("🛠️ Adding column 'daily_limit'...")
        cursor.execute("ALTER TABLE teachers ADD COLUMN daily_limit FLOAT DEFAULT 500.0")
        conn.commit()
        print("✅ Added 'daily_limit' column.")

    # 4. Check for users.block_reason
    print("\nChecking users table for block_reason...")
    try:
        cursor.execute("SELECT block_reason FROM users LIMIT 1")
        print("✅ Column 'block_reason' already exists.")
    except sqlite3.OperationalError:
        print("🛠️ Adding column 'block_reason'...")
        cursor.execute("ALTER TABLE users ADD COLUMN block_reason VARCHAR(255)")
        conn.commit()
    
    try:
        cursor.execute("SELECT debt_amount FROM users LIMIT 1")
        print("✅ Column 'debt_amount' already exists.")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN debt_amount FLOAT DEFAULT 0.0")
        conn.commit()
        print("✅ Added 'debt_amount' column.")

    conn.close()
    print("\n🎉 Database Schema Fixes Applied for SQLite.")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
