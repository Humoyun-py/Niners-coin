from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.all_models import db, User, Student, Teacher, Parent
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    # Public registration disabled as per user request.
    # Users are now created by Admin.
    return jsonify({"msg": "Ochiq ro'yxatdan o'tish to'xtatilgan. Iltimos, administratorga murojaat qiling."}), 403

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.check_password(data.get('password')):
        if not user.is_active:
            debt = int(user.debt_amount) if user.debt_amount else 0
            msg = f"To'lov qilingmagan shuning uchun akkaunt block qilindi | Qarz: {debt:,} so'm"
            return jsonify({"msg": msg}), 403
            
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role},
            expires_delta=timedelta(days=1)
        )
        return jsonify(access_token=access_token, role=user.role, full_name=user.full_name), 200
    
    return jsonify({"msg": "Username yoki parol xato"}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify(user.to_dict()), 200

@auth_bp.route('/profile', methods=['PATCH'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user: return jsonify({"msg": "User not found"}), 404
    
    data = request.get_json()
    if 'full_name' in data: user.full_name = data['full_name']
    if 'email' in data: user.email = data['email']
    
    db.session.commit()
    return jsonify({"msg": "Profil yangilandi", "user": user.to_dict()}), 200
