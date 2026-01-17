from flask import Blueprint, jsonify, request, Response, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.all_models import (
    db, User, Student, Teacher, Parent, Class, AuditLog, Complaint, ApprovalRequest, 
    ShopItem, Purchase, Badge, StudentBadge, CoinTransaction, Test, TestResult, 
    Homework, HomeworkSubmission, Attendance, Notification, Topic, SystemSetting
)
from services.report_generator import generate_student_report, generate_student_pdf_report, generate_classroom_indicators
from services.security_service import log_event
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def check_admin():
    claims = get_jwt()
    if claims.get('role') not in ['admin', 'director']:
        return False
    return True

@admin_bp.route('/upload-image', methods=['POST'])
@jwt_required()
def upload_image():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    
    if 'image' not in request.files:
        return jsonify({"msg": "No file part"}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400
        
    if file:
        filename = secure_filename(file.filename)
        # Unique filename using timestamp
        import time
        filename = f"{int(time.time())}_{filename}"
        
        # Absolute path relative to backend/routes/../.. -> root
        # We assume root is where app.py is, and frontend is in root/frontend
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        upload_dir = os.path.join(base_dir, 'frontend', 'uploads', 'shop')
        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        upload_path = os.path.join(upload_dir, filename)
        file.save(upload_path)
        
        # Return the public URL path
        return jsonify({"url": f"/uploads/shop/{filename}"}), 200

@admin_bp.route('/debug/fix-homework-schema', methods=['GET'])
@jwt_required()
def fix_homework_schema():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    results = []
    try:
        from sqlalchemy import text
        # Columns to ensure exist
        columns = [
            ("teacher_id", "INTEGER REFERENCES teachers(id)"),
            ("class_id", "INTEGER REFERENCES classes(id)"),
            ("title", "VARCHAR(100)"),
            ("description", "TEXT"),
            ("xp_reward", "INTEGER DEFAULT 50"),
            ("deadline", "TIMESTAMP"),
            ("created_at", "TIMESTAMP")
        ]
        
        for col_name, col_type in columns:
            try:
                db.session.execute(text(f"ALTER TABLE homeworks ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
                results.append(f"✅ Added {col_name}")
            except Exception as e:
                db.session.rollback()
                results.append(f"⚠️ Failed to add {col_name}: {str(e)}") # Likely already exists
        
        return jsonify({"msg": "Schema update attempted", "details": results}), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@admin_bp.route('/complaints', methods=['GET'])
@jwt_required()
def get_complaints():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return jsonify([{
        "id": c.id,
        "title": c.title,
        "message": c.message,
        "status": c.status,
        "username": User.query.get(c.user_id).username if c.user_id else "User",
        "timestamp": c.created_at.isoformat()
    } for c in complaints]), 200

@admin_bp.route('/complaints/<int:complaint_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_complaint(complaint_id):
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    complaint = Complaint.query.get_or_404(complaint_id)
    complaint.status = 'resolved'
    db.session.commit()
    return jsonify({"msg": "Shikoyat ijobiy hal qilindi"}), 200

@admin_bp.route('/approval-requests', methods=['POST'])
@jwt_required()
def create_approval_request():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    data = request.get_json()
    new_req = ApprovalRequest(
        admin_id=get_jwt_identity(),
        title=data.get('title'),
        description=data.get('description')
    )
    db.session.add(new_req)
    db.session.commit()
    return jsonify({"msg": "So'rov direktorga yuborildi"}), 201

@admin_bp.route('/payment-check', methods=['POST'])
@jwt_required()
def run_payment_check():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    
    # Block ALL students
    all_students = Student.query.all()
    count = 0
    for s in all_students:
        if s.user and s.user.is_active:
            s.user.is_active = False
            s.user.block_reason = "To'lov qilingmagan"
            s.user.debt_amount = 650000.0
            s.payment_status = 'pending'
            log_event(None, f"Qo'lda hamma uchun blok: {s.user.username}", severity='danger')
            count += 1
    db.session.commit()
    return jsonify({"msg": f"{count} ta o'quvchi to'lov uchun bloklandi"}), 200

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    try:
        role_filter = request.args.get('role', 'all')
        
        query = User.query
        if role_filter != 'all':
            query = query.filter_by(role=role_filter)
            
        users = query.all()
        result = []
        for u in users:
            try:
                # Safe access to teacher_profile
                limit = None
                if u.role == 'teacher' and u.teacher_profile:
                    limit = u.teacher_profile.daily_limit
                
                result.append({
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "role": u.role,
                    "full_name": u.full_name,
                    "is_active": u.is_active,
                    "block_reason": u.block_reason,
                    "debt_amount": u.debt_amount,
                    "coin_balance": u.student_profile.coin_balance if u.student_profile else 0.0,
                    "daily_limit": limit
                })
            except Exception as e:
                print(f"Skipping user {u.id} due to serialization error: {e}")
        return jsonify(result), 200
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN get_users AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"Server Error in users: {str(e)}"}), 500

@admin_bp.route('/debug/schema', methods=['GET'])
@jwt_required()
def debug_schema():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        homework_cols = []
        if 'homeworks' in tables:
            homework_cols = [c['name'] for c in inspector.get_columns('homeworks')]
            
        return jsonify({
            "tables": tables,
            "homework_columns": homework_cols,
            "has_teacher_id": "teacher_id" in homework_cols,
            "db_url_masked": app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else "local"
        }), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@admin_bp.route('/debug/fix-students', methods=['GET'])
@jwt_required()
def fix_students():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    try:
        # Unblock ALL students
        students = Student.query.all()
        count = 0
        for s in students:
            if s.user:
                s.user.is_active = True
                s.user.block_reason = None
                # Optional: s.user.set_password(f"{s.user.username}09") # Force reset passwords if needed
                count += 1
        
        db.session.commit()
        return jsonify({"msg": f"Success! {count} students unblocked."}), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@admin_bp.route('/users', methods=['POST'])
@jwt_required()
def add_user():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    try:
        data = request.get_json()
        
        if User.query.filter_by(username=data.get('username')).first():
            return jsonify({"msg": "Username band"}), 400
        
        new_user = User(
            username=data.get('username'),
            email=data.get('email', f"{data.get('username')}@niners.uz"),
            role=data.get('role', 'student'),
            full_name=data.get('full_name')
        )
        new_user.set_password(data.get('password', '123456')) # Default password
        
        db.session.add(new_user)
        db.session.flush()
        
        profile = None
        if new_user.role == 'student':
            profile = Student(user_id=new_user.id, class_id=data.get('class_id'))
        elif new_user.role == 'teacher':
            try:
                limit_val = data.get('daily_limit', 500)
                if not limit_val: limit_val = 500
                daily_limit = float(limit_val)
            except:
                daily_limit = 500.0
                
            profile = Teacher(
                user_id=new_user.id, 
                subject=data.get('subject'),
                daily_limit=daily_limit
            )
        elif new_user.role == 'parent':
            profile = Parent(user_id=new_user.id)
        
        if profile:
            db.session.add(profile)
            
        db.session.commit()
        log_event(get_jwt_identity(), f"Yangi foydalanuvchi qo'shildi: {new_user.username} ({new_user.role})")
        return jsonify({"msg": "Muvaffaqiyatli qo'shildi", "id": new_user.id}), 201
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN add_user AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"User creation error: {str(e)}"}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    
    user.full_name = data.get('full_name', user.full_name)
    user.email = data.get('email', user.email)
    
    if data.get('password'):
        user.set_password(data.get('password'))
        
    # Profile specific updates
    if user.role == 'student' and user.student_profile:
        user.student_profile.class_id = data.get('class_id', user.student_profile.class_id)
    elif user.role == 'teacher' and user.teacher_profile:
        user.teacher_profile.subject = data.get('subject', user.teacher_profile.subject)
        if 'daily_limit' in data:
            user.teacher_profile.daily_limit = float(data['daily_limit'])
        
    log_event(get_jwt_identity(), f"Foydalanuvchi ma'lumotlari yangilandi: {user.username}")
    db.session.commit()
    return jsonify({"msg": "Ma'lumotlar yangilandi"}), 200

@admin_bp.route('/classes/<int:class_id>/students', methods=['POST'])
@jwt_required()
def add_student_to_class(class_id):
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    data = request.get_json()
    
    student = None
    if 'student_id' in data:
        student = Student.query.get(data['student_id']) # directly via ID
        if not student:
             # fallback if it's user_id
            student = Student.query.filter_by(user_id=data['student_id']).first()
    elif 'username' in data:
        user = User.query.filter_by(username=data['username']).first()
        if user and user.role == 'student':
            student = user.student_profile
 
    if not student:
        return jsonify({"msg": "Student topilmadi"}), 404
        
    student.class_id = class_id
    db.session.commit()
    log_event(get_jwt_identity(), f"Student {student.user.username} {class_id}-sinfga qo'shildi")
    return jsonify({"msg": "Student sinfga biriktirildi"}), 200

@admin_bp.route('/users/<int:user_id>/toggle-block', methods=['POST'])
@jwt_required()
def toggle_block(user_id):
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    
    # Check if we are trying to block an admin or director
    if user.is_active and user.role in ['admin', 'director']:
        return jsonify({"msg": "Administrator yoki Direktorni bloklash taqiqlangan"}), 400

    user.is_active = not user.is_active
    if not user.is_active:
        user.block_reason = data.get('reason', 'Sabab ko\'rsatilmadi')
        user.debt_amount = float(data.get('debt', 0.0))
    else:
        # Clear block info when unblocking
        user.block_reason = None
        user.debt_amount = 0.0

    action = "bloklandi" if not user.is_active else "blokdan chiqarildi"
    log_event(get_jwt_identity(), f"Foydalanuvchi {user.username} {action}. Sabab: {user.block_reason}, Qarz: {user.debt_amount}", severity='warning')
    db.session.commit()
    return jsonify({"msg": f"Foydalanuvchi {action}", "is_active": user.is_active}), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting Admins or Directors
    if user.role in ['admin', 'director']:
        return jsonify({"msg": "Admin yoki Direktorni o'chirish mumkin emas!"}), 400
        
    try:
        # Cascade Delete Manually
        try:
             Complaint.query.filter_by(user_id=user.id).delete()
             Notification.query.filter_by(user_id=user.id).delete()
             AuditLog.query.filter_by(user_id=user.id).delete()
             ApprovalRequest.query.filter_by(admin_id=user.id).delete()
        except Exception as e:
             # Just log common cleanup errors
             print(f"Common cleanup warning: {str(e)}")
        
        # B. Student Specific
        if user.role == 'student' and user.student_profile:
            try:
                student = user.student_profile
                # 1. Delete Badges & Purchases
                StudentBadge.query.filter_by(student_id=student.id).delete()
                Purchase.query.filter_by(student_id=student.id).delete()
                
                # 2. Coins
                CoinTransaction.query.filter_by(student_id=student.id).delete()
                
                # 3. Delete Academic Records
                Attendance.query.filter_by(student_id=student.id).delete()
                HomeworkSubmission.query.filter_by(student_id=student.id).delete()
                TestResult.query.filter_by(student_id=student.id).delete()
                
                db.session.delete(student)
                
                db.session.delete(student)
            except Exception as e:
                 # Ignore cleanup errors (e.g. missing columns) and proceed
                 print(f"Student cleanup warning: {str(e)}")

        # C. Teacher Specific
        if user.role == 'teacher' and user.teacher_profile:
            try:
                teacher = user.teacher_profile
                # 1. Unlink Classes
                classes = Class.query.filter_by(teacher_id=teacher.id).all()
                for c in classes:
                    c.teacher_id = None
                
                # 2. Delete Teacher's content
                # Delete Tests and Results
                tests = Test.query.filter_by(teacher_id=teacher.id).all()
                for t in tests:
                    TestResult.query.filter_by(test_id=t.id).delete()
                    db.session.delete(t)
                    
                # Delete Homeworks
                homeworks = Homework.query.filter_by(teacher_id=teacher.id).all()
                for h in homeworks:
                    HomeworkSubmission.query.filter_by(homework_id=h.id).delete()
                    db.session.delete(h)

                CoinTransaction.query.filter_by(teacher_id=teacher.id).delete()
                db.session.delete(teacher)
            except Exception as e:
                 # Ignore cleanup errors (e.g. missing columns) and proceed
                 print(f"Teacher cleanup warning: {str(e)}")

        # D. Parent Specific
        if user.role == 'parent' and user.parent_profile:
            db.session.delete(user.parent_profile)

        db.session.delete(user)
        db.session.commit()
        log_event(get_jwt_identity(), f"Foydalanuvchi o'chirildi: {user.username}", severity='danger')
        return jsonify({"msg": "Foydalanuvchi muvaffaqiyatli o'chirildi"}), 200

    except Exception as e:
        db.session.rollback()
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- DELETE ERROR {user_id} --- {datetime.utcnow()}\n{error_msg}\n")
        return jsonify({"msg": f"O'chirishda xatolik: {str(e)}"}), 500

@admin_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_classes():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    try:
        classes = Class.query.all()
        result = []
        for c in classes:
            teacher_name = "Belgilanmagan"
            if c.teacher_id:
                teacher = Teacher.query.get(c.teacher_id)
                if teacher and teacher.user:
                    teacher_name = teacher.user.full_name
            
            result.append({
                "id": c.id,
                "name": c.name,
                "teacher_id": c.teacher_id,
                "teacher_name": teacher_name,
                "student_count": len(c.students),
                "students_list": [{"id": s.user.id, "name": s.user.full_name} for s in c.students if s.user],
                "schedule_days": c.schedule_days,
                "schedule_time": c.schedule_time
            })
        return jsonify(result), 200
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN get_classes AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"Server Error in classes: {str(e)}"}), 500

