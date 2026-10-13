# Camagrrru

Python 3.10 backend with Nginx, MariaDB and native HTML/CSS/JavaScript.
Requirements reference: `en.subject.camagru.pdf`, Version 4.1.

## Start

Start Docker Desktop, then run `make up` from this folder.
Open http://localhost:8000. Account-confirmation, reset and comment emails can be
inspected in Mailpit at http://localhost:8025.

A missing `.env` is generated with random database credentials using Python 3 on the
host. Credentials remain in the ignored `.env`; never commit them. Existing `.env`
settings are used as-is. No npm or Composer is required.

## Request flow

Browser → Nginx (`web`) → Python WSGI application (`app`) → MariaDB (`db`).
Nginx serves CSS, JavaScript, overlays and uploaded PNGs directly. Python handles
accounts, gallery queries, comments, likes and server-side image composition.
The app container has no host-published port. Only Nginx is exposed at localhost:8000.

## Files

- `config/nginx.Dockerfile`, `config/nginx.conf`: Nginx image and routing.
- `Dockerfile`, `config/docker-entrypoint.sh`: Python image and runtime user.
- `backend/server.py`: standard-library WSGI entry point, form parsing and request limits.
- `backend/application.py`: application routes and database operations.
- `backend/views.py`: escaped HTML rendering.
- `backend/security.py`: password validation/hashing, sessions and CSRF.
- `backend/db.py`: parameterized SQL access.
- `backend/imaging.py`: server-side image validation and overlay composition.
- `backend/mail.py`: SMTP email delivery.
- `public/`: browser assets and overlay images.
- `sql/schema.sql`, `sql/seeds.sql`: initialize a fresh database, including sessions.

There are no source/test bind mounts, PHP routes or migration compatibility helpers.
Rebuild after changing source: `make up`.
The database health check ensures its initial schema is ready before Python starts;
there is no web health endpoint or web health check.

## Subject functionality

Registration requires email confirmation. Reset links expire and are single-use.
Authenticated users can change username, password, email and notification preference.
Email changes require confirmation; security changes revoke older sessions.
Logout is a one-click CSRF-protected button. The public gallery shows newest images
first, five per page. Only logged-in users can like/comment. Comment emails are
on by default and can be disabled. Capture requires a base image and at least one
overlay per V.4. PHP-equivalent image composition takes place on the Python server.
Users may delete only their own creations. Live preview and AJAX/infinite gallery
loading are retained.

Runtime dependencies and their PHP equivalents:

| Python functionality | PHP equivalent |
| --- | --- |
| PyMySQL parameterized SQL and transactions | PDO parameterized SQL and transactions |
| bcrypt hashing/verification | password_hash/password_verify |
| Pillow image decoding, resizing, alpha composition, PNG output | GD imagecreatefromstring/imagecopyresampled/alpha blending/imagepng |
| WSGI server | PHP built-in server; Nginx is explicitly allowed by the subject |
| secrets random tokens / constant-time comparison | random_bytes/bin2hex/hash_equals |
| hashlib | hash |
| HTML escaping, regex, JSON, base64 | htmlspecialchars, preg_match, json_encode/decode, base64_decode |
| SMTP delivery | mail with configured SMTP transport |
| URL parsing, cookies, server-side sessions | parse_url/parse_str, setcookie, custom session storage |
| Filesystem, time, basic collections and exceptions | PHP filesystem/time/array functions and exceptions |

PyMySQL uses parameterized DB-API queries, not MariaDB server-side PREPARE commands.
No application query interpolates user input. The dependency mapping documents our
interpretation of the subject's PHP-equivalent rule for evaluation.

## Data and diagnostics

`db_data` persists the database; `uploads_data` persists photos and is mounted read-only
in Nginx. `public/overlays` is packaged into both images and is not deleted by volume resets.

`make down` keeps data. `make clean`, `make fclean` and `make re` delete database/uploads.
Only use those reset commands when that is intended.

Application errors return generic responses and are recorded privately in
`/tmp/camagru-errors.log` inside `app`. Nginx errors are recorded in
`/tmp/camagru-nginx-errors.log` inside `web`. Routine access logs are disabled.
Inspect these files and the browser console during evaluation; an empty console alone
does not prove correctness. Real webcam hardware and Firefox compatibility remain to
be verified manually on this host.
