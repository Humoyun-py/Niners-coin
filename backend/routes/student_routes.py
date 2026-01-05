from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.all_models import db, Student, CoinTransaction, Notification, Complaint, ShopItem, Purchase, Topic
from services.coin_engine import spend_coins

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def student_dashboard():
    user_id = get_jwt_identity()
    claims = get_jwt()
    # print(f"DEBUG: student_dashboard call from user_id: {user_id}, role: {claims.get('role')}")
    student = Student.query.filter_by(user_id=user_id).first()
    
    if not student:
        return jsonify({"msg": "Student profile not linked to this user account. Please contact Admin if you are a student."}), 400
        
    # DAILY STREAK LOGIC
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    
    if student.last_streak_date:
        if student.last_streak_date == today - timedelta(days=1):
            # Yesterday was the last streak update, increment
            student.streak += 1
            student.last_streak_date = today
        elif student.last_streak_date < today - timedelta(days=1):
            # Missed a day, reset to 1
            student.streak = 1
            student.last_streak_date = today
        # if it was today, do nothing
    else:
        # First time streak logic
        student.streak = 1
        student.last_streak_date = today
    
    db.session.commit()

    recent_transactions = CoinTransaction.query.filter_by(student_id=student.id).order_by(CoinTransaction.timestamp.desc()).limit(5).all()
    
    return jsonify({
        "balance": student.coin_balance,
        "total_earned": student.total_earned,
        "rank": student.rank,
        "xp": student.xp,
        "streak": student.streak,
        "recent_activity": [
            {
                "amount": t.amount,
                "type": t.type,
                "source": t.source,
                "date": t.timestamp.isoformat()
            } for t in recent_transactions
        ]
    }), 200

@student_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        "id": n.id,
        "title": n.title,
        "message": n.message,
        "date": n.created_at.isoformat(),
        "is_read": n.is_read
    } for n in notifications]), 200

@student_bp.route('/test-notification', methods=['POST'])
@jwt_required()
def test_notification():
    user_id = get_jwt_identity()
    from services.security_service import send_notification
    send_notification(user_id, "Test Xabar", "Bu test xabarnoma! Tizim ishlayapti.")
    return jsonify({"msg": "Xabar yuborildi"}), 200

@student_bp.route('/notifications/<int:id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(id):
    user_id = get_jwt_identity()
    notification = Notification.query.filter_by(id=id, user_id=user_id).first()
    
    if notification:
        notification.is_read = True
        db.session.commit()
        return jsonify({"msg": "Marked as read"}), 200
    return jsonify({"msg": "Notification not found"}), 404

@student_bp.route('/complaints', methods=['POST'])
@jwt_required()
def submit_complaint():
    data = request.get_json()
    user_id = get_jwt_identity()
    new_complaint = Complaint(
        user_id=user_id,
        title=data.get('title'),
        message=data.get('message')
    )
    db.session.add(new_complaint)
    db.session.commit()
    return jsonify({"msg": "Shikoyatingiz qabul qilindi va ko'rib chiqiladi."}), 201

@student_bp.route('/shop/items', methods=['GET'])
@jwt_required()
def get_shop_items():
    items = ShopItem.query.filter(ShopItem.stock != 0).all() 
    return jsonify([{
        "id": i.id,
        "name": i.name,
        "price": i.price,
        "image_url": i.image_url,
        "stock": i.stock
    } for i in items]), 200

@student_bp.route('/shop/buy', methods=['POST'])
@jwt_required()
def buy_item():
    data = request.get_json()
    item_id = data.get('item_id')
    student = Student.query.filter_by(user_id=get_jwt_identity()).first()
    
    if not student: return jsonify({"msg": "Student not found"}), 404
    
    item = ShopItem.query.get_or_404(item_id)
    if item.stock == 0:
        return jsonify({"msg": "Item out of stock"}), 400
        
    success, msg = spend_coins(student.id, item.price, f"Bought {item.name}")
    if success:
        purchase = Purchase(
            student_id=student.id,
            item_id=item.id,
            price_at_purchase=item.price
        )
        if item.stock > 0:
            item.stock -= 1
            
        db.session.add(purchase)
        db.session.commit()
        return jsonify({"msg": "Xarid amalga oshirildi!"}), 200
    else:
        return jsonify({"msg": msg}), 400

@student_bp.route('/my-group/topics', methods=['GET'])
@jwt_required()
def get_my_topics():
    user_id = get_jwt_identity()
    # print(f"DEBUG: get_my_topics call from user_id: {user_id}")
    student = Student.query.filter_by(user_id=user_id).first()
    if not student or not student.class_id:
        return jsonify({"msg": "Siz guruhga biriktirilmagansiz"}), 404
        
    topics = Topic.query.filter_by(class_id=student.class_id).order_by(Topic.created_at.desc()).all()
    return jsonify([{
        "id": t.id,
        "title": t.title,
        "content": t.content,
        "date": t.created_at.strftime('%Y-%m-%d')
    } for t in topics]), 200
@student_bp.route('/my-class', methods=['GET'])
@jwt_required()
def get_my_class_details():
    user_id = get_jwt_identity()
    
    student = Student.query.filter_by(user_id=user_id).first()
    if not student or not student.class_id:
        return jsonify({"msg": "Siz guruhga biriktirilmagansiz"}), 404
    
    cls = student.student_class
    teacher_name = "Belgilanmagan"
    if cls.teacher_id:
        from models.all_models import Teacher
        teacher = Teacher.query.get(cls.teacher_id)
        if teacher: teacher_name = teacher.user.full_name
        
    classmates = []
    for s in cls.students:
        classmates.append({
            "id": s.id,
            "full_name": s.user.full_name,
            "rank": s.rank,
            "is_me": s.id == student.id
        })
        
    return jsonify({
        "class_name": cls.name,
        "teacher_name": teacher_name,
        "classmates": classmates
    }), 200

@student_bp.route('/my-badges', methods=['GET'])
@jwt_required()
def get_my_badges():
    user_id = get_jwt_identity()
    student = Student.query.filter_by(user_id=user_id).first()
    if not student: return jsonify({"msg": "Student not found"}), 404
    
    from models.all_models import Badge, StudentBadge
    
    all_badges = Badge.query.all()
    my_badges_rel = StudentBadge.query.filter_by(student_id=student.id).all()
    my_badge_ids = {b.badge_id for b in my_badges_rel}
    
    badges_data = []
    for b in all_badges:
        badges_data.append({
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "requirement_text": b.requirement_text,
            "icon": b.icon,
            "is_earned": b.id in my_badge_ids
        })
        
    return jsonify(badges_data), 200
