# Camagru — Study and Evaluation Plan

Current stack: **Python 3.10 + Nginx + MariaDB + Mailpit + native HTML/CSS/JavaScript + Docker Compose**.
Requirements reference: `en.subject.camagru.pdf`, **Version 4.1**. The 2018
`og_web_camagru.pdf` is useful for practice, but its PHP-specific rules must not
replace the assigned subject.

This is a learning plan for the existing application, not an instruction to rebuild
it from scratch. Read one small part, explain it in your own words, then demonstrate it.
A feature being implemented does not mean you can already explain it or that it has
passed every evaluation check.

- **Read:** the actual files to inspect.
- **Understand:** the concept behind the code.
- **Demonstrate:** a behavior or piece of evidence to show an evaluator.
- **Question:** a self-check before moving on.

## Where we are now

We have discussed Makefile commands, images/containers, Compose services, build
contexts, ports, volumes, database initialization, health checks and startup files.
Revisit them when needed; do not treat discussion alone as proof of mastery.

**Resume at Phase 2:** Python server startup and one request through WSGI.
Explain what happens before studying registration or other application features.

## Architecture map

### Starting the application

```text
Docker Desktop provides the Docker Engine
    ↓
make up → Makefile → docker compose up --build -d
    ↓
docker-compose.yml
    ├── db: MariaDB image → initializes an empty database → health check succeeds
    ├── mailpit: Mailpit image → starts the email receiver
    ├── app: root Dockerfile → docker-entrypoint.sh → python -m backend.server
    └── web: config/nginx.Dockerfile → starts Nginx using config/nginx.conf
```

`app` waits for a healthy database and a started Mailpit container. `web` depends on
`app` being started; that dependency is not an application-readiness health check.

### Handling a request

```text
Browser → localhost:8000 → Nginx in web:80
    ├── CSS / JavaScript / allowed images → served directly by Nginx
    └── /?page=... → Python in app:8000
                         ↓
                     server.py
                         ↓
                       app.py
                         ↓
           database / security / imaging / mail functions
                         ↓
                     views.py → response → Nginx → browser
```

### Seven main Python files

| File | Responsibility |
| --- | --- |
| `backend/server.py` | WSGI server, HTTP parsing, request-size/rate checks, response delivery |
| `backend/app.py` | Page actions, routing, authentication checks, transaction coordination |
| `backend/database.py` | MariaDB connection and parameterized SQL functions |
| `backend/views.py` | Shared layout, forms and HTML rendering with escaping |
| `backend/security.py` | Input validation, bcrypt passwords, sessions and random tokens |
| `backend/imaging.py` | Image decoding, validation and server-side overlay composition |
| `backend/mail.py` | SMTP confirmation, reset and comment-notification emails |

MVC is a separation of responsibilities here, not a collection of classes/folders:
**model = database functions; controller = app actions; view = HTML functions**.
There is no PHP entry point, custom Request class or controller inheritance hierarchy.

## Phase 1 — Launch and configuration

### 1.1 Makefile and Compose

- **Read:** `Makefile`, `docker-compose.yml`.
- **Understand:** `make up` is a shortcut; Compose defines the four services. `build`
  builds custom images, while `image` selects existing images. `context: .` makes
  project files available during image construction.
- **Demonstrate:** run `make up`, then `docker compose ps`; identify each service.
- **Question:** which service runs Python, and which receives the browser's request?

### 1.2 Environment and secrets

- **Read:** `.env.example`, `.gitignore`, Compose's `environment` sections.
- **Understand:** configure `.env` manually once. Compose supplies environment values
  to containers; Python reads them with `os.environ`. There is no `.env` generator.
  SMTP host/port are currently configured in Compose as `mailpit:1025`.
- **Demonstrate:** use `git check-ignore .env`; explain the settings without displaying passwords.
- **Question:** why must changing the application code not expose database credentials?

For a new checkout only, copy `.env.example` to `.env` and replace its example passwords
before `make up`. Preserve an existing `.env` rather than overwriting database credentials.

### 1.3 Dockerfiles and startup script

