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
from routes.ai_routes import ai_bp
from routes.video_routes import video_bp


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
        
        # Seed Branch Admins (Auto-Run)
        branches = [
            {"username": "niners-yunusobod", "password": "admin123", "branch": "Yunusobod", "full_name": "Admin Yunusobod"},
            {"username": "niners-gulzor", "password": "admin123", "branch": "Gulzor", "full_name": "Admin Gulzor"},
            {"username": "niners-beruniy", "password": "admin123", "branch": "Beruniy", "full_name": "Admin Beruniy"}
        ]
        for b in branches:
            if not User.query.filter_by(username=b['username']).first():
                ba = User(
                    username=b['username'],
                    email=f"{b['username']}@niners.uz",
                    role='admin',
                    full_name=b['full_name'],
                    branch=b['branch']
                )
                ba.set_password(b['password'])
                db.session.add(ba)
                print(f"✅ Auto-Seeded Branch Admin: {b['username']}")
        
        db.session.commit() # Ensure Branch Admins are saved before potential early return below
        
        # Seed Specific Teachers (Komron, Maruf, Mavlon, Madina, Muslima)
        from models.all_models import Teacher, Student, Class, SystemSetting
        
        # 1. Check if already seeded
        if SystemSetting.get_val('sample_data_seeded') == 'true':
            return

        print("\n" + "="*50)
        print("🚀 INITIALIZING SAMPLE DATA SEEDING...")
        print("="*50)

        teacher_map = {} # To keep track of teacher IDs
        initial_teachers = ["Komron", "Maruf", "Mavlon", "Madina", "Muslima"]
        
        for name in initial_teachers:
            user = User.query.filter_by(username=name).first()
            if not user:
                user = User(
                    username=name,
                    email=f"{name.lower()}@niners.uz",
                    role='teacher',
                    full_name=name
                )
                user.set_password(name)
                db.session.add(user)
                db.session.flush()
                
                teacher_profile = Teacher(
                    user_id=user.id,
                    subject="General",
                    daily_limit=500.0
                )
                db.session.add(teacher_profile)
                db.session.flush()
                print(f"✅ Created Teacher: {name}")
                teacher_map[name] = teacher_profile.id
            else:
                if user.teacher_profile:
                    teacher_map[name] = user.teacher_profile.id

        # Full Sample Data for KOMRON and MAVLON
        KOMRON_GROUPS_DCJ = [
            {"name": "Komron - DCJ - 08:30 - Guruh 1", "schedule_days": "Dushanba|Chorshanba|Juma", "schedule_time": "08:30", "students": ["Bilol", "Nurmuhammad"]},
            {"name": "Komron - DCJ - 10:30 - Guruh 2", "schedule_days": "Dushanba|Chorshanba|Juma", "schedule_time": "10:30", "students": ["Mubina", "Sulaymon", "Iymona", "Hilola", "Asolat", "Asalxon", "Ezoza", "Ziyoda", "Munisa"]},
            {"name": "Komron - DCJ - 12:30 - Guruh 3", "schedule_days": "Dushanba|Chorshanba|Juma", "schedule_time": "12:30", "students": ["Abdulloh"]},
            {"name": "Komron - DCJ - 14:00 - Guruh 4", "schedule_days": "Dushanba|Chorshanba|Juma", "schedule_time": "14:00", "students": ["Madina", "Xadicha", "Gulnoza", "Robiya"]},
            {"name": "Komron - DCJ - 15:30 - Guruh 5", "schedule_days": "Dushanba|Chorshanba|Juma", "schedule_time": "15:30", "students": ["Shaxina", "Baxtinisso", "Gulbaxor", "Firdavs"]},
            {"name": "Komron - DCJ - 17:00 - Guruh 6", "schedule_days": "Dushanba|Chorshanba|Juma", "schedule_time": "17:00", "students": ["Mardon", "Odil", "Asadbek", "Rushana", "Abdulloh"]},
            {"name": "Komron - DCJ - 18:30 - Guruh 7", "schedule_days": "Dushanba|Chorshanba|Juma", "schedule_time": "18:30", "students": ["Bexruz", "Shaxina"]}
        ]
        KOMRON_GROUPS_SPS = [
            {"name": "Komron - SPS - 10:00 - Guruh 1", "schedule_days": "Seshanba|Payshanba|Shanba", "schedule_time": "10:00", "students": ["Anasbek", "Xurshid", "Abdurahmon", "Shamshod", "Muhammadamin", "Momin", "Zebo", "Tamila", "Dilsora"]},
            {"name": "Komron - SPS - 14:00 - Guruh 2", "schedule_days": "Seshanba|Payshanba|Shanba", "schedule_time": "14:00", "students": ["Nigora"]},
            {"name": "Komron - SPS - 15:30 - Guruh 3", "schedule_days": "Seshanba|Payshanba|Shanba", "schedule_time": "15:30", "students": ["Dilshoda", "Abduvali", "Husan"]},
            {"name": "Komron - SPS - 17:00 - Guruh 4", "schedule_days": "Seshanba|Payshanba|Shanba", "schedule_time": "17:00", "students": ["Yerdana", "Artyom"]},
            {"name": "Komron - SPS - 18:30 - Guruh 5", "schedule_days": "Seshanba|Payshanba|Shanba", "schedule_time": "18:30", "students": ["Ilhom", "Davron", "Amir"]},
            {"name": "Komron - SPS - 20:00 - Guruh 6", "schedule_days": "Seshanba|Payshanba|Shanba", "schedule_time": "20:00", "students": ["Bilol"]}
        ]
        MAVLON_GROUPS = [
            {"name": "Mavlon - DCJ - 14:30 - Guruh 1", "schedule_days": "Dushanba|Chorshanba|Juma", "schedule_time": "14:30", "students": ["Kamron", "Afruza", "Zilola", "Muslima"]},
            {"name": "Mavlon - DCJ - 16:00 - Guruh 2", "schedule_days": "Dushanba|Chorshanba|Juma", "schedule_time": "16:00", "students": ["Mubina", "Usmon1", "Usmon2", "Shaxzoda"]}
        ]

        all_seed_data = [
            {"teacher": "Komron", "groups": KOMRON_GROUPS_DCJ + KOMRON_GROUPS_SPS},
            {"teacher": "Mavlon", "groups": MAVLON_GROUPS}
        ]

        for teacher_entry in all_seed_data:
            t_id = teacher_map.get(teacher_entry["teacher"])
            if not t_id: 
                print(f"⚠️ Skipping data for {teacher_entry['teacher']} - profile not found")
                continue

            for group in teacher_entry["groups"]:
                # 1. Create Class
                existing_class = Class.query.filter_by(name=group["name"]).first()
                if not existing_class:
                    existing_class = Class(
                        name=group["name"], 
                        teacher_id=t_id,
                        schedule_days=group["schedule_days"],
                        schedule_time=group["schedule_time"]
                    )
                    db.session.add(existing_class)
                    db.session.flush()
                    print(f"🏫 Created Class: {group['name']}")

                # 2. Create Students
                for s_name in group["students"]:
                    base_username = s_name.lower().replace(" ", "_").replace("'", "")
                    username = base_username
                    counter = 1
                    while User.query.filter_by(username=username).first():
                        username = f"{base_username}{counter}"
                        counter += 1
                    
                    if not User.query.filter_by(full_name=s_name, role='student').join(Student).filter(Student.class_id==existing_class.id).first():
                        s_user = User(
                            username=username,
                            email=f"{username}@student.uz",
                            role='student',
                            full_name=s_name
                        )
                        s_user.set_password(f"{base_username}09") 
                        db.session.add(s_user)
                        db.session.flush()

                        s_profile = Student(user_id=s_user.id, class_id=existing_class.id)
                        db.session.add(s_profile)
                        print(f"👤 Created Student: {s_name} in {group['name']}")

        # Mark as seeded
        SystemSetting.set_val('sample_data_seeded', 'true', 'Flag to prevent duplicate sample seeding')
        db.session.commit()
        print("="*50)
        print("🎉 SAMPLE DATA SEEDING COMPLETE!")
        print("="*50 + "\n")

    def sync_schema():
        from sqlalchemy import text
        # Add missing columns for PostgreSQL safely
        tables_columns = {
            "teachers": [("daily_limit", "FLOAT DEFAULT 500.0")],
            "badges": [("requirement_text", "VARCHAR(255)")],
            "users": [
                ("block_reason", "VARCHAR(255)"),
                ("debt_amount", "FLOAT DEFAULT 0.0"),
                ("branch", "VARCHAR(50)") # Auto-add branch column
            ],
            "coin_transactions": [("teacher_id", "INTEGER REFERENCES teachers(id)")],
            "classes": [
                ("schedule_days", "VARCHAR(50)"),
                ("schedule_time", "VARCHAR(10)"),
                ("branch", "VARCHAR(50)") # Auto-add branch column
            ],
            "homework_submissions": [
                ("content", "TEXT"),
                ("image_url", "VARCHAR(500)"),
                ("admin_comment", "VARCHAR(255)")
            ],
            "homeworks": [
                ("teacher_id", "INTEGER REFERENCES teachers(id)"),
                ("class_id", "INTEGER REFERENCES classes(id)"),
                ("title", "VARCHAR(100)"),
                ("description", "TEXT"),
                ("xp_reward", "INTEGER DEFAULT 50"),
                ("deadline", "TIMESTAMP"),
                ("created_at", "TIMESTAMP")
            ],
            "topics": [
                ("class_id", "INTEGER REFERENCES classes(id)"),
                ("title", "VARCHAR(150)"),
                ("content", "TEXT")
            ],
            "attendance": [
                ("class_id", "INTEGER REFERENCES classes(id)"),
                ("student_id", "INTEGER REFERENCES students(id)"),
                ("date", "DATE"),
                ("status", "VARCHAR(20)")
            ]
        }
        
        for table, cols in tables_columns.items():
            for col_name, col_type in cols:
                try:
                    # Individual transaction for each column to prevent global rollback
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                    db.session.commit()
                    print(f"Schema Sync: Added column {col_name} to {table}")
                except Exception as e:
                    db.session.rollback()
                    err_str = str(e).lower()
                    if "duplicate column" in err_str or "already exists" in err_str:
                        # Log as info, not warning
                        pass 
                    else:
                        print(f"Schema Sync Warning for {table}.{col_name}: {e}")

    # Initialize Database if it doesn't exist
    with app.app_context():
        db.create_all()
        sync_schema() # Ensure existing tables have new columns
        
        # AUTO-FIX DATABASE SCHEMA (runs BEFORE seed_data to avoid column errors)
        from sqlalchemy import text
        
        # AUTO-FIX SHOP IMAGES DATABASE
        try:
            db.session.execute(text("ALTER TABLE shop_items ALTER COLUMN image_url TYPE TEXT"))
            db.session.commit()
            print("✅ AUTO-FIX: shop_items.image_url set to TEXT")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ AUTO-FIX: shop_items already correct or error: {str(e)}")
        
        # AUTO-FIX HOMEWORK IMAGES DATABASE
        try:
            db.session.execute(text("ALTER TABLE homework_submissions ALTER COLUMN image_url TYPE TEXT"))
            db.session.commit()
            print("✅ AUTO-FIX: homework_submissions.image_url set to TEXT")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ AUTO-FIX: homework_submissions already correct: {str(e)}")
        
        # AUTO-FIX PROFILE IMAGES (CRITICAL: Must run before seed_data)
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT"))
            db.session.commit()
            print("✅ AUTO-FIX: users.profile_image column added")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ AUTO-FIX: profile_image already exists: {str(e)}")
        
        # NOW seed data (after all schema fixes)
        try:
            seed_data()
        except Exception as e:
            print(f"⚠️ Seed Data Error (Skipping to keep server running): {str(e)}")
        
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(teacher_bp, url_prefix='/api/teacher')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(director_bp, url_prefix='/api/director')
    app.register_blueprint(coin_test_bp, url_prefix='/api/game')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(video_bp, url_prefix='/api/video')
    
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/login')
    def login_page():
        return send_from_directory(app.static_folder, 'login.html')

    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        """Serve uploaded files (e.g., shop item images)"""
        uploads_dir = os.path.join(app.static_folder, 'uploads')
        return send_from_directory(uploads_dir, filename)

    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        return {"msg": "Critical Server Error", "error": str(error), "trace": traceback.format_exc()}, 500

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
