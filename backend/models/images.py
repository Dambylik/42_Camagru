"""Images persistence: parameterized SQL only."""


class ImageModel:
    def __init__(self, db):
        self.db = db

    def paginate(self, values):
        return self.db.all('SELECT i.*,u.username,(SELECT COUNT(*) FROM likes l WHERE l.image_id=i.id) AS like_count FROM images i JOIN users u ON u.id=i.user_id ORDER BY i.created_at DESC,i.id DESC LIMIT 5 OFFSET %s', values)

    def count(self):
        return self.db.one('SELECT COUNT(*) AS n FROM images')

    def has_liked(self, values):
        return self.db.one('SELECT 1 FROM likes WHERE user_id=%s AND image_id=%s', values)

    def find_for_update(self, values):
        return self.db.one('SELECT * FROM images WHERE id=%s FOR UPDATE', values)

    def unlike(self, values):
        return self.db.execute('DELETE FROM likes WHERE user_id=%s AND image_id=%s', values)

    def like(self, values):
        return self.db.execute('INSERT INTO likes (user_id,image_id) VALUES (%s,%s)', values)

    def like_count(self, values):
        return self.db.one('SELECT COUNT(*) AS n FROM likes WHERE image_id=%s', values)

    def by_user(self, values):
        return self.db.all('SELECT * FROM images WHERE user_id=%s ORDER BY id DESC', values)

    def create(self, values):
        return self.db.execute('INSERT INTO images (user_id,path) VALUES (%s,%s)', values)

    def delete(self, values):
        return self.db.execute('DELETE FROM images WHERE id=%s', values)
