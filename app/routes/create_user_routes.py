from flask import Blueprint, request, jsonify, make_response
from client import create_client_with_profile
from auth import verify_access_token, create_access_token, create_refresh_token
# from client import update_user_profile_photo
from exceptions import (
    ClientCreationError,
    UsernameAlreadyExists,
    InvalidClientData,
    InvalidUserInfoData,
    MissingAccessToken, 
    InvalidAccessToken,
    UserProfilePhotoUpdateError,
    InvalidProfileImage

)


createuser_bp = Blueprint("create_user", __name__)


@createuser_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    required_fields = ("display_name", "username", "password", "gender")
    missing = [f for f in required_fields if not data.get(f)]

    if missing:
        return jsonify({
            "message": "Missing required fields",
            "missing_fields": missing
        }), 400

    try:
        user_id = create_client_with_profile(
            name=data["name"],          # 👈 derived
            username=data["username"],
            password=data["password"],
            email=data["email"],  # 👈 same source
            department=data["department"],
            designation=data["designation"],
            phone=data["phone"],
            employee_id=data.get("employee_id"),
            gender=data.get("gender"),
        )

        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        response = make_response(jsonify({
            "success": True,
            "user_id": user_id,
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 900
        }), 200)

        response.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            secure=False,          # TRUE in production (HTTPS)
            samesite="Strict",
            max_age=3 * 24 * 60 * 60
        )

        return response

    except UsernameAlreadyExists:
        return jsonify({"message": "Username already exists"}), 409

    except InvalidClientData:
        return jsonify({"message": "Invalid data or missing fields"}), 400
    
    except InvalidUserInfoData as e:
        return jsonify({"message": str(e)}), 400

    except ClientCreationError:
        return jsonify({"message": "Failed to create user"}), 500

    except Exception:
        return jsonify({"message": "Internal server error"}), 500
    

@createuser_bp.route("/api/me/profile-photo", methods=["POST"])
def upload_profile_photo():
    # ------------------------
    # Auth
    # ------------------------
    try:
        auth_header = request.headers.get("Authorization")
        user_id = verify_access_token(auth_header)

    except (MissingAccessToken, InvalidAccessToken):
        return jsonify({"message": "Unauthorized"}), 401

    # ------------------------
    # Input validation
    # ------------------------
    if "file" not in request.files:
        return jsonify({"message": "Missing file"}), 400

    file = request.files["file"]

    # ------------------------
    # Core logic
    # ------------------------
    try:
        update_user_profile_photo(
            user_id=user_id,
            file=file,
        )

        return jsonify({
            "success": True,
            "message": "Profile photo updated"
        }), 200

    # ------------------------
    # Expected / domain errors
    # ------------------------
    except InvalidProfileImage:
        return jsonify({"message": "The file uploaded is not a valid image"}), 400

    except UserProfilePhotoUpdateError:
        return jsonify({"message": "Failed to update profile photo"}), 500

    # ------------------------
    # Safety net
    # ------------------------
    except Exception:
        return jsonify({"message": "Internal server error"}), 500