@admin_bp.route('/classes', methods=['POST'])
@jwt_required()
def create_class():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    data = request.get_json()
    teacher_user_id = data.get('teacher_id') # Usually User ID from frontend
    
    teacher = Teacher.query.filter_by(user_id=teacher_user_id).first()
    if not teacher:
        # Maybe it IS a Teacher.id
        teacher = Teacher.query.get(teacher_user_id)
        
    new_class = Class(
        name=data.get('name'), 
        teacher_id=teacher.id if teacher else None,
        schedule_days=data.get('schedule_days'),
        schedule_time=data.get('schedule_time')
    )
    db.session.add(new_class)
    db.session.commit()
    log_event(get_jwt_identity(), f"Yangi sinf yaratildi: {new_class.name}")
    return jsonify({"msg": "Sinf yaratildi"}), 201

@admin_bp.route('/classes/<int:class_id>', methods=['PUT'])
@jwt_required()
def update_class(class_id):
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    data = request.get_json()
    cls = Class.query.get_or_404(class_id)
    
    cls.name = data.get('name', cls.name)
    cls.schedule_days = data.get('schedule_days', cls.schedule_days)
    cls.schedule_time = data.get('schedule_time', cls.schedule_time)
    
    teacher_user_id = data.get('teacher_id')
    if teacher_user_id:
        teacher = Teacher.query.filter_by(user_id=teacher_user_id).first()
        if not teacher:
            teacher = Teacher.query.get(teacher_user_id)
        if teacher:
            cls.teacher_id = teacher.id
            
    db.session.commit()
    log_event(get_jwt_identity(), f"Sinf ma'lumotlari yangilandi: {cls.name}")
    return jsonify({"msg": "Sinf yangilandi"}), 200