- **Read:** `Dockerfile`, `config/nginx.Dockerfile`, `config/docker-entrypoint.sh`.
- **Understand:** `FROM`, `WORKDIR`, `COPY`, `RUN`, `ENV`, `EXPOSE`, `ENTRYPOINT`;
  image-build instructions versus container startup. The entrypoint prepares uploads
  permissions and starts Python as the `camagru` user.
- **Demonstrate:** trace `ENTRYPOINT` to `python -m backend.server`.
- **Question:** does `COPY` run when a browser requests a page?

### 1.4 Ports, volumes and startup order

- **Read:** Compose's `ports`, `volumes`, `depends_on` and database health check.
- **Understand:** host port 8000 maps to Nginx port 80. Python port 8000 and MariaDB
  port 3306 are internal. Mailpit's viewer is at localhost:8025; SMTP uses internal
  port 1025. Services reach each other by name, not their own `localhost`.
- **Demonstrate:** list uploads with `docker compose exec web ls -lah /usr/share/nginx/html/uploads`.
- **Question:** why does Python mount uploads writable while Nginx mounts them read-only?

`db_data` stores database files. `uploads_data` stores photos. Docker Desktop manages
named volumes inside its Linux VM. Ordinary restarts keep data. `make clean`,
`make fclean` and `make re` delete persistent data; they are reset commands.

## Phase 2 — From Nginx to Python

### 2.1 Nginx routing

- **Read:** `config/nginx.conf`.
- **Understand:** `listen`, `root`, `location`, `try_files`, `proxy_pass` and security
  headers. Nginx serves allowed assets directly and forwards `/` with its query
  string to `app:8000`. Other paths are rejected.
- **Demonstrate:** trace `/css/app.css` and `/?page=login` separately.
- **Question:** why does Nginx need Python for login, but not for CSS?

### 2.2 WSGI and request parsing

- **Read:** `backend/server.py`, beginning with its final `make_server(...)` line.
- **Understand:** the WSGI server creates `environ` from each incoming request and
  calls `application(environ, start_response)`. `parameters()` parses encoded fields;
  `dispatch(environ)` checks the method/body and passes request information to `app.handle()`.
- **Demonstrate:** explain GET versus POST, `QUERY_STRING`, `wsgi.input`, and the
  returned status/headers/body. Explain why the body must be bytes.
- **Question:** is `environ` created once at startup or separately for each request?

The request limiter currently allows 120 POST requests per IP in a 15-minute window.
Its counters are held in memory and reset when the Python process restarts.

### 2.3 Application routing and request state

- **Read:** `backend/app.py`: `handle()`, `dispatch()`, then `show()` and `login()`.
- **Understand:** `handle()` opens a connection, loads the session, builds a plain
  request dictionary, routes the request and commits/rolls back database work.
  `dispatch(request)` chooses an action using the method and `page` parameter.
- **Demonstrate:** trace `/?page=login` from Nginx through to the rendered form.
- **Question:** what is the difference between the two functions named `dispatch`?

There is no `index.php`: `server.py` is the HTTP/WSGI interface and `app.py` coordinates
application actions. Editing Python, CSS or JavaScript requires rebuilding with
`make up`, because this setup has no source bind mounts.

## Phase 3 — Database fundamentals

### 3.1 Schema and initial data

- **Read:** `sql/schema.sql`, `sql/seeds.sql` and their Compose mounts.
- **Understand:** tables `users`, `overlays`, `images`, `comments`, `likes`, `sessions`;
  primary/foreign keys, uniqueness, indexes, `VARCHAR`, `NOT NULL` and timestamps.
  Overlay files live in `public/overlays`; SQL stores their names and filenames.
- **Demonstrate:** open `make db`, use `SHOW TABLES;` and `DESCRIBE users;`.
- **Question:** why must schema creation run before seed inserts?

MariaDB executes the initialization files only for an empty data directory. Editing
these files does not update an existing database. Do not erase real data merely to
study initialization.

### 3.2 Parameterized queries and exceptions

- **Read:** `backend/database.py`: `connect()`, `fetch_all()`, `fetch_one()`, `execute()` and `users_find_by()`.
- **Understand:** PyMySQL's role versus MariaDB; `%s` placeholders and separate values;
  transaction commit/rollback and database exceptions. Dynamic column names are
  restricted to an internal allowlist.
- **Demonstrate:** point to a query and identify its SQL and supplied values.
- **Question:** why should a submitted email be treated as data rather than SQL?

