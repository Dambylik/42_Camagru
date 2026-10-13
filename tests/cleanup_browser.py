"""Remove only explicitly named browser-smoke fixtures; reads names from stdin."""
import re
import sys
from pathlib import Path
sys.path.insert(0, '/app')
from backend.db import connect, Database

connection = connect()
db = Database(connection)
try:
    for name in sys.stdin.read().splitlines():
        if not re.fullmatch(r'browser_(chrome|firefox)_[a-z0-9]+',name):
            raise ValueError('Not a browser-smoke fixture name')
        user = db.one('SELECT id FROM users WHERE username=%s',(name,))
        if user:
            images = db.all('SELECT path FROM images WHERE user_id=%s',(user['id'],))
            db.execute('DELETE FROM sessions WHERE user_id=%s',(user['id'],))
            db.execute('DELETE FROM users WHERE id=%s',(user['id'],))
            connection.commit()
            for image in images:
                (Path('/app/public/uploads') / Path(image['path']).name).unlink(missing_ok=True)
finally:
    connection.close()