@admin_bp.route('/classes/<int:class_id>', methods=['DELETE'])
@jwt_required()
def delete_class(class_id):
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    cls = Class.query.get_or_404(class_id)
    
    try:
        from sqlalchemy.exc import ProgrammingError, OperationalError
        
        # 1. Detach students (Robust)
        try:
            for s in cls.students:
                s.class_id = None
        except Exception:
            pass # Ignore detach errors
            
        # 2. Delete Class-Specific Data (Robust)
        try:
            from models.all_models import Attendance, Topic, Homework, HomeworkSubmission
            
            # Delete Attendance
            try:
                Attendance.query.filter_by(class_id=cls.id).delete()
            except (ProgrammingError, OperationalError):
                db.session.rollback()

            # Delete Topics
            try:
                Topic.query.filter_by(class_id=cls.id).delete()
            except (ProgrammingError, OperationalError):
                db.session.rollback()

            # Delete Homework and Submissions
            try:
                homeworks = Homework.query.filter_by(class_id=cls.id).all()
                for hw in homeworks:
                    try:
                        HomeworkSubmission.query.filter_by(homework_id=hw.id).delete()
                        db.session.delete(hw)
                    except:
                        pass
            except (ProgrammingError, OperationalError):
                 db.session.rollback()
                 
        except Exception as e:
            print(f"Cleanup non-critical error: {e}")
            
        db.session.delete(cls)
        db.session.commit()
        log_event(get_jwt_identity(), f"Sinf o'chirildi: {cls.id}", severity='danger')
        return jsonify({"msg": "Sinf o'chirildi"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"General delete failed: {str(e)}"}), 500

