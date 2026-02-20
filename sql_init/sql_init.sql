CREATE DATABASE IF NOT EXISTS pass_app;
USE pass_app;

-- =========================
-- USERS
-- =========================
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36)
        CHARACTER SET ascii
        COLLATE ascii_bin
        NOT NULL,

    role ENUM('admin', 'client') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    name VARCHAR(255)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id)
) ENGINE=InnoDB;

-- =========================
-- AUTH
-- =========================
CREATE TABLE IF NOT EXISTS auth (
    user_id VARCHAR(36)
        CHARACTER SET ascii
        COLLATE ascii_bin
        NOT NULL,

    username VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),
    UNIQUE KEY uq_auth_username (username),

    CONSTRAINT fk_auth_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================
-- TOKEN SERVICES
-- =========================
CREATE TABLE IF NOT EXISTS token_services (
    token_id BIGINT NOT NULL AUTO_INCREMENT,

    user_id VARCHAR(36)
        CHARACTER SET ascii
        COLLATE ascii_bin
        NOT NULL,

    token_hash VARCHAR(64) NOT NULL,
    token_type ENUM('access', 'refresh') NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (token_id),
    UNIQUE KEY uq_token_hash (token_hash),
    KEY idx_token_user_id (user_id),

    CONSTRAINT fk_token_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================
-- ADMINS
-- =========================
CREATE TABLE IF NOT EXISTS admins (
    user_id VARCHAR(36)
        CHARACTER SET ascii
        COLLATE ascii_bin
        NOT NULL,

    permission_level INT NOT NULL DEFAULT 1,

    granted_by VARCHAR(36)
        CHARACTER SET ascii
        COLLATE ascii_bin
        NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),

    CONSTRAINT chk_admin_permission_level
        CHECK (permission_level BETWEEN 1 AND 3),

    CONSTRAINT fk_admin_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_admin_granted_by
        FOREIGN KEY (granted_by)
        REFERENCES users(user_id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- =========================
-- CLIENTS
-- =========================
CREATE TABLE IF NOT EXISTS clients (
    user_id VARCHAR(36)
        CHARACTER SET ascii
        COLLATE ascii_bin
        NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),

    CONSTRAINT fk_client_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================
-- USERS INFO
-- =========================
CREATE TABLE IF NOT EXISTS users_info (
    user_id VARCHAR(36)
        CHARACTER SET ascii
        COLLATE ascii_bin
        NOT NULL,

    profile_photo_key VARCHAR(255) NULL,

    name VARCHAR(100)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        NOT NULL,

    email VARCHAR(150)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        UNIQUE
        NULL,

    department ENUM(
        'software_development',
        'qa',
        'devops',
        'hr',
        'finance',
        'sales'
    ) NOT NULL,

    designation ENUM(
        'junior_developer',
        'developer',
        'senior_developer',
        'tech_lead',
        'engineering_manager'
    ) NOT NULL,

    phone VARCHAR(15)
        CHARACTER SET ascii
        NOT NULL
        UNIQUE,

    employee_id VARCHAR(20)
        CHARACTER SET ascii
        NOT NULL
        UNIQUE,

    gender ENUM('male', 'female') NOT NULL,

    created_at DATETIME
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),

    CONSTRAINT fk_users_info_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

-- =========================
-- LEAVE REQUESTS
-- =========================
CREATE TABLE IF NOT EXISTS leave_requests (
    leave_id BIGINT NOT NULL AUTO_INCREMENT,

    user_id VARCHAR(36)
        CHARACTER SET ascii
        COLLATE ascii_bin
        NOT NULL,

    leave_type ENUM(
        'casual_leave',
        'sick_leave',
        'annual_leave',
        'emergency_leave'
    ) NOT NULL,

    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    days INT NOT NULL,

    reason TEXT
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        NOT NULL,

    status ENUM('pending', 'approved', 'rejected')
        NOT NULL
        DEFAULT 'pending',

    created_at DATETIME
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (leave_id),
    KEY idx_leave_user_id (user_id),

    CONSTRAINT fk_leave_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================
-- ATTENDANCE
-- =========================
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id BIGINT NOT NULL AUTO_INCREMENT,

    user_id VARCHAR(36)
        CHARACTER SET ascii
        COLLATE ascii_bin
        NOT NULL,

    date DATE NOT NULL,

    clock_in DATETIME NOT NULL,
    clock_out DATETIME NULL,

    status ENUM('present', 'absent', 'half_day', 'late')
        NOT NULL
        DEFAULT 'present',

    created_at DATETIME
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (attendance_id),
    UNIQUE KEY uq_attendance_user_date (user_id, date),
    KEY idx_attendance_user_id (user_id),

    CONSTRAINT fk_attendance_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

