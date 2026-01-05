from models.all_models import db, Student, Badge, StudentBadge, Notification, CoinTransaction, Attendance, HomeworkSubmission
from datetime import datetime

class BadgeService:
    @staticmethod
    def check_all_badges(student_id):
        """Run all badge checks for a student."""
        BadgeService.check_wealth_badges(student_id)
        BadgeService.check_discipline_badges(student_id)
        BadgeService.check_scholar_badges(student_id)

    @staticmethod
    def check_wealth_badges(student_id):
        student = Student.query.get(student_id)
        if not student: return

        # Wealth levels based on total balance or earned coins? Let's use current balance as per seed script.
        # But maybe total earned is better. For now, let's use balance to match seed_badges requirement_text.
        balance = student.balance
        
        # Find badges in Wealth category (Boyvachcha Lvl X)
        # Requirement: balance >= i * 20
        lvl = int(balance // 20)
        if lvl > 0:
            for i in range(1, min(lvl + 1, 26)):
                badge_name = f"Boyvachcha Lvl {i}"
                BadgeService.award_badge_by_name(student_id, badge_name)

    @staticmethod
    def check_discipline_badges(student_id):
        # Count 'present' attendance
        present_count = Attendance.query.filter_by(student_id=student_id, status='present').count()
        
        # Requirement: count >= i * 5
        lvl = int(present_count // 5)
        if lvl > 0:
            for i in range(1, min(lvl + 1, 26)):
                badge_name = f"Intizom Ustasi Lvl {i}"
                BadgeService.award_badge_by_name(student_id, badge_name)

    @staticmethod
    def check_scholar_badges(student_id):
        # Count completed homeworks
        hw_count = HomeworkSubmission.query.filter_by(student_id=student_id, status='completed').count()
        
        # Requirement: count >= i * 4
        lvl = int(hw_count // 4)
        if lvl > 0:
            for i in range(1, min(lvl + 1, 26)):
                badge_name = f"Bilimdon Lvl {i}"
                BadgeService.award_badge_by_name(student_id, badge_name)

    @staticmethod
    def award_badge_by_name(student_id, badge_name):
        badge = Badge.query.filter_by(name=badge_name).first()
        if not badge: return

        # Check if already earned
        exists = StudentBadge.query.filter_by(student_id=student_id, badge_id=badge.id).first()
        if not exists:
            try:
                new_earned = StudentBadge(student_id=student_id, badge_id=badge.id)
                db.session.add(new_earned)
                
                # Notify student
                student = Student.query.get(student_id)
                notif = Notification(
                    user_id=student.user_id,
                    title="Yangi Nishon! 🎉",
                    message=f"Tabriklaymiz! Siz '{badge.icon} {badge.name}' nishonini qo'lga kiritdingiz!"
                )
                db.session.add(notif)
                db.session.commit()
                print(f"Awarded badge {badge_name} to student {student_id}")
            except Exception as e:
                db.session.rollback()
                # Unique constraint might have caught it in a parallel race
                pass
