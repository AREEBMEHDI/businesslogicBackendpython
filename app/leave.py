from datetime import datetime
from models import db, LeaveRequests, UsersInfo
from exceptions import (
    InvalidLeaveData,
    LeaveRequestCreationError,
    LeaveRequestNotFound,
    LeaveAlreadyProcessed,
)


VALID_LEAVE_TYPES = {
    "Casual Leave": "casual_leave",
    "Sick Leave": "sick_leave",
    "Annual Leave": "annual_leave",
    "Emergency Leave": "emergency_leave",
}

LEAVE_TYPE_DISPLAY = {v: k for k, v in VALID_LEAVE_TYPES.items()}


def create_leave_request(
    *,
    user_id: str,
    leave_type: str,
    from_date: str,
    to_date: str,
    reason: str,
) -> dict:
    """
    Creates a leave request for the given user.
    Returns leave request dict.
    Raises LeaveRequestError subclasses on failure.
    """

    # ------------------------
    # Basic validation
    # ------------------------
    if not user_id or not leave_type or not from_date or not to_date or not reason:
        raise InvalidLeaveData("Missing required fields")

    # Normalize leave type from frontend display name to enum value
    leave_type_enum = VALID_LEAVE_TYPES.get(leave_type)
    if not leave_type_enum:
        raise InvalidLeaveData("Invalid leave type")

    # Parse dates
    try:
        parsed_from = datetime.strptime(from_date, "%m/%d/%Y").date()
        parsed_to = datetime.strptime(to_date, "%m/%d/%Y").date()
    except ValueError:
        raise InvalidLeaveData("Invalid date format. Use mm/dd/yyyy")

    if parsed_to < parsed_from:
        raise InvalidLeaveData("To date cannot be before from date")

    # Calculate days (inclusive)
    days = (parsed_to - parsed_from).days + 1

    try:
        leave = LeaveRequests(
            user_id=user_id,
            leave_type=leave_type_enum,
            from_date=parsed_from,
            to_date=parsed_to,
            days=days,
            reason=reason.strip(),
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(leave)
        db.session.commit()

        return {
            "leave_id": leave.leave_id,
            "leave_type": leave_type,
            "from_date": parsed_from.strftime("%d %b %Y"),
            "to_date": parsed_to.strftime("%d %b %Y"),
            "days": days,
            "reason": leave.reason,
            "status": leave.status,
            "created_at": leave.created_at.isoformat(),
        }

    except (InvalidLeaveData,):
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise LeaveRequestCreationError("Failed to create leave request") from e


def get_leave_history(*, user_id: str) -> list:
    """
    Fetches all leave requests for a user, ordered by most recent first.
    """

    try:
        leaves = LeaveRequests.query.filter_by(
            user_id=user_id
        ).order_by(LeaveRequests.created_at.desc()).all()

        return [
            {
                "leave_id": leave.leave_id,
                "leave_type": LEAVE_TYPE_DISPLAY.get(leave.leave_type, leave.leave_type),
                "from_date": leave.from_date.strftime("%d %b %Y"),
                "to_date": leave.to_date.strftime("%d %b %Y"),
                "days": leave.days,
                "reason": leave.reason,
                "status": leave.status,
                "created_at": leave.created_at.isoformat(),
            }
            for leave in leaves
        ]

    except Exception as e:
        raise LeaveRequestCreationError("Failed to fetch leave history") from e


def get_all_leave_requests(*, status: str = None) -> list:
    """
    Fetches all leave requests across all users.
    Optionally filters by status (pending, approved, rejected).
    Returns list of leave request dicts with user info.
    """

    try:
        query = db.session.query(
            LeaveRequests, UsersInfo
        ).outerjoin(
            UsersInfo, LeaveRequests.user_id == UsersInfo.user_id
        ).order_by(LeaveRequests.created_at.desc())

        # ------------------------
        # Optional status filter
        # ------------------------
        if status:
            query = query.filter(LeaveRequests.status == status)

        results = query.all()

        return [
            {
                "leave_id": leave.leave_id,
                "user_id": leave.user_id,
                "employee_name": info.name if info else None,
                "employee_id": info.employee_id if info else None,
                "department": info.department if info else None,
                "leave_type": LEAVE_TYPE_DISPLAY.get(leave.leave_type, leave.leave_type),
                "from_date": leave.from_date.strftime("%d %b %Y"),
                "to_date": leave.to_date.strftime("%d %b %Y"),
                "days": leave.days,
                "reason": leave.reason,
                "status": leave.status,
                "created_at": leave.created_at.isoformat(),
            }
            for leave, info in results
        ]

    except Exception as e:
        raise LeaveRequestCreationError("Failed to fetch leave requests") from e


def update_leave_status(*, leave_id: int, status: str) -> dict:
    """
    Updates the status of a leave request (approve or reject).
    Returns updated leave request dict.
    Raises LeaveRequestError subclasses on failure.
    """

    # ------------------------
    # Fetch leave request
    # ------------------------
    leave = LeaveRequests.query.filter_by(leave_id=leave_id).first()

    if not leave:
        raise LeaveRequestNotFound("Leave request not found")

    # ------------------------
    # Check if already processed
    # ------------------------
    if leave.status != "pending":
        raise LeaveAlreadyProcessed(
            f"Leave request already {leave.status}"
        )

    # ------------------------
    # Update status
    # ------------------------
    try:
        leave.status = status
        leave.updated_at = datetime.utcnow()
        db.session.commit()

        return {
            "leave_id": leave.leave_id,
            "user_id": leave.user_id,
            "leave_type": LEAVE_TYPE_DISPLAY.get(leave.leave_type, leave.leave_type),
            "from_date": leave.from_date.strftime("%d %b %Y"),
            "to_date": leave.to_date.strftime("%d %b %Y"),
            "days": leave.days,
            "reason": leave.reason,
            "status": leave.status,
            "updated_at": leave.updated_at.isoformat(),
        }

    except (LeaveRequestNotFound, LeaveAlreadyProcessed):
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise LeaveRequestCreationError("Failed to update leave status") from e