@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    try:
        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
        result = []
        for l in logs:
            user_name = "System"
            if l.user_id:
                u = User.query.get(l.user_id)
                if u: 
                    user_name = u.username # Frontend expects 'username' in audit-logs.html
                else:
                    user_name = f"User {l.user_id} (Deleted)"
            
            result.append({
                "id": l.id,
                "action": l.action,
                "username": user_name, # Renamed for frontend compatibility
                "severity": l.severity,
                "timestamp": l.timestamp.isoformat()
            })
        return jsonify(result), 200
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN get_audit_logs AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"Audit logs error: {str(e)}"}), 500

@admin_bp.route('/users/<int:user_id>/adjust-coins', methods=['POST'])
@jwt_required()
def adjust_coins(user_id):
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    data = request.get_json()
    try:
        amount = int(data.get('amount', 0)) # Ensure int
    except:
        return jsonify({"msg": "Noto'g'ri miqdor"}), 400
        
    reason = data.get('reason', 'Admin tuzatish')
    
    user = User.query.get_or_404(user_id)
    if user.role != 'student' or not user.student_profile:
        return jsonify({"msg": "Faqat studentlar coinlarini o'zgartirish mumkin"}), 400
        
    from services.coin_engine import award_coins
    
    # Passing negative amount works fine in award_coins as it just adds
    success, msg = award_coins(user.student_profile.id, amount, f"Admin: {reason}")
    
    if success:
        log_event(get_jwt_identity(), f"{user.username} balansi {amount} ga o'zgartirildi ({reason})", severity='warning')
        return jsonify({"msg": "Coinlar muvaffaqiyatli o'zgartirildi", "new_balance": user.student_profile.coin_balance}), 200
    else:
        return jsonify({"msg": msg}), 400

