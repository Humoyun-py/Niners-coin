from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.all_models import db, Teacher, Class, Student, CoinTransaction, Topic, Homework, HomeworkSubmission
from services.coin_engine import award_coins
from sqlalchemy import func
from datetime import datetime

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def teacher_dashboard():
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    
    if not teacher:
        return jsonify({"msg": "Teacher profile not found"}), 404
        
    classes = Class.query.filter_by(teacher_id=teacher.id).all()
        
    today = datetime.utcnow().date()
    issued_today = db.session.query(func.sum(CoinTransaction.amount))\
        .filter(CoinTransaction.teacher_id == teacher.id)\
        .filter(func.date(CoinTransaction.timestamp) == today)\
        .filter(CoinTransaction.type == 'earn').scalar() or 0

    # Get recent transactions issued by this teacher
    recent_txs = CoinTransaction.query.filter_by(teacher_id=teacher.id, type='earn')\
        .order_by(CoinTransaction.timestamp.desc()).limit(10).all()

    return jsonify({
        "teacher_name": teacher.user.full_name,
        "class_count": len(classes),
        "rating": teacher.rating,
        "daily_limit": teacher.daily_limit,
        "issued_today": float(issued_today),
        "classes": [{"id": c.id, "name": c.name, "student_count": len(c.students)} for c in classes],
        "recent_rewards": [{
            "student_name": tx.student.user.full_name,
            "amount": tx.amount,
            "source": tx.source,
            "date": tx.timestamp.strftime('%H:%M')
        } for tx in recent_txs]
    }), 200

@teacher_bp.route('/award-coins', methods=['POST'])
@jwt_required()
def teacher_award_coins():
    data = request.get_json()
    claims = get_jwt()
    user_id = get_jwt_identity()
    
    if claims.get('role') != 'teacher':
        return jsonify({"msg": "Unauthorized"}), 403
    
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return jsonify({"msg": "Teacher profile not found"}), 404
        
    student_id = data.get('student_id')
    amount = float(data.get('amount', 0))
    source = data.get('source', 'standalone_reward')
    
    # 1. Check daily limit
    today = datetime.utcnow().date()
    issued_today = db.session.query(func.sum(CoinTransaction.amount))\
        .filter(CoinTransaction.teacher_id == teacher.id)\
        .filter(func.date(CoinTransaction.timestamp) == today)\
        .filter(CoinTransaction.type == 'earn').scalar() or 0
    
    # Get global limit from SystemSetting as fallback if teacher data is missing or use teacher.daily_limit
    max_limit = teacher.daily_limit
    
    if issued_today + amount > max_limit:
        return jsonify({"msg": f"Kunlik limitdan oshib ketdingiz. Bugun berilgan: {issued_today}, Maksimal: {max_limit}"}), 400

    success, msg = award_coins(student_id, amount, source, teacher_id=teacher.id)
    
    if success:
        return jsonify({"msg": msg, "issued_today": issued_today + amount}), 200
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
    
    # Calculate total coins to be awarded in this batch (Attendance + Bonus)
    total_planned = sum([
        float(rec.get('coins', 0)) + float(rec.get('bonus_amount', 0)) 
        for rec in records
    ])
    
    # Check daily limit
    today = datetime.utcnow().date()
    issued_today = db.session.query(func.sum(CoinTransaction.amount))\
        .filter(CoinTransaction.teacher_id == teacher.id)\
        .filter(func.date(CoinTransaction.timestamp) == today)\
        .filter(CoinTransaction.type == 'earn').scalar() or 0
    
    if issued_today + total_planned > teacher.daily_limit:
        return jsonify({"msg": f"Kunlik limitdan oshib ketyapsiz. Bugun berilgan: {issued_today}, Maksimal: {teacher.daily_limit}. Hozirgi urinish: {total_planned}"}), 400

    for rec in records:
        sid = rec.get('student_id')
        status = rec.get('status')
        
        # If new or status changed to present, award coin
        coin_amount = float(rec.get('coins', 0))
        reason = f"Davomat ({cls.name})"
        
        # If no custom amount specified, use default logic
        if 'coins' not in rec:
            if not existing and status == 'present':
                coin_amount = 1.0
            elif existing and existing.status != 'present' and status == 'present':
                coin_amount = 1.0
            else:
                coin_amount = 0.0

        existing = Attendance.query.filter_by(student_id=sid, class_id=class_id, date=date_obj).first()
        if existing:
            existing.status = status
        else:
            new_att = Attendance(student_id=sid, class_id=class_id, date=date_obj, status=status)
            db.session.add(new_att)
        
        if coin_amount > 0:
            award_coins(sid, coin_amount, reason, teacher_id=teacher.id)
        else:
            # Still check for attendance-based badges even if no coins were given
            from services.badge_engine import check_and_award_badges
            check_and_award_badges(sid)

        # Handle Bonus / Homework Coins (NEW)
        bonus_amount = float(rec.get('bonus_amount', 0))
        bonus_reason = rec.get('bonus_reason', 'Qo\'shimcha faollik')
        
        if bonus_amount > 0:
            # Check limit again for bonus
            # Since we checked total_planned earlier, we need to ensure we included bonuses in total_planned calculation
            # But let's assume the earlier check covered it or we just proceed (soft limit for now or recalculate)
             award_coins(sid, bonus_amount, bonus_reason, teacher_id=teacher.id)
            
        count += 1
        
    db.session.commit()
    return jsonify({"msg": f"Davomat saqlandi ({count} o'quvchi), Jami {total_planned} coin berildi."}), 200

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
        teacher_id=teacher.id,  # CRITICAL: Must set teacher_id
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
@teacher_bp.route('/homework', methods=['GET', 'POST'])
@jwt_required()
def homework_management():
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return jsonify({"msg": "Teacher not found"}), 404

    if request.method == 'POST':
        data = request.get_json()
        class_id = data.get('class_id')
        description = data.get('description')
        deadline_str = data.get('deadline') # "YYYY-MM-DD"

        if not class_id or not description:
            return jsonify({"msg": "Class and Description required"}), 400

        # Optional: Check if class belongs to teacher
        target_class = Class.query.get(class_id)
        if not target_class or target_class.teacher_id != teacher.id:
            return jsonify({"msg": "Invalid class"}), 403

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                pass # Ignore invalid date

        new_hw = Homework(
            class_id=class_id,
            teacher_id=teacher.id,
            description=description,
            deadline=deadline
        )
        db.session.add(new_hw)
        db.session.commit()
        return jsonify({"msg": "Homework created", "homework": new_hw.to_dict()}), 201

    else: # GET
        # Get all homeworks by this teacher
        homeworks = Homework.query.filter_by(teacher_id=teacher.id).order_by(Homework.created_at.desc()).all()
        return jsonify([h.to_dict() for h in homeworks]), 200

