"""Generate local credentials without printing or committing them."""
import os
import secrets
from pathlib import Path

path = Path(__file__).resolve().parent.parent / '.env'
content = ('MYSQL_DATABASE=camagru\nMYSQL_USER=camagru\n'
           f'MYSQL_PASSWORD={secrets.token_hex(24)}\n'
           f'MYSQL_ROOT_PASSWORD={secrets.token_hex(24)}\n'
           'APP_URL=http://localhost:8000\nMAIL_FROM=noreply@camagru.local\n')
descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(descriptor,'w') as stream:
    stream.write(content)
