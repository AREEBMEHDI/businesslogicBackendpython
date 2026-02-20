from flask import Blueprint, request, jsonify
from auth import verify_access_token
from leave import create_leave_request, get_leave_history
from exceptions import (
    MissingAccessToken,
    InvalidAccessToken,
    InvalidLeaveData,
    LeaveRequestCreationError,
)


leave_bp = Blueprint("leave", __name__)


# =========================
# APPLY FOR LEAVE
# =========================
@leave_bp.route("/api/leave/apply", methods=["POST"])
def apply_leave():
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
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "Invalid JSON body"}), 400

    required_fields = ("from_date", "to_date", "leave_type", "reason")
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
        result = create_leave_request(
            user_id=user_id,
            leave_type=data["leave_type"],
            from_date=data["from_date"],
            to_date=data["to_date"],
            reason=data["reason"],
        )

        return jsonify({
            "success": True,
            "message": "Leave request submitted successfully",
            "leave": result
        }), 200

    # ------------------------
    # Expected / domain errors
    # ------------------------
    except InvalidLeaveData as e:
        return jsonify({"message": str(e)}), 400

    except LeaveRequestCreationError:
        return jsonify({"message": "Failed to create leave request"}), 500

    # ------------------------
    # Safety net
    # ------------------------
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


# =========================
# GET LEAVE HISTORY
# =========================
@leave_bp.route("/api/leave/history", methods=["GET"])
def leave_history():
    # ------------------------
    # Auth
    # ------------------------
    try:
        auth_header = request.headers.get("Authorization")
        user_id = verify_access_token(auth_header)

    except (MissingAccessToken, InvalidAccessToken):
        return jsonify({"message": "Unauthorized"}), 401

    # ------------------------
    # Core logic
    # ------------------------
    try:
        history = get_leave_history(user_id=user_id)

        return jsonify({
            "success": True,
            "leaves": history
        }), 200

    except Exception:
        return jsonify({"message": "Internal server error"}), 500