PyMySQL's parameterized DB-API queries are not MariaDB's server-side PREPARE protocol.
Do not claim that this Python application uses PDO or `PDO::ERRMODE_EXCEPTION`.

## Phase 4 — Accounts and private actions (V.2)

Study one action at a time in `app.py`, then follow its database, security and view calls.

- [ ] **Registration:** `register()`, `security.check_*()`, `password_hash()`, `users_create()`.
  Demonstrate invalid fields, a weak password and duplicates being rejected. Browser
  validation helps users; server validation still runs when the browser is bypassed.
- [ ] **Confirmation:** `secrets.token_hex(32)`, `mail.send_link()`, `confirm()`.
  Demonstrate login blocked before confirmation, a 24-hour expiry and single-use token.
  Email confirmation proves access to the mailbox, not that the user is human.
- [ ] **Login:** `login()`, bcrypt comparison, session rotation.
  Demonstrate confirmed login and rejection of incorrect credentials.
- [ ] **Logout:** `logout()`, a POST form with CSRF token, session rotation.
  Demonstrate logout and subsequent rejection/redirect on protected pages.
- [ ] **Reset:** `forgot()`, `reset()`, `change_password()`.
  Demonstrate actual reset-email delivery, one-hour expiry, strong new password,
  old password rejection, token consumption and older-session invalidation.
- [ ] **Preferences:** `profile()`, `confirm_email()`.
  Demonstrate username uniqueness, current-password checks, new-email confirmation,
  password changes and notification preference. Security changes revoke older sessions.

**Questions:** what does the browser store in its cookie? Where is session data kept?
Why compare the logged-in user ID rather than trust a user ID in submitted form data?

## Phase 5 — Frontend and layout (V.1)

- **Read:** `views.layout()`, `views.heading()`, form/page renderers and `public/css/app.css`.
- **Understand:** shared navigation/main/footer, escaped dynamic values, input types,
  labels, password hints, focus styles, viewport and responsive Flexbox.
- **Demonstrate:** login, registration, confirmation, reset, gallery, profile and
  Studio at desktop and phone widths. Check spacing, image size, overflow and keyboard access.
- **Question:** what is shared between pages, and what is specific to one page?

Keep the cream/blush cat-lover style coherent. Form illustrations have explicit small
sizes. Studio needs more workspace than a form but uses the same heading/card styling.

## Phase 6 — Editor and image processing (V.4)

- [ ] Trace `app.editor()` → overlay/photo queries → `views.editor()` → `public/js/editor.js`.
- [ ] Explain webcam permission, video, canvas, native DOM events and base-image readiness.
- [ ] Demonstrate the upload alternative when no camera is available.
- [ ] Show capture disabled until media and at least one overlay are ready; explain
  the independent server-side check. V.4 requires an overlay; the old checklist conflicts here.
- [ ] Explain how JavaScript sends the raw base PNG plus sticker IDs/positions, not
  merely an already-combined final image.
- [ ] Read `imaging.compose()`: strict base64, PNG decoding, 5 MB bound, dimension
  bounds, sticker validation, resizing and alpha composition with Pillow.
- [ ] Explain browser-side PNG conversion: this implementation does not use PHP
  `$_FILES` or a multipart upload handler. A submitted MIME label alone is not trusted.
- [ ] Demonstrate saved server-composed pixels, random PNG filename, database record,
  previous-photo thumbnails and deletion of both metadata and file.
- [ ] Explain `app.delete()` ownership check; demonstrate another user's image cannot be deleted.

**Question:** which processing is only a browser preview, and which produces the saved file?

## Phase 7 — Gallery and interaction (V.3)

- [ ] Read `app.gallery()` and the corresponding database/view functions.
- [ ] Explain newest-first order, stable ID tie-break, five-image pages, LIMIT/OFFSET.
- [ ] Demonstrate public browsing and multiple pages with enough images.
- [ ] Read `interaction()` and `public/js/gallery.js`; explain like toggle, comments,
  authentication, CSRF and AJAX/JSON responses.
- [ ] Demonstrate a comment containing HTML displayed as text, including dynamically added comments.
- [ ] Demonstrate real notification email delivery with preference enabled and no
  delivery with it disabled. New accounts default to enabled; self-comments are also covered.

