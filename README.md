# Camagrrru

Python 3.10 backend with Nginx, MariaDB and native HTML/CSS/JavaScript.
Requirements reference: `en.subject.camagru.pdf`, Version 4.1.

## Start

For a new checkout, configure the environment once:

```sh
cp .env.example .env
```

Edit `.env` and replace both example passwords with your own values. If `.env`
already exists, keep it; do not overwrite credentials used by an existing database.
Start Docker Desktop, then run `make up` from this folder.
Open http://localhost:8000. Account-confirmation, reset and comment emails can be
inspected in Mailpit at http://localhost:8025.

Credentials remain in the ignored `.env`; never commit them. `make up` requires this
file and does not generate credentials. No host Python, npm or Composer is required.

## Request flow

Browser → Nginx (`web`) → Python WSGI application (`app`) → MariaDB (`db`).
Nginx serves CSS, JavaScript, overlays and uploaded PNGs directly. Python handles
accounts, gallery queries, comments, likes and server-side image composition.
The app container has no host-published port. Only Nginx is exposed at localhost:8000.

## Small code structure

There are seven application files, using ordinary functions:

- `backend/server.py`: reads HTTP requests and calls the application through WSGI.
- `backend/app.py`: handles registration, login, profile, gallery and editor actions.
- `backend/database.py`: connects to MariaDB and contains parameterized SQL queries.
- `backend/views.py`: creates the HTML pages and escapes displayed values.
- `backend/security.py`: validates fields, hashes passwords and manages sessions.
- `backend/imaging.py`: checks and combines images on the server.
- `backend/mail.py`: sends confirmation, reset and notification emails.

The request information is a dictionary, not a custom Request class. There are no
controller/model classes, inheritance hierarchy or extra subfolders. MVC responsibilities
remain logical: database functions are the model, page-action functions are controllers,
and HTML functions are views. The subject suggests MVC but does not require folder names.

Follow a request: `server.py` → `app.py` → database/security/image/mail functions → `views.py`.

`config/nginx.conf` configures the public web server. `sql/schema.sql` and `sql/seeds.sql`
initialize a new database. There are no source/test bind mounts or migration helpers.
Rebuild after source changes: `make up`. The database health check waits for initialization.

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

`db_data` persists the database. Uploaded photos are saved in `public/uploads` on the host;
the app container can write there and Nginx mounts the same folder read-only.
`public/overlays` is packaged into both images and is not deleted by volume resets.

`make down` keeps data. `make clean`, `make fclean` and `make re` delete the database
volume, but do not delete photos in `public/uploads`. Before switching from the old
`uploads_data` Docker volume, copy its photos into the host folder while the old
containers are still running:

```sh
docker compose cp web:/usr/share/nginx/html/uploads/. ./public/uploads/
```

Application errors return generic responses and are recorded privately in
`/tmp/camagru-errors.log` inside `app`. Nginx errors are recorded in
`/tmp/camagru-nginx-errors.log` inside `web`. Routine access logs are disabled.
Inspect these files and the browser console during evaluation; an empty console alone
does not prove correctness. Real webcam hardware and Firefox compatibility remain to
be verified manually on this host.
