from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.all_models import db, Teacher, Class, Student, CoinTransaction, Topic
from services.coin_engine import award_coins

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def teacher_dashboard():
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    
    if not teacher:
        return jsonify({"msg": "Teacher profile not found"}), 404
        
    classes = Class.query.filter_by(teacher_id=teacher.id).all()
    
    return jsonify({
        "teacher_name": teacher.user.full_name,
        "class_count": len(classes),
        "rating": teacher.rating,
        "classes": [{"id": c.id, "name": c.name, "student_count": len(c.students)} for c in classes]
    }), 200

@teacher_bp.route('/award-coins', methods=['POST'])
@jwt_required()
def teacher_award_coins():
    data = request.get_json()
    claims = get_jwt()
    
    if claims.get('role') != 'teacher':
        return jsonify({"msg": "Unauthorized"}), 403
        
    student_id = data.get('student_id')
    amount = data.get('amount')
    source = data.get('source', 'activity')
    
    success, msg = award_coins(student_id, amount, source)
    
    if success:
        return jsonify({"msg": msg}), 200
    return jsonify({"msg": msg}), 400

@teacher_bp.route('/classes/<int:class_id>', methods=['GET'])
@jwt_required()
def get_class_details(class_id):
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher: return jsonify({"msg": "Unauthorized"}), 403
    
    cls = Class.query.filter_by(id=class_id, teacher_id=teacher.id).first()
    if not cls: return jsonify({"msg": "Class not found or access denied"}), 404
    
    students_data = []
    for s in cls.students:
        students_data.append({
            "id": s.id,
            "full_name": s.user.full_name,
            "username": s.user.username,
            "balance": s.coin_balance,
            "rank": s.rank
        })
        
    return jsonify({
        "id": cls.id,
        "name": cls.name,
        "students": students_data
    }), 200

@teacher_bp.route('/attendance', methods=['POST'])
@jwt_required()
def mark_attendance():
    data = request.get_json()
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher: return jsonify({"msg": "Unauthorized"}), 403
    
    class_id = data.get('class_id')
    date_str = data.get('date') # YYYY-MM-DD
    records = data.get('records') # [{"student_id": 1, "status": "present"}, ...]
    
    if not records: return jsonify({"msg": "No records provided"}), 400
    
    # Optional: Verify class ownership
    cls = Class.query.filter_by(id=class_id, teacher_id=teacher.id).first()
    if not cls: return jsonify({"msg": "Class access denied"}), 403

    from models.all_models import Attendance
    from datetime import datetime
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
    
    count = 0
    from services.coin_engine import award_coins
    
    for rec in records:
        sid = rec.get('student_id')
        status = rec.get('status')
        
        # Check if exists to update
        existing = Attendance.query.filter_by(student_id=sid, class_id=class_id, date=date_obj).first()
        
        # If new or status changed to present, award coin
        coin_amount = float(rec.get('coins', 0))
        reason = "Davomat uchun"
        
        # If no custom amount specified, use default logic
        if 'coins' not in rec:
            if not existing and status == 'present':
                coin_amount = 1.0
            elif existing and existing.status != 'present' and status == 'present':
                coin_amount = 1.0
            else:
                coin_amount = 0.0

        if existing:
            existing.status = status
        else:
            new_att = Attendance(student_id=sid, class_id=class_id, date=date_obj, status=status)
            db.session.add(new_att)
        
        if coin_amount > 0:
            award_coins(sid, coin_amount, reason, f"O'qituvchi tomonidan darsda {status} deb belgilandi")
            
        count += 1
        
    db.session.commit()
    return jsonify({"msg": f"Davomat saqlandi ({count} o'quvchi)"}), 200

