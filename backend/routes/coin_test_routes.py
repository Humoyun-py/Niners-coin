from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.all_models import db, Test, CoinTransaction, Student
from services.test_engine import submit_test_result

coin_test_bp = Blueprint('coin_test', __name__)

@coin_test_bp.route('/tests', methods=['GET'])
@jwt_required()
def get_all_tests():
    tests = Test.query.all()
    return jsonify([{
        "id": t.id,
        "title": t.title,
        "reward": t.coin_reward,
        "teacher": t.teacher.user.full_name
    } for t in tests]), 200

@coin_test_bp.route('/tests/<int:test_id>/submit', methods=['POST'])
@jwt_required()
def submit_test(test_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    claims = get_jwt()
    # current_user = get_jwt_identity()
    # user_id = current_user['id']
    student = Student.query.filter_by(user_id=user_id).first()
    
    if not student:
        return jsonify({"msg": "Only students can submit tests"}), 403
        
    score = data.get('score', 0)
    success, msg = submit_test_result(student.id, test_id, score)
    
    if success:
        return jsonify({"msg": msg}), 200
    return jsonify({"msg": msg}), 400

@coin_test_bp.route('/my-coins', methods=['GET'])
@jwt_required()
def get_my_coins():
    user_id = get_jwt_identity()
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"msg": "No student profile"}), 404
        
    transactions = CoinTransaction.query.filter_by(student_id=student.id).order_by(CoinTransaction.timestamp.desc()).all()
    return jsonify({
        "balance": student.coin_balance,
        "transactions": [{
            "amount": t.amount,
            "source": t.source,
            "date": t.timestamp.isoformat()
        } for t in transactions]
    }), 200
