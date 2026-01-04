import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# 1. Get Database URL from environment variable
# Use PostgreSQL/MySQL for production, fallback to SQLite for local development
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Default to local SQLite if no URL is provided
    # Note: For professional setup, always ensure DATABASE_URL is set in .env
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    DATABASE_URL = f"sqlite:///{os.path.join(instance_path, 'niners.db')}"

# 2. Configure Engine
# For Postgres/MySQL, we use pool settings for production stability
if DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("mysql"):
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True
    )
else:
    
    # SQLite doesn't support pool_size/max_overflow
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )

# 3. Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class for models (optional if using Flask-SQLAlchemy's db.Model)
Base = declarative_base()

def get_db():
    """
    Dependency for obtaining a database session.
    Ensures the session is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
