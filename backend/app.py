import os
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models.all_models import db
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.teacher_routes import teacher_bp
from routes.admin_routes import admin_bp
from routes.director_routes import director_bp
from routes.coin_test_routes import coin_test_bp

load_dotenv()

jwt = JWTManager()
migrate = Migrate()

def create_app():
    # Set frontend directory
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
    
    # Database Configuration
    instance_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance'))
    if not os.path.exists(instance_path):
        os.makedirs(instance_path, exist_ok=True)
    
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    db_path = os.path.join(instance_path, 'niners.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-dev-key')
    
    CORS(app)
    db.init_app(app)
    
    def seed_data():
        from models.all_models import User
        # Seed Admin
        if not User.query.filter_by(role='admin').first():
            admin = User(
                username='admin',
                email='admin@niners.uz',
                role='admin',
                full_name='System Administrator'
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Seed Director
        if not User.query.filter_by(role='director').first():
            director = User(
                username='director',
                email='director@niners.uz',
                role='director',
                full_name='Main Director'
            )
            director.set_password('director123')
            db.session.add(director)
        
        # Seed Specific Teachers (Komron, Maruf, Mavlon, Madina, Muslima)
        initial_teachers = ["Komron", "Maruf", "Mavlon", "Madina", "Muslima"]
        from models.all_models import Teacher
        
        for name in initial_teachers:
            if not User.query.filter_by(username=name).first():
                new_teacher = User(
                    username=name,
                    email=f"{name.lower()}@niners.uz",
                    role='teacher',
                    full_name=name
                )
                new_teacher.set_password(name) # Password same as name/username
                db.session.add(new_teacher)
                db.session.flush() # flush to get ID
                
                # Create Teacher Profile
                teacher_profile = Teacher(
                    user_id=new_teacher.id,
                    subject="General", # Default subject
                    daily_limit=500.0
                )
                db.session.add(teacher_profile)
                print(f"Seeded Teacher: {name}")
        
        db.session.commit()

    def sync_schema():
        from sqlalchemy import text
        # Add missing columns for PostgreSQL safely
        tables_columns = {
            "teachers": [("daily_limit", "FLOAT DEFAULT 500.0")],
            "badges": [("requirement_text", "VARCHAR(255)")],
            "users": [
                ("block_reason", "VARCHAR(255)"),
                ("debt_amount", "FLOAT DEFAULT 0.0")
            ],
            "coin_transactions": [("teacher_id", "INTEGER REFERENCES teachers(id)")],
            "classes": [
                ("schedule_days", "VARCHAR(50)"),
                ("schedule_time", "VARCHAR(10)")
            ]
        }
        
        for table, cols in tables_columns.items():
            for col_name, col_type in cols:
                try:
                    # SQLite < 3.35 doesn't support IF NOT EXISTS in ALTER TABLE
                    # We try to add. If it exists, it will throw an error, which we catch.
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                    print(f"Schema Sync: Added column {col_name} to {table}")
                except Exception as e:
                    # Check if error is because column exists
                    err_str = str(e).lower()
                    if "duplicate column" in err_str or "exists" in err_str:
                        print(f"Schema Sync Info: Column {col_name} already exists in {table}.")
                    else:
                        print(f"Schema Sync Warning for {table}.{col_name}: {e}")
                    db.session.rollback()
        
        db.session.commit()

    # Initialize Database if it doesn't exist
    with app.app_context():
        db.create_all()
        sync_schema() # Ensure existing tables have new columns
        seed_data()
        
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(teacher_bp, url_prefix='/api/teacher')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(director_bp, url_prefix='/api/director')
    app.register_blueprint(coin_test_bp, url_prefix='/api/game')
    
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/login')
    def login_page():
        return send_from_directory(app.static_folder, 'login.html')


    @app.before_request
    def check_auto_block():
        from datetime import datetime
        now = datetime.now()
        if now.day == 1:
            lock_dir = os.path.join(os.path.dirname(__file__), 'instance')
            if not os.path.exists(lock_dir): os.makedirs(lock_dir)
            lock_file = os.path.join(lock_dir, f'auto_block_{now.month}_{now.year}.lock')
            
            if not os.path.exists(lock_file):
                # Import here to avoid circular dependencies
                from models.all_models import Student, db
                from services.security_service import log_event
                
                # Use a separate thread or just run it here if the list is small
                # For this project, it's fine to run it here
                # Block ALL students
                all_students = Student.query.all()
                for s in all_students:
                    if s.user and s.user.is_active:
                        s.user.is_active = False
                        s.user.block_reason = "To'lov qilingmagan"
                        s.user.debt_amount = 650000.0
                        # Also reset payment status to ensure they are marked for the new month
                        s.payment_status = 'pending'
                        log_event(None, f"Avtomatik hamma uchun blok (Oyni 1-kuni): {s.user.username}", severity='danger')
                
                db.session.commit()
                with open(lock_file, 'w') as f: f.write('executed')


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
