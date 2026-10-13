"""Users persistence: parameterized SQL only."""


class UserModel:
    def __init__(self, db):
        self.db = db

    def find_by(self, column, value):
        if column not in ('id', 'email', 'username'):
            raise ValueError('Unsupported user lookup')
        return self.db.one('SELECT * FROM users WHERE ' + column + ' = %s', (value,))

    def create(self, values):
        return self.db.execute('INSERT INTO users (username,email,password,verify_token,verify_expires_at) VALUES (%s,%s,%s,%s,DATE_ADD(NOW(), INTERVAL 24 HOUR))', values)

    def confirm(self, values):
        return self.db.execute('UPDATE users SET is_verified=1,verify_token=NULL,verify_expires_at=NULL WHERE verify_token=%s AND verify_expires_at>NOW()', values)

    def set_reset_token(self, values):
        return self.db.execute('UPDATE users SET reset_token=%s,reset_expires_at=DATE_ADD(NOW(),INTERVAL 1 HOUR) WHERE id=%s', values)

    def find_reset_token(self, values):
        return self.db.one('SELECT * FROM users WHERE reset_token=%s AND reset_expires_at>NOW() FOR UPDATE', values)

    def update_password(self, values):
        return self.db.execute('UPDATE users SET password=%s,session_version=session_version+1,reset_token=NULL,reset_expires_at=NULL,pending_email=NULL,email_change_token=NULL,email_change_expires_at=NULL WHERE id=%s', values)

    def update_username(self, values):
        return self.db.execute('UPDATE users SET username=%s WHERE id=%s', values)

    def update_notifications(self, values):
        return self.db.execute('UPDATE users SET notify_on_comment=%s WHERE id=%s', values)

    def request_email_change(self, values):
        return self.db.execute('UPDATE users SET pending_email=%s,email_change_token=%s,email_change_expires_at=DATE_ADD(NOW(),INTERVAL 1 HOUR) WHERE id=%s', values)

    def find_email_change(self, values):
        return self.db.one('SELECT * FROM users WHERE email_change_token=%s AND email_change_expires_at>NOW() FOR UPDATE', values)

    def confirm_email_change(self, values):
        return self.db.execute('UPDATE users SET email=pending_email,pending_email=NULL,email_change_token=NULL,email_change_expires_at=NULL,reset_token=NULL,reset_expires_at=NULL,session_version=session_version+1 WHERE id=%s', values)
