from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.all_models import db, User, Teacher, Student, ApprovalRequest, AuditLog
from services.security_service import log_event

director_bp = Blueprint('director', __name__)

@director_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    # Placeholder for director analytics
    return jsonify({
        "top_teachers": [
            {"id": 1, "name": "Murod Ahmedov", "rating": 4.9},
            {"id": 2, "name": "Elena Pak", "rating": 4.8}
        ]
    }), 200

@director_bp.route('/approval-requests', methods=['GET'])
@jwt_required()
def get_approval_requests():
    claims = get_jwt()
    if claims.get('role') != 'director': return jsonify({"msg": "Forbidden"}), 403
    reqs = ApprovalRequest.query.filter_by(status='pending').all()
    return jsonify([{
        "id": r.id,
        "title": r.title,
        "description": r.description,
        "admin": User.query.get(r.admin_id).full_name if r.admin_id else "Admin",
        "timestamp": r.created_at.isoformat()
    } for r in reqs]), 200

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
