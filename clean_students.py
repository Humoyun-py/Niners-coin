"""
Script to clean database - removes all students and Komron's classes
Run this before re-running seed_komron_students.py
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from models.all_models import db, User, Student, Teacher, Class
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("🧹 Cleaning database...")
    
    # Find Komron's teacher ID
    komron_user = User.query.filter_by(username='Komron').first()
    if komron_user:
        komron_teacher = Teacher.query.filter_by(user_id=komron_user.id).first()
        if komron_teacher:
            # Delete classes
            deleted_classes = Class.query.filter_by(teacher_id=komron_teacher.id).delete()
            print(f"✅ Deleted {deleted_classes} classes")
    
    # Delete all students
    deleted_students = Student.query.delete()
    print(f"✅ Deleted {deleted_students} student profiles")
    
    # Delete all student users
    deleted_users = User.query.filter_by(role='student').delete()
    print(f"✅ Deleted {deleted_users} student users")
    
    db.session.commit()
    print("\n🎉 Database cleaned! Now run: python seed_komron_students.py")
