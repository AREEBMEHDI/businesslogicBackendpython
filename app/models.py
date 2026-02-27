from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta

db = SQLAlchemy()


class Users(db.Model):
    __tablename__ = 'users2'
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    role = db.Column(
        db.String(20),
        CheckConstraint("role IN ('admin', 'client')"),
        nullable=False
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    auth = db.relationship("Auth", backref="user", uselist=False)
    tokens = db.relationship("TokenServices", backref="user", cascade="all, delete-orphan")
    client = db.relationship("Clients", backref="user", uselist=False)
    users_info = db.relationship("UsersInfo", backref="user", uselist=False)
    admin = db.relationship(
        "Admins",
        foreign_keys="Admins.user_id",
        backref="admin_user",
        uselist=False
    )

    # Admin who granted permissions
    granted_admins = db.relationship(
        "Admins",
        foreign_keys="Admins.granted_by",
        backref="granted_by_user"
    )


class Auth(db.Model):
    __tablename__ = 'auth'
    user_id = db.Column(db.String(36), db.ForeignKey('users2.user_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)




class TokenServices(db.Model):
    __tablename__ = 'token_services'
    token_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users2.user_id', ondelete='CASCADE'), index=True, nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    token_type = db.Column(
        db.String(20),
        CheckConstraint("token_type IN ('access','refresh')", name="chk_token_type"),
        nullable=False
    )
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

class Admins(db.Model):
    __tablename__ = 'admins'
    user_id = db.Column(db.String(36), db.ForeignKey('users2.user_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    permission_level = db.Column(db.Integer, nullable=False, default=1)
    granted_by = db.Column(db.String(36), db.ForeignKey('users2.user_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            'permission_level BETWEEN 1 AND 3',
            name='chk_admin_permission_level'
        ),
        )
    
class Clients(db.Model):
    __tablename__ = 'clients'
    user_id = db.Column(db.String(36), db.ForeignKey('users2.user_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)


class UsersInfo(db.Model):
    __tablename__ = 'users_info'

    user_id = db.Column(db.String(36), db.ForeignKey('users2.user_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    profile_photo_key = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    department = db.Column(
        db.String(50),
        CheckConstraint(
            "department IN ('software_development','qa','devops','hr','finance','sales')",
            name="chk_department"
        ),
        nullable=False  
    )
    designation = db.Column(
        db.String(50),
        CheckConstraint(
            "designation IN ('junior_developer','developer','senior_developer','tech_lead','engineering_manager')",
            name="chk_designation"
        ),
        nullable=False
    )
    phone = db.Column(db.String(15), nullable=False, unique=True)
    employee_id = db.Column(db.String(20), nullable=False, unique=True)
    gender = db.Column(
        db.String(10),
        CheckConstraint(
            "gender IN ('male','female')",
            name="chk_gender"
        ),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    updated_at = db.Column( db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)


class LeaveRequests(db.Model):
    __tablename__ = 'leave_requests'

    leave_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users2.user_id', ondelete='CASCADE'), index=True, nullable=False)
    leave_type = db.Column(
        db.String(30),
        CheckConstraint(
            "leave_type IN ('casual_leave','sick_leave','annual_leave','emergency_leave')",
            name="chk_leave_type"
        ),
        nullable=False
    )
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.String(20),
        CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name="chk_leave_status"
        ),
        nullable=False,
        default='pending'
    )
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)

    user = db.relationship("Users", backref=db.backref("leave_requests", cascade="all, delete-orphan"))


class Attendance(db.Model):
    __tablename__ = 'attendance'

    attendance_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users2.user_id', ondelete='CASCADE'), index=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.String(20),
        CheckConstraint(
            "status IN ('present','absent','half_day','late')",
            name="chk_attendance_status"
        ),
        nullable=False,
        default='present'
    )
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)

    user = db.relationship("Users", backref=db.backref("attendance_records", cascade="all, delete-orphan"))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='uq_attendance_user_date'),
    )