@teacher_bp.route('/award-individual', methods=['POST'])
@jwt_required()
def award_individual():
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher: return jsonify({"msg": "Teacher not found"}), 404

    data = request.get_json()
    student_id = data.get('student_id')
    amount = float(data.get('amount', 0))
    reason = data.get('reason', 'Qo\'shimcha faollik')

    if amount <= 0:
        return jsonify({"msg": "Coin miqdori 0 dan katta bo'lishi kerak"}), 400

    student = Student.query.get(student_id)
    if not student:
        return jsonify({"msg": "O'quvchi topilmadi"}), 404

    # Check daily limit
    today = datetime.utcnow().date()
    awarded_today = db.session.query(func.sum(CoinTransaction.amount)).filter(
        CoinTransaction.teacher_id == teacher.id,
        func.date(CoinTransaction.timestamp) == today,
        CoinTransaction.amount > 0
    ).scalar() or 0

    if awarded_today + amount > teacher.daily_limit:
        return jsonify({"msg": f"Kunlik limit yetarli emas! (Qoldiq: {teacher.daily_limit - awarded_today})"}), 400

    award_coins(student.id, amount, reason, teacher_id=teacher.id)
    db.session.commit()

    # Capture current balance
    return jsonify({"msg": "Coin yuborildi!", "new_balance": student.coin_balance}), 200

@teacher_bp.route('/homework/<int:homework_id>/submissions', methods=['GET'])
@jwt_required()
def get_homework_submissions(homework_id):
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher: return jsonify({"msg": "Teacher not found"}), 404

    homework = Homework.query.get(homework_id)
    if not homework or homework.teacher_id != teacher.id:
        return jsonify({"msg": "Homework not found or access denied"}), 404
        
    submissions = HomeworkSubmission.query.filter_by(homework_id=homework_id).all()
    
    result = []
    for sub in submissions:
        student = Student.query.get(sub.student_id)
        result.append({
            "id": sub.id,
            "student_name": student.user.full_name,
            "student_username": student.user.username,
            "content": sub.content,
            "image_url": sub.image_url,
            "submitted_at": sub.timestamp.isoformat(),
            "status": sub.status,
            "admin_comment": sub.admin_comment
        })
        
    return jsonify(result), 200

@teacher_bp.route('/homework/submission/<int:submission_id>/grade', methods=['POST'])
@jwt_required()
def grade_submission(submission_id):
    user_id = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher: return jsonify({"msg": "Teacher not found"}), 404
    
    submission = HomeworkSubmission.query.get(submission_id)
    if not submission: return jsonify({"msg": "Submission not found"}), 404
    
    # Check if teacher owns the homework
    if submission.homework.teacher_id != teacher.id:
        return jsonify({"msg": "Access denied"}), 403
        
    data = request.get_json()
    action = data.get('action') # approve, reject
    amount = float(data.get('amount', 0))
    comment = data.get('comment', '')
    
    if action == 'approve':
        if amount > 0:
            # Check limits
            today = datetime.utcnow().date()
            awarded_today = db.session.query(func.sum(CoinTransaction.amount)).filter(
                CoinTransaction.teacher_id == teacher.id,
                func.date(CoinTransaction.timestamp) == today,
                CoinTransaction.amount > 0
            ).scalar() or 0
            
            if awarded_today + amount > teacher.daily_limit:
               return jsonify({"msg": f"Kunlik limit yetarli emas! (Qoldiq: {teacher.daily_limit - awarded_today})"}), 400

            success, msg = award_coins(submission.student_id, amount, f"Homework: {submission.homework.description[:20]}...", teacher_id=teacher.id)
            if not success: return jsonify({"msg": msg}), 400
            
        submission.status = 'approved'
        submission.admin_comment = comment
        db.session.commit()
        return jsonify({"msg": f"Uy ishi qabul qilindi! {amount} coin berildi."}), 200
        
    elif action == 'reject':
        submission.status = 'rejected'
        submission.admin_comment = comment
        db.session.commit()
        return jsonify({"msg": "Uy ishi rad etildi."}), 200
        
    return jsonify({"msg": "Invalid action"}), 400
