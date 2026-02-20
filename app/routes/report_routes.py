from flask import Blueprint, request, jsonify
from datetime import date
from auth import verify_access_token
from reports import get_monthly_report
from exceptions import (
    MissingAccessToken,
    InvalidAccessToken,
    ReportError,
)


report_bp = Blueprint("report", __name__)


# =========================
# MONTHLY REPORT
# =========================
@report_bp.route("/api/reports/monthly", methods=["GET"])
def api_monthly_report():
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
    today = date.today()
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    if not (1 <= month <= 12):
        return jsonify({"message": "Invalid month. Must be 1-12"}), 400

    if not (2000 <= year <= 2100):
        return jsonify({"message": "Invalid year"}), 400

    # ------------------------
    # Core logic
    # ------------------------
    try:
        report = get_monthly_report(
            user_id=user_id,
            month=month,
            year=year,
        )

        return jsonify({
            "success": True,
            "report": report
        }), 200

    # ------------------------
    # Expected / domain errors
    # ------------------------
    except ReportError as e:
        return jsonify({"message": str(e)}), 400

    # ------------------------
    # Safety net
    # ------------------------
    except Exception:
        return jsonify({"message": "Internal server error"}), 500