@admin_bp.route('/shop/items', methods=['GET'])
@jwt_required()
def get_shop_items():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    items = ShopItem.query.all()
    return jsonify([{
        "id": i.id,
        "name": i.name,
        "price": i.price,
        "stock": i.stock,
        "image_url": i.image_url
    } for i in items]), 200

@admin_bp.route('/shop/items', methods=['POST'])
@jwt_required()
def add_shop_item():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    data = request.get_json()
    new_item = ShopItem(
        name=data.get('name'),
        description=data.get('description'),
        price=data.get('price'),
        image_url=data.get('image_url'),
        stock=data.get('stock', -1)
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({"msg": "Item added"}), 201

@admin_bp.route('/shop/items/<int:item_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_shop_item(item_id):
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    item = ShopItem.query.get_or_404(item_id)
    
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({"msg": "Item deleted"}), 200
        
    data = request.get_json()
    item.name = data.get('name', item.name)
    item.price = data.get('price', item.price)
    item.stock = data.get('stock', item.stock)
    item.image_url = data.get('image_url', item.image_url)
    db.session.commit()
    return jsonify({"msg": "Item updated"}), 200

@admin_bp.route('/shop/history', methods=['GET'])
@jwt_required()
def get_purchase_history():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    try:
        purchases = Purchase.query.order_by(Purchase.timestamp.desc()).limit(50).all()
        result = []
        for p in purchases:
            result.append({
                "id": p.id,
                "student": p.student.user.full_name if (p.student and p.student.user) else "Unknown Student",
                "item": p.item.name if p.item else "Unknown Item",
                "price": p.price_at_purchase,
                "date": p.timestamp.strftime('%Y-%m-%d %H:%M')
            })
        return jsonify(result), 200
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN get_purchase_history AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"Purchase history error: {str(e)}"}), 500

