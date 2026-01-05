import sqlite3
import os

# Path to the database
db_path = os.path.join('instance', 'niners.db')

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}. Please run the app first.")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column(table, column, type, default=None):
    try:
        query = f"ALTER TABLE {table} ADD COLUMN {column} {type}"
        if default is not None:
            query += f" DEFAULT {default}"
        cursor.execute(query)
        print(f"Added column '{column}' to table '{table}'.")
    except sqlite3.OperationalError:
        print(f"Column '{column}' in table '{table}' already exists or table not found.")

# Add missing columns
add_column('teachers', 'daily_limit', 'REAL', '500.0')
add_column('coin_transactions', 'teacher_id', 'INTEGER')

conn.commit()
conn.close()
print("Migration completed successfully!")
