from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.all_models import User, Student, Teacher, Class

video_bp = Blueprint('video_bp', __name__)

@video_bp.route('/join', methods=['GET'])
@jwt_required()
def join_video():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.role == 'student':
        student = user.student_profile
        if not student or not student.class_id:
            return jsonify({"error": "No class assigned"}), 400
        
        assigned_class = Class.query.get(student.class_id)
        if not assigned_class:
             return jsonify({"error": "Class not found"}), 404
             
        # Room Name Format: niners_class_{id}
        # Secure, simple, unique per class
        room_name = f"niners_class_{assigned_class.id}"
        
        return jsonify({
            "room_name": room_name,
            "display_name": user.full_name,
            "role": "student"
        })
        
    elif user.role == 'teacher':
        # Teachers should pick a room from list, but if they hit this, redirect or error
        return jsonify({"error": "Teachers should use /rooms endpoint"}), 400
        
    return jsonify({"error": "Role not supported"}), 403

@video_bp.route('/rooms', methods=['GET'])
@jwt_required()
def get_teacher_rooms():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.role != 'teacher':
        return jsonify({"error": "Unauthorized"}), 403
        
    teacher = user.teacher_profile
    if not teacher:
         return jsonify({"error": "Teacher profile not found"}), 404
         
    classes = Class.query.filter_by(teacher_id=teacher.id).all()
    
    rooms = []
    for c in classes:
        rooms.append({
            "class_id": c.id,
            "class_name": c.name,
            "room_name": f"niners_class_{c.id}",
            "schedule": f"{c.schedule_days} {c.schedule_time}"
        })
        
    return jsonify({
        "teacher_name": user.full_name,
        "rooms": rooms
    })
