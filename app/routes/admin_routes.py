from flask import Blueprint, request, jsonify, make_response

from auth import (
    authenticate_admin,
    verify_access_token,
    is_admin_user,
    create_access_token,
    create_refresh_token,
)
from client import create_client_with_profile
from leave import get_all_leave_requests, update_leave_status
from exceptions import (
    AuthenticationError,
    MissingCredentials,
    InvalidCredentials,
    InactiveUser,
    NotAnAdmin,
    MissingAccessToken,
    InvalidAccessToken,
    ClientCreationError,
    UsernameAlreadyExists,
    InvalidClientData,
    InvalidUserInfoData,
    LeaveRequestCreationError,
    LeaveRequestNotFound,
    LeaveAlreadyProcessed,
)

admin_bp = Blueprint("admin", __name__)


# =========================
# ADMIN LOGIN
# =========================
@admin_bp.route("/api/admin/login", methods=["POST"])
def admin_login_api():
    try:
        username = request.form.get("username")
        password = request.form.get("password")

        user_id = authenticate_admin(username, password)

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

    except NotAnAdmin:
        return jsonify({"message": "Invalid credentials"}), 401

    except (InvalidCredentials, AuthenticationError):
        # Do NOT leak details
        return jsonify({"message": "Invalid credentials"}), 401


# =========================
# ADMIN CREATE USER
# =========================
@admin_bp.route("/api/admin/create-user", methods=["POST"])
def admin_create_user():
    # ------------------------
    # Auth: verify token + admin check
    # ------------------------
    try:
        auth_header = request.headers.get("Authorization")
        admin_user_id = verify_access_token(auth_header)

        if not is_admin_user(admin_user_id):
            return jsonify({"message": "Forbidden"}), 403

    except (MissingAccessToken, InvalidAccessToken):
        return jsonify({"message": "Unauthorized"}), 401

    # ------------------------
    # Input validation
    # ------------------------
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    required_fields = ("name", "username", "password", "email",
                       "department", "designation", "phone",
                       "employee_id", "gender")
    missing = [f for f in required_fields if not data.get(f)]

    if missing:
        return jsonify({
            "message": "Missing required fields",
            "missing_fields": missing
        }), 400

    # ------------------------
    # Core logic
    # ------------------------
    try:
        user_id = create_client_with_profile(
            name=data["name"],
            username=data["username"],
            password=data["password"],
            email=data["email"],
            department=data["department"],
            designation=data["designation"],
            phone=data["phone"],
            employee_id=data["employee_id"],
            gender=data["gender"],
        )

        return jsonify({
            "success": True,
            "message": "User created successfully",
            "user_id": user_id,
        }), 201

    except UsernameAlreadyExists:
        return jsonify({"message": "Username already exists"}), 409

    except InvalidClientData:
        return jsonify({"message": "Invalid data or missing fields"}), 400

    except InvalidUserInfoData as e:
        return jsonify({"message": str(e)}), 400

    except ClientCreationError as e:
        return jsonify({"message": str(e)}), 500


# =========================
# ADMIN - ALL LEAVE REQUESTS
# =========================
@admin_bp.route("/api/admin/leave-requests", methods=["GET"])
def admin_all_leave_requests():
    # ------------------------
    # Auth: verify token + admin check
    # ------------------------
    try:
        auth_header = request.headers.get("Authorization")
        admin_user_id = verify_access_token(auth_header)

        if not is_admin_user(admin_user_id):
            return jsonify({"message": "Forbidden"}), 403

    except (MissingAccessToken, InvalidAccessToken):
        return jsonify({"message": "Unauthorized"}), 401

    # ------------------------
    # Optional filter
    # ------------------------
    status = request.args.get("status")

    valid_statuses = ("pending", "approved", "rejected")
    if status and status not in valid_statuses:
        return jsonify({"message": "Invalid status. Must be pending, approved, or rejected"}), 400

    # ------------------------
    # Core logic
    # ------------------------
    try:
        leaves = get_all_leave_requests(status=status)

        return jsonify({
            "success": True,
            "total": len(leaves),
            "leaves": leaves
        }), 200

    # ------------------------
    # Expected / domain errors
    # ------------------------
    except LeaveRequestCreationError:
        return jsonify({"message": "Failed to fetch leave requests"}), 500

    # ------------------------
    # Safety net
    # ------------------------
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


# =========================
# ADMIN - UPDATE LEAVE STATUS
# =========================
@admin_bp.route("/api/admin/leave-requests/<int:leave_id>", methods=["PATCH"])
def admin_update_leave_status(leave_id):
    # ------------------------
    # Auth: verify token + admin check
    # ------------------------
    try:
        auth_header = request.headers.get("Authorization")
        admin_user_id = verify_access_token(auth_header)

        if not is_admin_user(admin_user_id):
            return jsonify({"message": "Forbidden"}), 403

    except (MissingAccessToken, InvalidAccessToken):
        return jsonify({"message": "Unauthorized"}), 401

    # ------------------------
    # Input validation
    # ------------------------
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    status = data.get("status")

    if not status:
        return jsonify({"message": "Missing required field: status"}), 400

    valid_statuses = ("approved", "rejected")
    if status not in valid_statuses:
        return jsonify({"message": "Invalid status. Must be approved or rejected"}), 400

    # ------------------------
    # Core logic
    # ------------------------
    try:
        result = update_leave_status(
            leave_id=leave_id,
            status=status,
        )

        return jsonify({
            "success": True,
            "message": f"Leave request {status} successfully",
            "leave": result
        }), 200

    # ------------------------
    # Expected / domain errors
    # ------------------------
    except LeaveRequestNotFound:
        return jsonify({"message": "Leave request not found"}), 404

    except LeaveAlreadyProcessed as e:
        return jsonify({"message": str(e)}), 409

    except LeaveRequestCreationError:
        return jsonify({"message": "Failed to update leave status"}), 500

    # ------------------------
    # Safety net
    # ------------------------
    except Exception:
        return jsonify({"message": "Internal server error"}), 500
