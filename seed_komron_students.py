"""
One-time script to seed students and classes for Komron and Mavlon
Run this only ONCE to populate the database
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from models.all_models import db, User, Student, Teacher, Class

app = create_app()

# Data structure for KOMRON
KOMRON_GROUPS_DCJ = [
    {
        "name": "Komron - DCJ - 08:30 - Guruh 1",
        "schedule_days": "Dushanba|Chorshanba|Juma",
        "schedule_time": "08:30",
        "students": ["Bilol", "Nurmuhammad"]
    },
    {
        "name": "Komron - DCJ - 10:30 - Guruh 2",
        "schedule_days": "Dushanba|Chorshanba|Juma",
        "schedule_time": "10:30",
        "students": ["Mubina", "Sulaymon", "Iymona", "Hilola", "Asolat", "Asalxon", "Ezoza", "Ziyoda", "Munisa"]
    },
    {
        "name": "Komron - DCJ - 12:30 - Guruh 3",
        "schedule_days": "Dushanba|Chorshanba|Juma",
        "schedule_time": "12:30",
        "students": ["Abdulloh"]
    },
    {
        "name": "Komron - DCJ - 14:00 - Guruh 4",
        "schedule_days": "Dushanba|Chorshanba|Juma",
        "schedule_time": "14:00",
        "students": ["Madina", "Xadicha", "Gulnoza", "Robiya"]
    },
    {
        "name": "Komron - DCJ - 15:30 - Guruh 5",
        "schedule_days": "Dushanba|Chorshanba|Juma",
        "schedule_time": "15:30",
        "students": ["Shaxina", "Baxtinisso", "Gulbaxor", "Firdavs"]
    },
    {
        "name": "Komron - DCJ - 17:00 - Guruh 6",
        "schedule_days": "Dushanba|Chorshanba|Juma",
        "schedule_time": "17:00",
        "students": ["Mardon", "Odil", "Asadbek", "Rushana", "Abdulloh"]
    },
    {
        "name": "Komron - DCJ - 18:30 - Guruh 7",
        "schedule_days": "Dushanba|Chorshanba|Juma",
        "schedule_time": "18:30",
        "students": ["Bexruz", "Shaxina"]
    }
]

KOMRON_GROUPS_SPS = [
    {
        "name": "Komron - SPS - 10:00 - Guruh 1",
        "schedule_days": "Seshanba|Payshanba|Shanba",
        "schedule_time": "10:00",
        "students": ["Anasbek", "Xurshid", "Abdurahmon", "Shamshod", "Muhammadamin", "Momin", "Zebo", "Tamila", "Dilsora"]
    },
    {
        "name": "Komron - SPS - 14:00 - Guruh 2",
        "schedule_days": "Seshanba|Payshanba|Shanba",
        "schedule_time": "14:00",
        "students": ["Nigora"]
    },
    {
        "name": "Komron - SPS - 15:30 - Guruh 3",
        "schedule_days": "Seshanba|Payshanba|Shanba",
        "schedule_time": "15:30",
        "students": ["Dilshoda", "Abduvali", "Husan"]
    },
    {
        "name": "Komron - SPS - 17:00 - Guruh 4",
        "schedule_days": "Seshanba|Payshanba|Shanba",
        "schedule_time": "17:00",
        "students": ["Yerdana", "Artyom"]
    },
    {
        "name": "Komron - SPS - 18:30 - Guruh 5",
        "schedule_days": "Seshanba|Payshanba|Shanba",
        "schedule_time": "18:30",
        "students": ["Ilhom", "Davron", "Amir"]
    },
    {
        "name": "Komron - SPS - 20:00 - Guruh 6",
        "schedule_days": "Seshanba|Payshanba|Shanba",
        "schedule_time": "20:00",
        "students": ["Bilol"]
    }
]

KOMRON_ALL_GROUPS = KOMRON_GROUPS_DCJ + KOMRON_GROUPS_SPS

# Data structure for MAVLON
MAVLON_GROUPS = [
    {
        "name": "Mavlon - DCJ - 14:30 - Guruh 1",
        "schedule_days": "Dushanba|Chorshanba|Juma",
        "schedule_time": "14:30",
        "students": ["Kamron", "Afruza", "Zilola", "Muslima"]
    },
    {
        "name": "Mavlon - DCJ - 16:00 - Guruh 2",
        "schedule_days": "Dushanba|Chorshanba|Juma",
        "schedule_time": "16:00",
        "students": ["Mubina", "Usmon1", "Usmon2", "Shaxzoda"]
    }
]

# Combined data for all teachers
ALL_TEACHERS = [
    {"username": "Komron", "groups": KOMRON_ALL_GROUPS},
    {"username": "Mavlon", "groups": MAVLON_GROUPS}
]

with app.app_context():
    print("🚀 Starting student and class seeding...")
    
    total_created = 0
    total_classes = 0
    
    # Process each teacher
    for teacher_data in ALL_TEACHERS:
        teacher_username = teacher_data["username"]
        teacher_groups = teacher_data["groups"]
        
        print(f"\n👨‍🏫 Processing Teacher: {teacher_username}")
        
        # 1. Find teacher profile
        teacher_user = User.query.filter_by(username=teacher_username).first()
        if not teacher_user:
            print(f"  ❌ {teacher_username} user not found! Skipping...")
            continue
        
        teacher_profile = Teacher.query.filter_by(user_id=teacher_user.id).first()
        if not teacher_profile:
            print(f"  ❌ {teacher_username} teacher profile not found! Skipping...")
            continue
        
        print(f"  ✅ Found teacher: {teacher_user.full_name} (ID: {teacher_profile.id})")
        
        created_students = {}
        created_count = 0
        
        # 2. Process each group for this teacher
        for group_idx, group_data in enumerate(teacher_groups, 1):
            print(f"\n📚 Processing: {group_data['name']}")
        
            # Create or find class
            existing_class = Class.query.filter_by(
                name=group_data['name'],
                teacher_id=teacher_profile.id
            ).first()
        
            if existing_class:
                print(f"    ⚠️  Class already exists, using existing")
                target_class = existing_class
            else:
                target_class = Class(
                    name=group_data['name'],
                    teacher_id=teacher_profile.id,
                    schedule_days=group_data['schedule_days'],
                    schedule_time=group_data['schedule_time']
                )
                db.session.add(target_class)
                db.session.flush()
                print(f"    ✅ Created class: {target_class.name}")
                total_classes += 1
        
            # 3. Create students and assign to class
            for student_name in group_data['students']:
                # Create unique username (handle duplicates by adding numbers)
                base_username = student_name.lower()
                username = base_username
                counter = 1
                
                # Check if user with this name already exists (for any role or duplicate names)
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create User
                new_user = User(
                    username=username,
                    email=f"{username}@student.niners.uz",
                    role='student',
                    full_name=student_name
                )
                new_user.set_password(f"{base_username}09")
                db.session.add(new_user)
                db.session.flush()
                
                # Create Student profile
                new_student = Student(
                    user_id=new_user.id,
                    class_id=target_class.id,
                    coin_balance=0.0,
                    rank="Newbie"
                )
                db.session.add(new_student)
                db.session.flush()
                
                created_count += 1
                total_created += 1
                
                # Show if this is a duplicate name
                suffix = "" if counter == 1 else f" (as {username})"
                print(f"      ✅ Created student: {student_name}{suffix} (username: {username}, password: {base_username}09)")
        
        print(f"  📊 {teacher_username}: Created {created_count} students")
        
    # Commit all changes
    db.session.commit()
    print(f"\n🎉 DONE! Total: {total_created} students across {total_classes} classes")
    print(f"� Teachers processed: {len(ALL_TEACHERS)}")
