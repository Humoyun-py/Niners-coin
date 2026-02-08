from models.all_models import db, Student, CoinTransaction
from services.security_service import send_notification
from services.badge_engine import check_and_award_badges

def award_coins(student_id, amount, source, description=None, teacher_id=None):
    """
    Business logic for awarding coins to a student.
    Ensures balance is updated and transaction is logged.
    """
    student = Student.query.get(student_id)
    if not student:
        return False, "Student not found"
    
    if student.user and not student.user.is_active and amount > 0:
        block_reason = student.user.block_reason or "Sabab ko'rsatilmagan"
        return False, f"Coin berib bo'lmaydi: O'quvchi bloklangan ({block_reason})"
        
    try:
        # Update balance
        student.coin_balance += amount
        
        # Only increase total_earned for positive amounts
        if amount > 0:
            student.total_earned += amount
        
        # Log transaction
        transaction = CoinTransaction(
            student_id=student_id,
            amount=amount,
            type='earn',
            source=source,
            teacher_id=teacher_id
        )
        db.session.add(transaction)
        
        # Notify student
        msg_title = "Yangi Coinlar!" if amount >= 0 else "Coinlar Olib Tashlandi"
        msg_body = f"Sizga {amount} coin berildi. Sabab: {source}" if amount >= 0 else f"Sizdan {abs(amount)} coin olib tashlandi. Sabab: {source}"
        
        send_notification(student.user_id, msg_title, msg_body)
        
        # Check for rank up (Simple logic)
        if student.total_earned > 1000:
            student.rank = "Legend"
        elif student.total_earned > 500:
            student.rank = "Expert"
        elif student.total_earned > 100:
            student.rank = "Pro"
            
        # Check for new badges
        new_badges = check_and_award_badges(student_id)
        for b_name in new_badges:
            send_notification(student.user_id, "Yangi Nishon! 🏆", f"Tabriklaymiz! Siz '{b_name}' nishonini qo'lga kiritdingiz.")
            
        db.session.commit()
        return True, f"Successfully awarded {amount} coins"
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def spend_coins(student_id, amount, reason):
    student = Student.query.get(student_id)
    if not student or student.coin_balance < amount:
        return False, "Coinlar yetarli emas"
        
    try:
        student.coin_balance -= amount
        transaction = CoinTransaction(
            student_id=student_id,
            amount=-amount,
            type='spend',
            source=reason
        )
        db.session.add(transaction)
        db.session.commit()
        return True, f"Successfully spent {amount} coins"
    except Exception as e:
        db.session.rollback()
        return False, str(e)