**Question:** why are authorization and HTML escaping still needed when buttons are hidden from guests?

## Phase 8 — Explain the mandatory security protections

| Subject concern | Code to explain | Evidence to demonstrate |
| --- | --- | --- |
| Plaintext passwords | bcrypt functions in `security.py` | Stored hash differs from password; correct password verifies |
| Injected HTML/JavaScript | `views.e()`, native DOM text nodes | Comment payload displays as text without executing |
| Unwanted uploads | `imaging.compose()`, safe filenames, Nginx allowlist | Invalid image rejected; saved content is a newly encoded PNG |
| Altered SQL queries | Parameterized functions in `database.py` | Injection input cannot change query logic or authenticate |
| External form manipulation | CSRF/Origin checks in `app.dispatch()` | Missing/wrong token and hostile Origin rejected |
| Access to private actions | Login/session and image-owner checks | Anonymous editor blocked; another owner's deletion rejected |

Explain HttpOnly/SameSite cookies, conditional Secure flag under HTTPS, session-version
revocation, secret configuration and private error reporting. These are runtime protections,
not development scaffolding. No collection of checks proves absence of every security flaw.

## Phase 9 — Evaluation readiness

- [ ] Start using a configured `.env` and one `make up` command.
- [ ] Demonstrate schema/overlay initialization with disposable data rather than wiping real volumes.
- [ ] Exercise signup → confirmation → login → editor → gallery → comment → preferences → logout.
- [ ] Check browser Console and Network with extensions disabled; identify HTTP status codes.
- [ ] Check `make logs` and private diagnostic files:
  `/tmp/camagru-errors.log` inside `app`, `/tmp/camagru-nginx-errors.log` inside `web`.
- [ ] Understand ordinary form-validation messages versus unexpected application failures.
  Suppressing access messages or hiding errors does not prove the application is correct.
- [ ] Verify current Chrome and Firefox. Historical minimum browser versions from
  the subject require separate verification; a current-browser pass does not establish them.
- [ ] Verify actual webcam hardware as well as the upload fallback.
- [ ] Inspect the submitted repository for credentials, obsolete files and missing assets.
- [ ] Review optional bonuses only after mandatory functionality is fully verified.

Earlier verification exercised core flows and Chrome desktop/mobile layouts. Firefox
automation could not launch on this host due to macOS restrictions; Firefox and real
webcam verification remain outstanding. Re-check current behavior during evaluation.
There are no committed test scripts or development source mounts in this architecture.

## Phase 10 — Bonuses already present and optional future work

Present in the code, but still demonstrate them: AJAX likes/comments, live overlay
preview, sticker movement/resizing, and infinite gallery loading with retry behavior.
The gallery uses native XMLHttpRequest and a scroll listener, not a frontend library.
Social sharing and animated GIF generation are not implemented; they are optional ideas,
not tasks needed to finish the mandatory subject.

## PHP-equivalent explanation for the evaluator

The subject permits another server language with functionality equivalent to PHP's
standard library/extensions. Explain the mapping; do not claim evaluator approval is automatic.

| Python functionality | PHP equivalent |
| --- | --- |
| PyMySQL data access/transactions | PDO parameterized queries and transactions |
| bcrypt | password_hash / password_verify |
| Pillow composition | GD image decoding, resizing, alpha blending and PNG output |
| secrets / constant-time comparison | random_bytes / bin2hex / hash_equals |
| HTML escape / regex / JSON / base64 | htmlspecialchars / preg_match / JSON and base64 functions |
| SMTP email | mail with configured transport |
| Cookies and database-backed sessions | setcookie and custom session storage |

Nginx is explicitly allowed as a web server. Python package installation happens while
building its image; it does not introduce an application framework. Old mandatory PHP
filenames and PDO configuration belong to the historical checklist, not this Python layout.

## How to use this plan with a tutor

1. Read the next small code section together.
2. Explain it in your own words; ask for unfamiliar terms before continuing.
3. Answer one question at a time, with hints before solutions when needed.
4. Demonstrate the behavior and identify the exact code responsible.
5. Mark a checkbox only when you can explain and verify it yourself.

Next question: does WSGI `application()` run only at startup, or for each request
that reaches the Python server?