# BADGE MANAGEMENT FROM ADMIN PANEL
from models.all_models import Badge, StudentBadge

@admin_bp.route('/badges', methods=['GET'])
@jwt_required()
def get_all_badges():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    try:
        badges = Badge.query.all()
        return jsonify([{
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "requirement_text": b.requirement_text,
            "icon": b.icon
        } for b in badges]), 200
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN get_all_badges AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"Badges error: {str(e)}"}), 500

@admin_bp.route('/badges', methods=['POST'])
@jwt_required()
def add_badge():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    data = request.get_json()
    new_badge = Badge(
        name=data.get('name'),
        description=data.get('description'),
        requirement_text=data.get('requirement_text'),
        icon=data.get('icon')
    )
    db.session.add(new_badge)
    db.session.commit()
    log_event(get_jwt_identity(), f"Yangi nishon yaratildi: {new_badge.name}")
    return jsonify({"msg": "Badge created successfully"}), 201

@admin_bp.route('/badges/<int:badge_id>', methods=['DELETE'])
@jwt_required()
def delete_badge(badge_id):
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    badge = Badge.query.get_or_404(badge_id)
    # Delete assigned student badges first? Or Cascade? 
    # SQLAlchemy default might vary, let's allow explicit delete
    StudentBadge.query.filter_by(badge_id=badge.id).delete()
    
    db.session.delete(badge)
    db.session.commit()
    return jsonify({"msg": "Badge deleted"}), 200

@admin_bp.route('/badges/assign', methods=['POST'])
@jwt_required()
def assign_badge_manually():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    data = request.get_json()
    student_id = data.get('student_id')
    badge_id = data.get('badge_id')
    
    exists = StudentBadge.query.filter_by(student_id=student_id, badge_id=badge_id).first()
    if exists:
        return jsonify({"msg": "Student already has this badge"}), 400
        
    sb = StudentBadge(student_id=student_id, badge_id=badge_id)
    db.session.add(sb)
    db.session.commit()
    return jsonify({"msg": "Badge assigned to student"}), 200

@admin_bp.route('/export/students/csv', methods=['GET'])
@jwt_required()
def export_students_csv():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    csv_data = generate_student_report()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=students_report.csv"}
    )

@admin_bp.route('/export/students/pdf', methods=['GET'])
@jwt_required()
def export_students_pdf():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    pdf_buffer = generate_student_pdf_report()
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="students_report.pdf",
        mimetype="application/pdf"
    )

@admin_bp.route('/reports/classroom-indicators', methods=['GET'])
@jwt_required()
def get_classroom_indicators():
    if not check_admin(): return jsonify({"msg": "Forbidden"}), 403
    data = generate_classroom_indicators()
    return jsonify(data), 200


