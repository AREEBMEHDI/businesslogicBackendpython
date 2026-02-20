class ClientCreationError(Exception):
    """Base error for client creation failures."""
    pass


class UsernameAlreadyExists(ClientCreationError):
    """Raised when username already exists."""
    pass


class InvalidClientData(ClientCreationError):
    """Raised when input validation fails."""
    pass

##########################################################

class UserInfoCreationError(Exception):
    pass


class InvalidUserInfoData(UserInfoCreationError):
    pass


##########################################################

class AuthenticationError(Exception):
    """Base class for auth-related errors"""
    pass


class InvalidCredentials(AuthenticationError):
    """Username or password is wrong"""
    pass


class InactiveUser(AuthenticationError):
    """User exists but is disabled"""
    pass


class MissingCredentials(AuthenticationError):
    """Username or password missing"""
    pass


class NotAnAdmin(AuthenticationError):
    """User is not an admin"""
    pass


##########################################################

class RefreshTokenError(Exception):
    """Base class for refresh-token-related errors"""
    pass


class MissingRefreshToken(RefreshTokenError):
    """Refresh token missing"""
    pass

class InvalidRefreshToken(RefreshTokenError):
    """Invalid Refresh token"""
    pass

##########################################################

class AccessTokenError(Exception):
    """Base class for refresh-token-related errors"""
    pass


class MissingAccessToken(RefreshTokenError):
    """Refresh token missing"""
    pass

class InvalidAccessToken(RefreshTokenError):
    """Invalid Refresh token"""
    pass


####################################################

class ProfilePhotoError(Exception):
    pass

class ProfilePhotoUploadError(ProfilePhotoError):
    pass

class InvalidProfileImage(ProfilePhotoError):
    pass

class ProfilePhotoDeleteError(ProfilePhotoError):
    pass

class UserProfilePhotoUpdateError(ProfilePhotoError):
    pass

class UserProfilePhotoNotFound(ProfilePhotoError):
    pass

#######################################################

class UserProfileNotFound(Exception):
    pass


#######################################################

class SocialMediaError(Exception):
    pass

class InvalidSocialPlatform(SocialMediaError):
    pass


class InvalidSocialHandle(SocialMediaError):
    pass


class SocialUpsertError(SocialMediaError):
    pass


#######################################################

class LeaveRequestError(Exception):
    """Base error for leave request failures."""
    pass


class InvalidLeaveData(LeaveRequestError):
    """Raised when input validation fails."""
    pass


class LeaveRequestCreationError(LeaveRequestError):
    """Raised when leave request creation fails."""
    pass


class LeaveRequestNotFound(LeaveRequestError):
    """Raised when leave request does not exist."""
    pass


class LeaveAlreadyProcessed(LeaveRequestError):
    """Raised when leave request has already been approved or rejected."""
    pass


#######################################################

class AttendanceError(Exception):
    """Base error for attendance failures."""
    pass


class AlreadyClockedIn(AttendanceError):
    """Raised when user tries to clock in but already clocked in today."""
    pass


class NotClockedIn(AttendanceError):
    """Raised when user tries to clock out but hasn't clocked in today."""
    pass


class AlreadyClockedOut(AttendanceError):
    """Raised when user tries to clock out but already clocked out today."""
    pass


#######################################################

class ReportError(Exception):
    """Base error for report generation failures."""
    pass
