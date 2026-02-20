from datetime import datetime, date, timedelta
from calendar import monthrange
from sqlalchemy import func, extract
from models import db, Attendance, LeaveRequests
from exceptions import ReportError


# Default annual leave allocations per type
LEAVE_ALLOCATIONS = {
    "casual_leave": 12,
    "sick_leave": 10,
    "annual_leave": 15,
    "emergency_leave": 5,
}

LEAVE_TYPE_DISPLAY = {
    "casual_leave": "Casual Leave",
    "sick_leave": "Sick Leave",
    "annual_leave": "Annual Leave",
    "emergency_leave": "Emergency Leave",
}

LEAVE_TYPE_COLORS = {
    "casual_leave": "#0C6B46",
    "sick_leave": "#3B82F6",
    "annual_leave": "#D97706",
    "emergency_leave": "#DC2626",
}


def get_monthly_report(*, user_id: str, month: int, year: int) -> dict:
    """
    Returns the full monthly report for a user.
    Includes attendance summary, leave summary, working hours,
    and performance score.
    """

    # ------------------------
    # Validate month/year
    # ------------------------
    if month < 1 or month > 12:
        raise ReportError("Invalid month")

    if year < 2000 or year > 2100:
        raise ReportError("Invalid year")

    try:
        attendance = _get_attendance_summary(
            user_id=user_id, month=month, year=year
        )
        leaves = _get_leave_summary(
            user_id=user_id, year=year
        )
        hours = _get_working_hours(
            user_id=user_id, month=month, year=year
        )
        performance = _get_performance_score(attendance=attendance)

        return {
            "month": month,
            "year": year,
            "attendance": attendance,
            "leaves": leaves,
            "hours": hours,
            "performance": performance,
        }

    except ReportError:
        raise
    except Exception as e:
        raise ReportError("Failed to generate report") from e


def _get_attendance_summary(*, user_id: str, month: int, year: int) -> dict:
    """
    Calculates attendance summary for a given month.
    """

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    today = date.today()

    # Only count up to today if the month is current
    end_date = min(last_day, today)

    # Count working days (Mon-Fri)
    working_days = 0
    current = first_day
    while current <= end_date:
        if current.weekday() < 5:
            working_days += 1
        current += timedelta(days=1)

    # Fetch attendance records for the month
    records = Attendance.query.filter(
        Attendance.user_id == user_id,
        Attendance.date >= first_day,
        Attendance.date <= end_date
    ).all()

    present_days = 0
    absent_days = 0
    late_days = 0
    half_days = 0

    for record in records:
        if record.status == "present":
            present_days += 1
        elif record.status == "absent":
            absent_days += 1
        elif record.status == "late":
            late_days += 1
        elif record.status == "half_day":
            half_days += 1

    # Days with no record on working days count as absent
    days_with_records = len([
        r for r in records if r.date.weekday() < 5
    ])
    absent_days += max(0, working_days - days_with_records)

    # Attendance rate: days attended / working days
    attended = present_days + late_days + half_days
    rate = round((attended / working_days) * 100) if working_days > 0 else 0

    return {
        "working_days": working_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "late_days": late_days,
        "half_days": half_days,
        "rate": rate,
    }


def _get_leave_summary(*, user_id: str, year: int) -> list:
    """
    Calculates leave usage per type for the given year.
    Only counts approved leaves.
    """

    first_of_year = date(year, 1, 1)
    last_of_year = date(year, 12, 31)

    approved_leaves = LeaveRequests.query.filter(
        LeaveRequests.user_id == user_id,
        LeaveRequests.status == "approved",
        LeaveRequests.from_date >= first_of_year,
        LeaveRequests.to_date <= last_of_year,
    ).all()

    # Sum days per leave type
    used_by_type = {}
    for leave in approved_leaves:
        used_by_type[leave.leave_type] = (
            used_by_type.get(leave.leave_type, 0) + leave.days
        )

    result = []
    for leave_type, total in LEAVE_ALLOCATIONS.items():
        used = used_by_type.get(leave_type, 0)
        result.append({
            "type": LEAVE_TYPE_DISPLAY[leave_type],
            "total": total,
            "used": used,
            "balance": max(0, total - used),
            "color": LEAVE_TYPE_COLORS[leave_type],
        })

    return result


def _get_working_hours(*, user_id: str, month: int, year: int) -> dict:
    """
    Calculates working hour stats for a given month.
    """

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    today = date.today()
    end_date = min(last_day, today)

    # Expected working days
    working_days = 0
    current = first_day
    while current <= end_date:
        if current.weekday() < 5:
            working_days += 1
        current += timedelta(days=1)

    expected_hours = working_days * 8

    # Fetch attendance records
    records = Attendance.query.filter(
        Attendance.user_id == user_id,
        Attendance.date >= first_day,
        Attendance.date <= end_date
    ).all()

    total_hours = 0.0
    days_counted = 0

    for record in records:
        if record.clock_in and record.clock_out:
            diff = (record.clock_out - record.clock_in).total_seconds() / 3600.0
            total_hours += diff
            days_counted += 1
        elif record.clock_in:
            # Still clocked in, count hours so far
            diff = (datetime.utcnow() - record.clock_in).total_seconds() / 3600.0
            total_hours += diff
            days_counted += 1

    overtime = max(0.0, total_hours - expected_hours)
    avg_daily = round(total_hours / days_counted, 1) if days_counted > 0 else 0.0

    return {
        "expected": round(expected_hours, 1),
        "actual": round(total_hours, 1),
        "overtime": round(overtime, 1),
        "avg_daily": avg_daily,
    }


def _get_performance_score(*, attendance: dict) -> dict:
    """
    Derives a performance score from attendance data.
    """

    rate = attendance["rate"]

    if rate >= 95:
        grade = "A+"
        message = "Excellent performance! Keep up the great work."
    elif rate >= 90:
        grade = "A"
        message = "Great performance! You're doing well."
    elif rate >= 80:
        grade = "B"
        message = "Good performance. There's room for improvement."
    elif rate >= 70:
        grade = "C"
        message = "Average performance. Try to improve attendance."
    else:
        grade = "D"
        message = "Needs improvement. Please focus on attendance."

    return {
        "grade": grade,
        "message": message,
        "attendance_rate": rate,
    }
