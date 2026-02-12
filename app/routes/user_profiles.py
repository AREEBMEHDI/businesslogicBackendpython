from flask import request, jsonify, Blueprint
from typing import Optional, Dict, List
from models import db, Users, UsersInfo, UserSocial, Auth
from auth import verify_access_token
from exceptions import MissingAccessToken, InvalidAccessToken

1

# ==================== Helper Functions ====================


def get_user_profile_info(user_id: str) -> Optional[Dict]:
    """
    Fetch user profile information from UsersInfo table.

    Args:
        user_id: The user's UUID

    Returns:
        Dictionary with profile info or None if not found
    """
    try:
        user_info = UsersInfo.query.filter_by(user_id=user_id).first()
        if not user_info:
            return None

        return {
            "name": user_info.name,
            "gender": user_info.gender,
            "email": user_info.email,
            "department": user_info.department,
            "designation": user_info.designation,
            "phone": user_info.phone,
            "employee_id": user_info.employee_id,
            "department": user_info.department,
            "created_at": user_info.created_at.isoformat() if user_info.created_at else None,
            "updated_at": user_info.updated_at.isoformat() if user_info.updated_at else None
        }
    except Exception as e:
        print(f"Error fetching user profile info: {e}")
        return None


@profile.route('/my_profile/details', methods=['GET'])
def get_my_profile_details():
    """
    Get profile details (display name, gender, vibe, photo) of the authenticated user.
    Requires Bearer token authentication.

    Headers:
        Authorization: Bearer <access_token>

    Response:
        {
            "success": true,
            "display_name": "Johnny",
            "gender": "male",
            "vibe": "Always down for coffee!",
            "profile_photo_key": "photos/uuid.jpg",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-15T00:00:00"
        }
    """
    try:
        # Verify access token and get user_id
        auth_header = request.headers.get('Authorization')
        try:
            user_id = verify_access_token(auth_header)
        except (MissingAccessToken, InvalidAccessToken) as e:
            return jsonify({"error": str(e)}), 401

        # Get profile details
        profile_info = get_user_profile_info(user_id)

        if not profile_info:
            return jsonify({"error": "Profile details not found"}), 404

        return jsonify({
            "success": True,
            **profile_info
        }), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


