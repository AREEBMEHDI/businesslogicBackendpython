import uuid
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from flask_bcrypt import Bcrypt
# from helper_func import detect_image_extension
from models import db, Users, Clients, Auth, UsersInfo
# from validations import is_valid_profile_image, is_allowed_social_platform, is_valid_social_handle
# from spaces import get_spaces, generate_signed_get_url, DO_SPACES_BUCKET
import imghdr
from exceptions import (
    ClientCreationError,
    UsernameAlreadyExists,
    InvalidClientData,
    UserInfoCreationError,
    InvalidUserInfoData,
    InvalidProfileImage,
    ProfilePhotoUploadError,
    ProfilePhotoDeleteError,
    UserProfileNotFound,
    UserProfilePhotoUpdateError,
    UserProfilePhotoNotFound,
    InvalidSocialPlatform,
    InvalidSocialHandle,
    SocialUpsertError
)

bcrypt = Bcrypt()


def create_client(
    *,
    name: str,
    username: str,
    password: str,
    ) -> str:
    """
    Creates a client user.
    Returns user_id.
    Raises ClientCreationError subclasses on failure.
    """

    # ------------------------
    # Basic validation
    # ------------------------
    if not name or not username or not password:
        raise InvalidClientData("Missing required fields")

    if Auth.query.filter_by(username=username).first():
        raise UsernameAlreadyExists("Username already exists")

    user_id = str(uuid.uuid4())

    try:
        # ------------------------
        # USERS TABLE
        # ------------------------
        user = Users(
            user_id=user_id,
            role="client",
            name=name,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.session.add(user)

        # ------------------------
        # CLIENTS TABLE
        # ------------------------
        client = Clients(
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        db.session.add(client)

        # ------------------------
        # AUTH TABLE
        # ------------------------
        password_hash = bcrypt.generate_password_hash(password).decode()

        auth = Auth(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            created_at=datetime.utcnow()
        )
        db.session.add(auth)

        return user_id

    except (UsernameAlreadyExists, InvalidClientData):
        raise
    except Exception as e:
        raise ClientCreationError("Failed to create client") from e


def create_users_info(
    *,
    email: str,
    user_id: str,
    name: str,
    department: str,
    designation: str,
    phone: str,
    employee_id: str,
    gender: str | None = None,
) -> None:
    """
    Creates users_info entry for a user.
    Must be called inside an active transaction.
    """

    # ------------------------
    # Validation
    # ------------------------
    if not user_id or not email or not gender:
        raise InvalidUserInfoData("Missing required fields")

    if gender not in ("male", "female"):
        raise InvalidUserInfoData("Invalid gender")

    try:
        info = UsersInfo(
            user_id=user_id,
            profile_photo_key=None,
            name=name,
            email=email,
            department=department,
            designation=designation,
            phone=phone,
            employee_id=employee_id,
            gender=gender,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(info)

    except Exception as e:
        raise UserInfoCreationError("Failed to create user info") from e


def create_client_with_profile(
    *,
    username: str,
    password: str,
    email: str,
    name: str,
    department: str,
    designation: str,
    phone: str,
    employee_id: str,
    gender: str | None = None,
) -> str:
    """
    Atomic creation of:
    - users
    - clients
    - auth
    - users_info
    """

    try:
        user_id = create_client(
            name=name,
            username=username,
            password=password,
        )

        create_users_info(
            email=email,
            user_id=user_id,
            name=name,
            department=department,
            designation=designation,
            phone=phone,
            employee_id=employee_id,
            gender=gender,
        )

        db.session.commit()
        return user_id

    except (UsernameAlreadyExists, InvalidClientData, InvalidUserInfoData):
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise ClientCreationError("Failed to create client with profile") from e
    

# def upload_profile_photo_to_spaces(
#     *,
#     file,
#     user_id: str,
# ) -> str:
#     """
#     Uploads profile photo to DigitalOcean Spaces.
#     Returns object key.
#     """

#     if not is_valid_profile_image(file):
#         raise InvalidProfileImage("Invalid profile image")

#     # Safe to read now (stream was rewound)
#     data = file.read()

#     # Extension detection (not validation)
#     try:
#         ext = detect_image_extension(data)
#     except ValueError:
#         raise InvalidProfileImage("Invalid profile image")


#     key = f"pfp/{user_id}/{uuid.uuid4()}.{ext}"

#     try:
#         s3 = get_spaces()
#         s3.put_object(
#             Bucket=DO_SPACES_BUCKET,
#             Key=key,
#             Body=data,
#             ContentType=file.mimetype,
#             ACL="private",
#             )
#     except Exception as e:
#         raise ProfilePhotoUploadError("Failed to upload profile photo") from e

#     return key

# def delete_profile_photo_from_spaces(
#     *,
#     profile_photo_key: str,
# ) -> None:
#     """
#     Deletes profile photo from Spaces (best-effort).
#     """

#     if not profile_photo_key:
#         return

#     try:
#         s3 = get_spaces()
#         s3.delete_object(
#             Bucket=DO_SPACES_BUCKET,
#             Key=profile_photo_key,
#         )
#     except Exception as e:
#         raise ProfilePhotoDeleteError("Failed to delete profile photo") from e

# def set_user_profile_photo_key(
#     *,
#     user_id: str,
#     profile_photo_key: str,
# ) -> str | None:
#     """
#     Stores new profile_photo_key.
#     Returns old key (if any).
#     """

#     info = UsersInfo.query.filter_by(user_id=user_id).first()
#     if not info:
#         raise UserProfileNotFound("User profile not found")

#     old_key = info.profile_photo_key

#     info.profile_photo_key = profile_photo_key
#     info.updated_at = datetime.utcnow()

#     db.session.add(info)
#     return old_key

# def update_user_profile_photo(
#     *,
#     user_id: str,
#     file,
# ) -> str:
#     """
#     Atomic profile photo update:
#     - upload new photo
#     - update DB
#     - delete old photo safely
#     """

#     # 1️⃣ Upload first
#     new_key = upload_profile_photo_to_spaces(
#             file=file,
#             user_id=user_id,
#         )


#     try:
#         # 2️⃣ Update DB
#         old_key = set_user_profile_photo_key(
#             user_id=user_id,
#             profile_photo_key=new_key,
#         )
#         db.session.commit()

#     except Exception as e:
#         db.session.rollback()

#         # Cleanup newly uploaded file
#         try:
#             delete_profile_photo_from_spaces(
#                 profile_photo_key=new_key
#             )
#         except Exception:
#             pass

#         raise UserProfilePhotoUpdateError("Failed to update profile photo") from e

#     # 3️⃣ Delete old photo AFTER commit (best effort)
#     if old_key:
#         try:
#             delete_profile_photo_from_spaces(
#                 profile_photo_key=old_key
#             )
#         except ProfilePhotoDeleteError:
#             pass

#     return new_key


# def get_profile_photo_url_for_user(
#     *,
#     user_id: str,
# ) -> str:
#     """
#     Returns a signed URL for a user's profile photo.
#     Raises UserProfileNotFound if photo not set.
#     """

#     info = UsersInfo.query.filter_by(user_id=user_id).first()
#     if not info or not info.profile_photo_key:
#         raise UserProfilePhotoNotFound("Profile photo not found")

#     return generate_signed_get_url(info.profile_photo_key)


# def upsert_user_social(
#     *,
#     user_id: str,
#     platform: str,
#     handle: str,
# ) -> None:
#     """
#     Create or update a user's social handle for a platform.
#     One social per platform per user.
#     """

#     # ------------------------
#     # Validation
#     # ------------------------
#     if not is_allowed_social_platform(platform):
#         raise InvalidSocialPlatform("Invalid social platform")

#     if not is_valid_social_handle(handle):
#         raise InvalidSocialHandle("Invalid social handle")

#     try:
#         social = UserSocial.query.filter_by(
#             user_id=user_id,
#             platform=platform,
#         ).first()

#         if social:
#             # Update
#             social.handle = handle
#         else:
#             # Create
#             social = UserSocial(
#                 user_id=user_id,
#                 platform=platform,
#                 handle=handle,
#             )
#             db.session.add(social)

#         db.session.commit()

#     except IntegrityError as e:
#         db.session.rollback()
#         raise SocialUpsertError("Failed to save social") from e

#     except Exception as e:
#         db.session.rollback()
#         raise SocialUpsertError("Failed to save social") from e