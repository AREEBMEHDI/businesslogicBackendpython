from datetime import datetime, date, timedelta
from models import db, Attendance
from exceptions import (
    AttendanceError,
    AlreadyClockedIn,
    NotClockedIn,
    AlreadyClockedOut,
)


def clock_in(*, user_id: str) -> dict:
    """
    Records clock-in for the current day.
    Returns attendance record dict.
    Raises AttendanceError subclasses on failure.
    """

    today = date.today()
    now = datetime.utcnow()

    # ------------------------
    # Check if already clocked in today
    # ------------------------
    existing = Attendance.query.filter_by(
        user_id=user_id,
        date=today
    ).first()

    if existing:
        raise AlreadyClockedIn("Already clocked in today")

    try:
        record = Attendance(
            user_id=user_id,
            date=today,
            clock_in=now,
            clock_out=None,
            status="present",
            created_at=now,
            updated_at=now,
        )
        db.session.add(record)
        db.session.commit()

        return _format_attendance(record)

    except (AlreadyClockedIn,):
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise AttendanceError("Failed to clock in") from e


def clock_out(*, user_id: str) -> dict:
    """
    Records clock-out for the current day.
    Returns attendance record dict.
    Raises AttendanceError subclasses on failure.
    """

    today = date.today()
    now = datetime.utcnow()

    # ------------------------
    # Check if clocked in today
    # ------------------------
    record = Attendance.query.filter_by(
        user_id=user_id,
        date=today
    ).first()

    if not record:
        raise NotClockedIn("Not clocked in today")

    if record.clock_out is not None:
        raise AlreadyClockedOut("Already clocked out today")

    try:
        record.clock_out = now
        record.updated_at = now
        db.session.commit()

        return _format_attendance(record)

    except (NotClockedIn, AlreadyClockedOut):
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise AttendanceError("Failed to clock out") from e


def get_today_summary(*, user_id: str) -> dict:
    """
    Returns today's attendance summary for the user.
    """

    today = date.today()

    record = Attendance.query.filter_by(
        user_id=user_id,
        date=today
    ).first()

    if not record:
        return {
            "date": today.strftime("%d %b %Y"),
            "clock_in": None,
            "clock_out": None,
            "status": "absent",
            "is_clocked_in": False,
        }

    return {
        "date": record.date.strftime("%d %b %Y"),
        "clock_in": record.clock_in.strftime("%I:%M %p") if record.clock_in else None,
        "clock_out": record.clock_out.strftime("%I:%M %p") if record.clock_out else None,
        "status": record.status,
        "is_clocked_in": record.clock_out is None,
    }


def get_weekly_attendance(*, user_id: str) -> list:
    """
    Returns attendance records for the current week (Monday to Sunday).
    """

    today = date.today()
    weekday = today.weekday()  # Monday=0, Sunday=6
    monday = today - timedelta(days=weekday)
    sunday = monday + timedelta(days=6)

    records = Attendance.query.filter(
        Attendance.user_id == user_id,
        Attendance.date >= monday,
        Attendance.date <= sunday
    ).all()

    # Index by date for quick lookup
    records_by_date = {r.date: r for r in records}

    day_names = ["M", "T", "W", "T", "F", "S", "S"]
    week = []
    for i in range(7):
        day = monday + timedelta(days=i)
        record = records_by_date.get(day)
        week.append({
            "name": day_names[i],
            "date": day.day,
            "full_date": day.isoformat(),
            "is_today": day == today,
            "is_past": day < today,
            "status": record.status if record else None,
        })

    return week


def get_monthly_stats(*, user_id: str) -> dict:
    """
    Returns monthly attendance statistics for the current month.
    """

    today = date.today()
    first_of_month = today.replace(day=1)

    records = Attendance.query.filter(
        Attendance.user_id == user_id,
        Attendance.date >= first_of_month,
        Attendance.date <= today
    ).all()

    total_hours = 0.0
    days_present = 0

    for record in records:
        if record.clock_in and record.clock_out:
            diff = (record.clock_out - record.clock_in).total_seconds() / 3600.0
            total_hours += diff
            days_present += 1
        elif record.clock_in:
            # Still clocked in, count hours so far
            diff = (datetime.utcnow() - record.clock_in).total_seconds() / 3600.0
            total_hours += diff
            days_present += 1

    # Expected: 8 hours per working day (Mon-Fri) in the month so far
    expected_days = 0
    current = first_of_month
    while current <= today:
        if current.weekday() < 5:  # Monday to Friday
            expected_days += 1
        current += timedelta(days=1)

    expected_hours = expected_days * 8
    avg_daily = round(total_hours / days_present, 1) if days_present > 0 else 0.0

    return {
        "expected_hours": round(expected_hours, 1),
        "actual_hours": round(total_hours, 1),
        "avg_daily": avg_daily,
        "days_present": days_present,
        "working_days": expected_days,
    }


def _format_attendance(record: Attendance) -> dict:
    """
    Formats an attendance record into a response dict.
    """
    return {
        "attendance_id": record.attendance_id,
        "date": record.date.strftime("%d %b %Y"),
        "clock_in": record.clock_in.strftime("%I:%M %p") if record.clock_in else None,
        "clock_out": record.clock_out.strftime("%I:%M %p") if record.clock_out else None,
        "status": record.status,
        "is_clocked_in": record.clock_out is None,
    }
