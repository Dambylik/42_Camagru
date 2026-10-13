-- Apply once to an existing database; new installs use schema.sql.
ALTER TABLE users
    ADD COLUMN session_version INT UNSIGNED NOT NULL DEFAULT 1,
    ADD COLUMN pending_email VARCHAR(255) DEFAULT NULL,
    ADD COLUMN email_change_token VARCHAR(64) DEFAULT NULL,
    ADD COLUMN email_change_expires_at DATETIME DEFAULT NULL;
