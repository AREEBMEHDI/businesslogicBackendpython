from flask import Blueprint, request, jsonify, make_response

from auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token_and_get_user,
    revoke_refresh_token,        # optional but recommended
)
from exceptions import (
    AuthenticationError,
    MissingCredentials,
    InvalidCredentials,
    InactiveUser,
    MissingRefreshToken,
    InvalidRefreshToken,
)

auth_bp = Blueprint("auth", __name__)


# =========================
# LOGIN
# =========================
@auth_bp.route("/api/login", methods=["POST"])
def login_api():
    try:
        username = request.form.get("username")
        password = request.form.get("password")

        user_id = authenticate_user(username, password)

        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        response = make_response(jsonify({
            "message": "Login successful",
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

    except MissingCredentials:
        return jsonify({"message": "Username and password are required"}), 400

    except InactiveUser:
        return jsonify({"message": "User account is inactive"}), 403

    except (InvalidCredentials, AuthenticationError):
        # Do NOT leak details
        return jsonify({"message": "Invalid credentials"}), 401
    

@auth_bp.route("/api/refresh", methods=["POST"])
def refresh_api():
    try:
        raw_refresh = request.cookies.get("refresh_token")
        user_id = verify_refresh_token_and_get_user(raw_refresh)

        access_token = create_access_token(user_id)

        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 900
        }), 200

    except MissingRefreshToken:
        return jsonify({"message": "Unauthorized"}), 401

    except InvalidRefreshToken:
        return jsonify({"message": "Unauthorized"}), 401
