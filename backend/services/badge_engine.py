from models.all_models import db, Student, Badge, StudentBadge, Notification, Attendance, HomeworkSubmission
from datetime import datetime

def check_and_award_badges(student_id):
    """
    Checks if a student qualifies for new badges based on their activity.
    Returns a list of names of newly awarded badges.
    """
    student = Student.query.get(student_id)
    if not student: return []

    new_badges_names = []

    # 1. Wealth Badges (Boyvachcha Lvl 1-25)
    balance = student.coin_balance
    lvl_wealth = int(balance // 20)
    for i in range(1, min(lvl_wealth + 1, 26)):
        if award_badge_if_needed(student_id, f"Boyvachcha Lvl {i}"):
            new_badges_names.append(f"Boyvachcha Lvl {i}")

    # 2. Discipline Badges (Intizom Ustasi Lvl 1-25)
    present_count = Attendance.query.filter_by(student_id=student_id, status='present').count()
    lvl_disc = int(present_count // 5)
    for i in range(1, min(lvl_disc + 1, 26)):
        if award_badge_if_needed(student_id, f"Intizom Ustasi Lvl {i}"):
            new_badges_names.append(f"Intizom Ustasi Lvl {i}")

    # 3. Scholar Badges (Bilimdon Lvl 1-25)
    # Using HomeworkSubmission if available, or fallback to earned coins from tests
    hw_count = HomeworkSubmission.query.filter_by(student_id=student_id, status='checked').count()
    lvl_scholar = int(hw_count // 4)
    for i in range(1, min(lvl_scholar + 1, 26)):
        if award_badge_if_needed(student_id, f"Bilimdon Lvl {i}"):
            new_badges_names.append(f"Bilimdon Lvl {i}")

    db.session.commit()
    return new_badges_names

def award_badge_if_needed(student_id, badge_name):
    badge = Badge.query.filter_by(name=badge_name).first()
    if not badge: return False

    # Check if already earned
    exists = StudentBadge.query.filter_by(student_id=student_id, badge_id=badge.id).first()
    if not exists:
        sb = StudentBadge(student_id=student_id, badge_id=badge.id)
        db.session.add(sb)
        
        # Add notification record as well
        student = Student.query.get(student_id)
        notif = Notification(
            user_id=student.user_id,
            title="Yangi Nishon! 🎉",
            message=f"Tabriklaymiz! Siz '{badge.icon} {badge.name}' nishonini qo'lga kiritdingiz!"
        )
        db.session.add(notif)
        return True
    return False
