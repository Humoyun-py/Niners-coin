from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Models defined in a single file for simplicity in initialization, 
# but can be split if project grows significantly.

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False) 
    full_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    block_reason = db.Column(db.String(255), nullable=True)
    debt_amount = db.Column(db.Float, default=0.0)
    profile_image = db.Column(db.Text, nullable=True)  # Base64 image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "block_reason": self.block_reason,
            "debt_amount": self.debt_amount,
            "profile_image": self.profile_image,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    coin_balance = db.Column(db.Float, default=0.0)
    total_earned = db.Column(db.Float, default=0.0)
    rank = db.Column(db.String(50), default="Newbie")
    xp = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    last_homework_date = db.Column(db.Date, nullable=True)
    last_streak_date = db.Column(db.Date, nullable=True)
    payment_status = db.Column(db.String(20), default="paid") # paid, pending, overdue
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.user.username if self.user else "N/A",
            "full_name": self.user.full_name if self.user else "N/A",
            "coin_balance": self.coin_balance,
            "total_earned": self.total_earned,
            "rank": self.rank,
            "xp": self.xp,
            "streak": self.streak,
            "payment_status": self.payment_status
        }

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=True)
    rating = db.Column(db.Float, default=5.0)
    daily_limit = db.Column(db.Float, default=500.0) # Default limit per teacher
    user = db.relationship('User', backref=db.backref('teacher_profile', uselist=False))

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.user.full_name if self.user else "N/A",
            "subject": self.subject or "N/A",
            "rating": self.rating,
            "daily_limit": self.daily_limit
        }

class Parent(db.Model):
    __tablename__ = 'parents'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('parent_profile', uselist=False))

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    students = db.relationship('Student', backref='student_class', lazy=True)
    schedule_days = db.Column(db.String(50), nullable=True) # "Dushanba|Chorshanba|Juma" or "Seshanba|Payshanba|Shanba"
    schedule_time = db.Column(db.String(10), nullable=True) # "14:00"

    def to_dict(self):
        teacher_name = "N/A"
        if self.teacher_id:
            teacher = Teacher.query.get(self.teacher_id)
            if teacher and teacher.user:
                teacher_name = teacher.user.full_name
        
        return {
            "id": self.id,
            "name": self.name,
            "teacher_name": teacher_name,
            "student_count": len(self.students) if self.students else 0,
            "schedule_days": self.schedule_days,
            "schedule_time": self.schedule_time
        }

class CoinTransaction(db.Model):
    __tablename__ = 'coin_transactions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True) # Who issued it
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False) 
    source = db.Column(db.String(100), nullable=False) 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', backref=db.backref('coin_transactions', lazy=True))
    teacher = db.relationship('Teacher', backref=db.backref('issued_transactions', lazy=True))

class Badge(db.Model):
    __tablename__ = 'badges'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    requirement_text = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(255), nullable=True)

class StudentBadge(db.Model):
    __tablename__ = 'student_badges'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'badge_id', name='_student_badge_uc'),)

    student = db.relationship('Student', backref=db.backref('badges', lazy=True))
    badge = db.relationship('Badge')

class Homework(db.Model):
    __tablename__ = 'homeworks'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    xp_reward = db.Column(db.Integer, default=50)
    deadline = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    target_class = db.relationship('Class', backref=db.backref('homeworks', lazy=True))
    author = db.relationship('Teacher', backref=db.backref('homeworks', lazy=True))

    def to_dict(self):
        class_name = "Unknown"
        if self.target_class:
            class_name = self.target_class.name
            
        return {
            "id": self.id,
            "class_name": class_name,
            "description": self.description,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "created_at": self.created_at.isoformat()
        }

class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    coin_reward = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    teacher = db.relationship('Teacher', backref=db.backref('tests', lazy=True))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(100))
    message = db.Column(db.String(500))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    severity = db.Column(db.String(20), default='info') # info, warning, danger
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class ApprovalRequest(db.Model):
    __tablename__ = 'approval_requests'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.relationship('User', foreign_keys=[admin_id])

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.String(20), default='open') # open, resolved, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='complaints')

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    status = db.Column(db.String(20), nullable=False) # present, absent, late, excused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='attendance_records')
    class_obj = db.relationship('Class', backref='attendance_logs')

class ShopItem(db.Model):
    __tablename__ = 'shop_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.Text, nullable=True) # URL or Base64 string
    stock = db.Column(db.Integer, default=-1) # -1 means infinite
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_items.id'), nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='completed') # completed, refunded
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='purchases')
    item = db.relationship('ShopItem')

class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=True) # HTML or text content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    class_obj = db.relationship('Class', backref='topics')

class TestResult(db.Model):
    __tablename__ = 'test_results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='test_history')
    test = db.relationship('Test')



class HomeworkSubmission(db.Model):
    __tablename__ = 'homework_submissions'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    homework_id = db.Column(db.Integer, db.ForeignKey('homeworks.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.Text, nullable=True)  # Base64 or URL
    admin_comment = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pending') # pending, submitted, approved, rejected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='homework_submissions')
    homework = db.relationship('Homework', backref='submissions')

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_val(key, default=None):
        s = SystemSetting.query.filter_by(key=key).first()
        return s.value if s else default
    
    @staticmethod
    def set_val(key, value, description=None):
        s = SystemSetting.query.filter_by(key=key).first()
        if s:
            s.value = str(value)
            if description: s.description = description
        else:
            s = SystemSetting(key=key, value=str(value), description=description)
            db.session.add(s)
        db.session.commit()
