import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app import create_app
from backend.models.all_models import db, User, Class, Student, Teacher, Homework, HomeworkSubmission, Attendance, Topic
from datetime import datetime

def test_delete_logic():
    app = create_app()
    with app.app_context():
        print("--- Setting up Test Data ---")
        
        # 1. Create Teacher
        t_user = User(username='test_t', role='teacher', full_name='T Teacher')
        db.session.add(t_user)
        db.session.flush()
        teacher = Teacher(user_id=t_user.id)
        db.session.add(teacher)
        db.session.flush()
        
        # 2. Create Class
        cls = Class(name='Test Class', teacher_id=teacher.id)
        db.session.add(cls)
        db.session.flush()
        
        # 3. Create Student
        s_user = User(username='test_s', role='student', full_name='S Student')
        db.session.add(s_user)
        db.session.flush()
        student = Student(user_id=s_user.id, class_id=cls.id)
        db.session.add(student)
        db.session.flush()
        
        # 4. Create Homework & Submission
        hw = Homework(class_id=cls.id, teacher_id=teacher.id, description='Test HW')
        db.session.add(hw)
        db.session.flush()
        
        sub = HomeworkSubmission(homework_id=hw.id, student_id=student.id, content='Ans')
        db.session.add(sub)
        
        # 5. Create Topic
        topic = Topic(class_id=cls.id, title='Test Topic', content='Content')
        db.session.add(topic)
        
        # 6. Create Attendance
        att = Attendance(student_id=student.id, class_id=cls.id, status='present', date=datetime.utcnow().date())
        db.session.add(att)
        
        db.session.commit()
        print(f"Created Class {cls.id}, Student {student.id}, HW {hw.id}")
        
        # --- TEST DELETE CLASS ---
        print("\n--- Testing Delete Class ---")
        try:
            # Simulate logic from admin_routes.delete_class
            c_to_del = Class.query.get(cls.id)
            if c_to_del:
                # 1. Detach students
                for s in c_to_del.students:
                    s.class_id = None
                
                # 2. Delete Class-Specific Data
                Attendance.query.filter_by(class_id=c_to_del.id).delete()
                Topic.query.filter_by(class_id=c_to_del.id).delete()
                
                homeworks = Homework.query.filter_by(class_id=c_to_del.id).all()
                for h in homeworks:
                    HomeworkSubmission.query.filter_by(homework_id=h.id).delete()
                    db.session.delete(h)
                    
                db.session.delete(c_to_del)
                db.session.commit()
                print("✅ Delete Class Success!")
            else:
                print("Class not found (already deleted?)")
                
        except Exception as e:
            print(f"❌ Delete Class Failed: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    test_delete_logic()
