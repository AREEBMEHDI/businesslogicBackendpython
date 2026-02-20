import secrets, hmac, hashlib
from datetime import datetime, timedelta
from models import db, Auth, TokenServices, Users, Admins
from flask_bcrypt import Bcrypt
from exceptions import (
    MissingCredentials,
    InvalidCredentials,
    InactiveUser,
    NotAnAdmin,
    MissingRefreshToken,
    InvalidRefreshToken,
    MissingAccessToken,
    InvalidAccessToken,
)

REFRESH_TOKEN_PEPPER="dc0f9e1716860acefd374209f733f725"  ## Later Add in Config


bcrypt = Bcrypt()

def authenticate_user(username: str, password: str) -> str:
    """
    Verifies username & password.
    Returns user_id if valid.
    Raises AuthenticationError subclasses on failure.
    """

    if not username or not password:
        raise MissingCredentials("Username and password are required")

    auth = Auth.query.filter_by(username=username).first()
    if not auth:
        # IMPORTANT: do NOT reveal which part failed
        raise InvalidCredentials("Invalid credentials")

    if not bcrypt.check_password_hash(auth.password_hash, password):
        raise InvalidCredentials("Invalid credentials")

    if not auth.user.is_active:
        raise InactiveUser("User account is inactive")

    return auth.user_id

def authenticate_admin(username: str, password: str) -> str:
    """
    Verifies username & password, then checks admin role.
    Returns user_id if valid admin.
    Raises AuthenticationError subclasses on failure.
    """
    user_id = authenticate_user(username, password)

    if not is_admin_user(user_id):
        raise NotAnAdmin("User is not an admin")

    return user_id

def create_access_token(user_id, minutes=15):
    raw_token = secrets.token_hex(32)

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    token = TokenServices(
        user_id=user_id,
        token_hash=token_hash,
        token_type="access",
        expires_at=datetime.utcnow() + timedelta(minutes=minutes),
        revoked=False
    )

    db.session.add(token)
    db.session.commit()

    return raw_token

def _hash_refresh_token(raw_token: str) -> str:
    # HMAC prevents offline guessing if DB leaks
    secret = REFRESH_TOKEN_PEPPER.encode()
    return hmac.new(secret, raw_token.encode(), hashlib.sha256).hexdigest()

def create_refresh_token(user_id, days=3):
    raw_token = secrets.token_urlsafe(48)  # strong + URL-safe

    token_hash = _hash_refresh_token(raw_token)

    token = TokenServices(
        user_id=user_id,
        token_hash=token_hash,
        token_type="refresh",
        expires_at=datetime.utcnow() + timedelta(days=days),
        revoked=False
    )

    db.session.add(token)
    db.session.commit()

    return raw_token

def revoke_refresh_token(raw_refresh_token: str):
    token_hash = _hash_refresh_token(raw_refresh_token)

    token = TokenServices.query.filter_by(
        token_hash=token_hash,
        token_type="refresh",
        revoked=False
    ).first()

    if token:
        token.revoked = True
        db.session.commit()

def is_admin_user(user_id: str) -> bool:
    """
    Returns True if the user exists and has admin role.
    """
    if not user_id:
        return False

    return db.session.query(
        Users.user_id
    ).filter_by(
        user_id=user_id,
        role="admin",
        is_active=True
    ).first() is not None



def verify_access_token(auth_header: str) -> str:
    """
    Verifies opaque access token from Authorization header.
    """

    # 1️⃣ Header sanity check
    if not auth_header or not auth_header.startswith("Bearer "):
        raise MissingAccessToken("Missing access token")

    raw_token = auth_header.split(" ", 1)[1].strip()
    if not raw_token:
        raise MissingAccessToken("Missing access token")

    # 2️⃣ Hash token
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    # 3️⃣ Lookup in DB
    token = TokenServices.query.filter_by(
        token_hash=token_hash,
        token_type="access",
        revoked=False
    ).first()

    if not token:
        raise InvalidAccessToken("Invalid access token")

    # 4️⃣ Expiry check
    if token.expires_at < datetime.utcnow():
        raise InvalidAccessToken("Invalid access token")

    return token.user_id

def verify_refresh_token_and_get_user(raw_refresh_token: str):
    if not raw_refresh_token:
        raise MissingRefreshToken("refresh_token is missing")

    token_hash = _hash_refresh_token(raw_refresh_token)

    token = TokenServices.query.filter_by(
        token_hash=token_hash,
        token_type="refresh",
        revoked=False
    ).first()

    if not token or token.expires_at < datetime.utcnow():
        raise InvalidRefreshToken("The refresh_token provided is invalid")

    return token.user_id

