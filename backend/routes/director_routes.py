from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.all_models import db, User, Teacher, Student, ApprovalRequest, AuditLog, CoinTransaction, Class, SystemSetting
from services.security_service import log_event
from sqlalchemy import func
from datetime import datetime, timedelta

director_bp = Blueprint('director', __name__)

@director_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    claims = get_jwt()
    if claims.get('role') != 'director': return jsonify({"msg": "Forbidden"}), 403

    try:
        # 1. Class Activity (Coins earned per class)
        # Using a join between Class, Student, and CoinTransaction
        class_stats = db.session.query(
            Class.name,
            func.sum(CoinTransaction.amount).label('total_coins')
        ).join(Student, Class.id == Student.class_id)\
         .join(CoinTransaction, Student.id == CoinTransaction.student_id)\
         .filter(CoinTransaction.type == 'earn')\
         .group_by(Class.name).all()

        # 2. Coin Circulation (Last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        circulation = db.session.query(
            func.date(CoinTransaction.timestamp).label('date'),
            func.sum(CoinTransaction.amount).label('total')
        ).filter(CoinTransaction.timestamp >= thirty_days_ago)\
         .group_by(func.date(CoinTransaction.timestamp))\
         .order_by(func.date(CoinTransaction.timestamp)).all()

        # 3. Overall Stats
        stats = {
            "total_coins_awarded": db.session.query(func.sum(CoinTransaction.amount)).filter(CoinTransaction.type == 'earn').scalar() or 0,
            "total_active_students": Student.query.count(),
            "total_teachers": Teacher.query.count(),
            "active_classes": Class.query.count()
        }

        return jsonify({
            "class_activity": [{"name": s[0], "value": float(s[1] or 0)} for s in class_stats],
            "circulation": [{"date": str(c[0]), "value": float(c[1] or 0)} for c in circulation],
            "stats": stats
        }), 200
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN get_analytics AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"Analytics error: {str(e)}"}), 500

@director_bp.route('/teachers-rating', methods=['GET'])
@jwt_required()
def get_teachers_rating():
    claims = get_jwt()
    if claims.get('role') != 'director': return jsonify({"msg": "Forbidden"}), 403

    try:
        teachers = Teacher.query.all()
        results = []
        for t in teachers:
            # SAFETY CHECK: If teacher has no user, skip or use placeholder
            if not t.user:
                print(f"Skipping teacher ID {t.id} - no associated user record")
                continue

            coins_given = db.session.query(func.sum(CoinTransaction.amount))\
                .filter(CoinTransaction.teacher_id == t.id)\
                .filter(CoinTransaction.type == 'earn').scalar() or 0

            results.append({
                "id": t.id,
                "name": t.user.full_name,
                "subject": t.subject,
                "rating": t.rating,
                "coins_given": float(coins_given)
            })
        
        # Sort by coins given or rating
        results.sort(key=lambda x: x['coins_given'], reverse=True)
        return jsonify(results), 200
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN get_teachers_rating AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"Teachers rating error: {str(e)}"}), 500

@director_bp.route('/policy', methods=['GET'])
@jwt_required()
def get_policy():
    claims = get_jwt()
    if claims.get('role') != 'director': return jsonify({"msg": "Forbidden"}), 403
    
    try:
        return jsonify({
            "daily_limit": SystemSetting.get_val("daily_coin_limit", "50"),
            "math_multiplier": SystemSetting.get_val("multiplier_math", "1.2"),
            "english_multiplier": SystemSetting.get_val("multiplier_english", "1.1"),
            "social_multiplier": SystemSetting.get_val("multiplier_social", "1.5")
        }), 200
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN get_policy AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"Policy error: {str(e)}"}), 500

@director_bp.route('/policy', methods=['POST'])
@jwt_required()
def update_policy():
    claims = get_jwt()
    if claims.get('role') != 'director': return jsonify({"msg": "Forbidden"}), 403
    
    data = request.get_json()
    if 'daily_limit' in data: SystemSetting.set_val("daily_coin_limit", data['daily_limit'], "Maximum coins per day")
    if 'math_multiplier' in data: SystemSetting.set_val("multiplier_math", data['math_multiplier'], "Math/STEM multiplier")
    if 'english_multiplier' in data: SystemSetting.set_val("multiplier_english", data['english_multiplier'], "English multiplier")
    if 'social_multiplier' in data: SystemSetting.set_val("multiplier_social", data['social_multiplier'], "Social activity multiplier")
    
    return jsonify({"msg": "Siyosat muvaffaqiyatli yangilandi"}), 200

@director_bp.route('/approval-requests', methods=['GET'])
@jwt_required()
def get_approval_requests():
    claims = get_jwt()
    if claims.get('role') != 'director': return jsonify({"msg": "Forbidden"}), 403
    try:
        reqs = ApprovalRequest.query.filter_by(status='pending').all()
        return jsonify([{
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "admin": User.query.get(r.admin_id).full_name if (r.admin_id and User.query.get(r.admin_id)) else "Admin",
            "timestamp": r.created_at.isoformat()
        } for r in reqs]), 200
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN get_approval_requests AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"Approval requests error: {str(e)}"}), 500

@director_bp.route('/approval-requests/<int:req_id>/action', methods=['POST'])
@jwt_required()
def action_approval_request(req_id):
    claims = get_jwt()
    if claims.get('role') != 'director': return jsonify({"msg": "Forbidden"}), 403
    data = request.get_json()
    status = data.get('status') # approved, rejected
    
    req = ApprovalRequest.query.get_or_404(req_id)
    req.status = status
    log_event(get_jwt_identity(), f"So'rov {status}: {req.title}")
    db.session.commit()
    return jsonify({"msg": f"So'rov {status} qilindi"}), 200

@director_bp.route('/teachers', methods=['GET'])
@jwt_required()
def get_teachers():
    claims = get_jwt()
    if claims.get('role') != 'director': return jsonify({"msg": "Forbidden"}), 403
    
    try:
        teachers = Teacher.query.all()
        return jsonify([{
            "id": t.id,
            "full_name": t.user.full_name if t.user else "Unknown",
            "subject": t.subject,
            "daily_limit": t.daily_limit
        } for t in teachers]), 200
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('debug_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- ERROR IN get_teachers AT {datetime.utcnow()} ---\n")
            f.write(error_msg)
        return jsonify({"msg": f"Teachers error: {str(e)}"}), 500

@director_bp.route('/teachers/limit', methods=['POST'])
@jwt_required()
def update_teacher_limit():
    claims = get_jwt()
    if claims.get('role') != 'director': return jsonify({"msg": "Forbidden"}), 403
    
    data = request.get_json()
    teacher_id = data.get('teacher_id')
    new_limit = data.get('daily_limit')
    
    teacher = Teacher.query.get(teacher_id)
    if not teacher: return jsonify({"msg": "Ustoz topilmadi"}), 404
    
    teacher.daily_limit = float(new_limit)
    db.session.commit()
    
    log_event(get_jwt_identity(), f"Ustoz {teacher.user.full_name} limiti {new_limit} ga o'zgartirildi")
    return jsonify({"msg": f"{teacher.user.full_name} uchun limit yangilandi"}), 200
