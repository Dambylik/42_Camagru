"""Database-backed session persistence."""

class SessionModel:
    def __init__(self, db):
        self.db = db

    def expire(self, values):
        return self.db.execute('DELETE FROM sessions WHERE expires_at < %s', values)

    def find(self, values):
        return self.db.one('SELECT * FROM sessions WHERE id = %s AND expires_at >= %s FOR UPDATE', values)

    def create_anonymous(self, values):
        return self.db.execute('INSERT INTO sessions (id, csrf_token, expires_at) VALUES (%s,%s,%s)', values)

    def delete(self, values):
        return self.db.execute('DELETE FROM sessions WHERE id = %s', values)

    def create_authenticated(self, values):
        return self.db.execute('INSERT INTO sessions (id,user_id,session_version,csrf_token,expires_at) VALUES (%s,%s,%s,%s,%s)', values)
