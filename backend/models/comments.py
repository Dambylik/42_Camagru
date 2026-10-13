"""Comments persistence: parameterized SQL only."""


class CommentModel:
    def __init__(self, db):
        self.db = db

    def by_image(self, values):
        return self.db.all('SELECT c.content,u.username FROM comments c JOIN users u ON u.id=c.user_id WHERE c.image_id=%s ORDER BY c.id', values)

    def create(self, values):
        return self.db.execute('INSERT INTO comments (image_id,user_id,content) VALUES (%s,%s,%s)', values)