@teacher_bp.route('/classes/<int:class_id>/topics', methods=['POST'])
@jwt_required()
def add_topic(class_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher: return jsonify({"msg": "Unauthorized"}), 403
    
    cls = Class.query.filter_by(id=class_id, teacher_id=teacher.id).first()
    if not cls: return jsonify({"msg": "Class access denied"}), 403
    
    new_topic = Topic(
        class_id=class_id,
        title=data.get('title'),
        content=data.get('content')
    )
    db.session.add(new_topic)
    db.session.commit()
    return jsonify({"msg": "Mavzu qo'shildi"}), 201

@teacher_bp.route('/classes/<int:class_id>/topics', methods=['GET'])
@jwt_required()
def get_class_topics(class_id):
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher: return jsonify({"msg": "Unauthorized"}), 403
    
    cls = Class.query.filter_by(id=class_id, teacher_id=teacher.id).first()
    if not cls: return jsonify({"msg": "Class access denied"}), 403
    
    topics = Topic.query.filter_by(class_id=class_id).order_by(Topic.created_at.desc()).all()
    return jsonify([{
        "id": t.id,
        "title": t.title,
        "content": t.content,
        "date": t.created_at.strftime('%Y-%m-%d')
    } for t in topics]), 200
@teacher_bp.route('/classes/<int:class_id>/homework', methods=['POST'])
@jwt_required()
def add_homework(class_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher: return jsonify({"msg": "Unauthorized"}), 403
    
    cls = Class.query.filter_by(id=class_id, teacher_id=teacher.id).first()
    if not cls: return jsonify({"msg": "Class access denied"}), 403
    
    from models.all_models import Homework
    new_hw = Homework(
        class_id=class_id,
        title=data.get('title'),
        description=data.get('description'),
        xp_reward=data.get('xp_reward', 50)
    )
    db.session.add(new_hw)
    db.session.commit()
    return jsonify({"msg": "Uy ishi qo'shildi"}), 201

@teacher_bp.route('/classes/<int:class_id>/homework', methods=['GET'])
@jwt_required()
def get_homeworks(class_id):
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher: return jsonify({"msg": "Unauthorized"}), 403
    
    from models.all_models import Homework
    homeworks = Homework.query.filter_by(class_id=class_id).order_by(Homework.created_at.desc()).all()
    return jsonify([{
        "id": h.id,
        "title": h.title,
        "description": h.description,
        "xp_reward": h.xp_reward,
        "date": h.created_at.strftime('%Y-%m-%d')
    } for h in homeworks]), 200

@teacher_bp.route('/homework/<int:hw_id>/verify/<int:student_id>', methods=['POST'])
@jwt_required()
def verify_homework(hw_id, student_id):
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher: return jsonify({"msg": "Unauthorized"}), 403
    
    from models.all_models import Homework, HomeworkSubmission, Student
    from datetime import datetime, date, timedelta

    hw = Homework.query.get_or_404(hw_id)
    student = Student.query.get_or_404(student_id)
    
    # Check if already submitted/completed
    existing = HomeworkSubmission.query.filter_by(homework_id=hw_id, student_id=student_id).first()
    if existing and existing.status == 'completed':
        return jsonify({"msg": "Bu uy ishi allaqachon bajarilgan"}), 400
        
    if not existing:
        existing = HomeworkSubmission(homework_id=hw_id, student_id=student_id, status='completed')
        db.session.add(existing)
    else:
        existing.status = 'completed'
        existing.timestamp = datetime.utcnow()

    # Award XP
    student.xp += hw.xp_reward
    
    # Handle Streak
    today = date.today()
    if student.last_homework_date:
        if student.last_homework_date == today - timedelta(days=1):
            student.streak += 1
        elif student.last_homework_date < today - timedelta(days=1):
            student.streak = 1
        # if already today, streak doesn't increase but stays
    else:
        student.streak = 1
    
    student.last_homework_date = today
    
    # Update Rank if needed (Mock logic for now, can be expanded)
    if student.xp > 5000: student.rank = "Expert"
    elif student.xp > 2500: student.rank = "Advanced"
    elif student.xp > 1000: student.rank = "Intermediate"
    else: student.rank = "Newbie"

    db.session.commit()
    return jsonify({"msg": f"Uy ishi tasdiqlandi! +{hw.xp_reward} XP, Streak: {student.streak}"}), 200
