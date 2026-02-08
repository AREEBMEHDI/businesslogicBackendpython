from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta

db = SQLAlchemy()


class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    role = db.Column(db.Enum('admin', 'client'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    auth = db.relationship("Auth", backref="user", uselist=False)
    tokens = db.relationship("TokenServices", backref="user", cascade="all, delete-orphan")
    admin = db.relationship("Admins", backref="user", uselist=False)
    client = db.relationship("Clients", backref="user", uselist=False)
    users_info = db.relationship("UsersInfo", backref="user", uselist=False)
    users_socials = db.relationship("UserSocial", backref="user", lazy="dynamic", cascade="all, delete-orphan")
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
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)




class TokenServices(db.Model):
    __tablename__ = 'token_services'
    token_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), index=True, nullable=False)
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    token_type = db.Column(db.Enum('access', 'refresh'), nullable=False)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

class Admins(db.Model):
    __tablename__ = 'admins'
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    permission_level = db.Column(db.Integer, nullable=False, default=1)
    granted_by = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            'permission_level BETWEEN 1 AND 3',
            name='chk_admin_permission_level'
        ),
        )
    
class Clients(db.Model):
    __tablename__ = 'clients'
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)


class UsersInfo(db.Model):
    __tablename__ = 'users_info'

    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True, nullable=False)
    profile_photo_key = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    department = db.Column(db.Enum('software_development','qa','devops','hr','finance','sales', name='department_enum'), nullable=False)
    designation = db.Column(db.Enum('junior_developer','developer','senior_developer','tech_lead','engineering_manager', name='designation_enum'), nullable=False)
    phone = db.Column(db.String(15), nullable=False, unique=True)
    employee_id = db.Column(db.String(20), nullable=False, unique=True)
    gender = db.Column(db.Enum('male', 'female', name='gender_enum'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    updated_at = db.Column( db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)
