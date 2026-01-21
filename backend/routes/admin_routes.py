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
        original_filename = secure_filename(file.filename)
        # Ensure extension exists
        import os
        name, ext = os.path.splitext(original_filename)
        if not ext:
            ext = ".png" # Default fallback
            
        import time
        filename = f"{int(time.time())}_{name}{ext}"
        
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

# ... (omitted text) ...

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
    
    # SAFER IMAGE UPDATE: Only update if explicitly provided and not empty/null
    # If frontend sends empty string, it might mean "remove image" or "bad state"
    # But usually sending nothing means "keep old".
    # Here we check if 'image_url' acts as a replacement.
    new_image = data.get('image_url')
    if new_image is not None:
        item.image_url = new_image
        
    db.session.commit()
    return jsonify({"msg": "Item updated"}), 200

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


