from flask import Blueprint, request, jsonify
from auth import verify_access_token
from attendance import clock_in, clock_out, get_today_summary, get_weekly_attendance, get_monthly_stats
from exceptions import (
    MissingAccessToken,
    InvalidAccessToken,
    AttendanceError,
    AlreadyClockedIn,
    NotClockedIn,
    AlreadyClockedOut,
)


attendance_bp = Blueprint("attendance", __name__)


# =========================
# CLOCK IN
# =========================
@attendance_bp.route("/api/attendance/clock-in", methods=["POST"])
def api_clock_in():
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
        result = clock_in(user_id=user_id)

        return jsonify({
            "success": True,
            "message": "Clocked in successfully",
            "attendance": result
        }), 200

    # ------------------------
    # Expected / domain errors
    # ------------------------
    except AlreadyClockedIn:
        return jsonify({"message": "Already clocked in today"}), 409

    except AttendanceError:
        return jsonify({"message": "Failed to clock in"}), 500

    # ------------------------
    # Safety net
    # ------------------------
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


# =========================
# CLOCK OUT
# =========================
@attendance_bp.route("/api/attendance/clock-out", methods=["POST"])
def api_clock_out():
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
        result = clock_out(user_id=user_id)

        return jsonify({
            "success": True,
            "message": "Clocked out successfully",
            "attendance": result
        }), 200

    # ------------------------
    # Expected / domain errors
    # ------------------------
    except NotClockedIn:
        return jsonify({"message": "Not clocked in today"}), 400

    except AlreadyClockedOut:
        return jsonify({"message": "Already clocked out today"}), 409

    except AttendanceError:
        return jsonify({"message": "Failed to clock out"}), 500

    # ------------------------
    # Safety net
    # ------------------------
    except Exception:
        return jsonify({"message": "Internal server error"}), 500


# =========================
# TODAY'S SUMMARY
# =========================
@attendance_bp.route("/api/attendance/today", methods=["GET"])
def api_today_summary():
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
        summary = get_today_summary(user_id=user_id)

        return jsonify({
            "success": True,
            "summary": summary
        }), 200

    except Exception:
        return jsonify({"message": "Internal server error"}), 500


# =========================
# WEEKLY ATTENDANCE
# =========================
@attendance_bp.route("/api/attendance/week", methods=["GET"])
def api_weekly_attendance():
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
        week = get_weekly_attendance(user_id=user_id)

        return jsonify({
            "success": True,
            "week": week
        }), 200

    except Exception:
        return jsonify({"message": "Internal server error"}), 500


# =========================
# MONTHLY STATS
# =========================
@attendance_bp.route("/api/attendance/stats", methods=["GET"])
def api_monthly_stats():
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
        stats = get_monthly_stats(user_id=user_id)

        return jsonify({
            "success": True,
            "stats": stats
        }), 200

    except Exception:
        return jsonify({"message": "Internal server error"}), 500
