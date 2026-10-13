"""Overlays persistence: parameterized SQL only."""


class OverlayModel:
    def __init__(self, db):
        self.db = db

    def all(self):
        return self.db.all('SELECT * FROM overlays ORDER BY id')
