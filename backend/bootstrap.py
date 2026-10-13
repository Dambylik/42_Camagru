"""Add Python session storage without deleting existing account/image data."""
import time
from .db import connect, Database


def initialize():
    for attempt in range(30):
        try:
            connection = connect()
            break
        except Exception:
            if attempt == 29:
                raise
            time.sleep(1)
    try:
        db = Database(connection)
        additions = {'session_version':'INT UNSIGNED NOT NULL DEFAULT 1',
                     'pending_email':'VARCHAR(255) DEFAULT NULL',
                     'email_change_token':'VARCHAR(64) DEFAULT NULL',
                     'email_change_expires_at':'DATETIME DEFAULT NULL'}
        columns = {row['Field'] for row in db.all('SHOW COLUMNS FROM users')}
        for name, definition in additions.items():
            if name not in columns:
                db.execute('ALTER TABLE users ADD COLUMN ' + name + ' ' + definition)
        db.execute('CREATE TABLE IF NOT EXISTS sessions ('
                   'id CHAR(64) PRIMARY KEY,user_id INT UNSIGNED DEFAULT NULL,'
                   'session_version INT UNSIGNED DEFAULT NULL,csrf_token CHAR(64) NOT NULL,'
                   'expires_at BIGINT NOT NULL, INDEX idx_session_expiry(expires_at)) ENGINE=InnoDB')
        connection.commit()
    finally:
        connection.close()
