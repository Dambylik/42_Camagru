# 📘 Camagru — Learning Notes

This file explains **how** the project is built, **why** each choice was made,
and the **best practices** for each topic. Read it with the code open next to it.
Each section has the same four parts:

- **What**: the concept in one or two sentences
- **Where**: the files that use it
- **Why this choice**: why we did it this way, and what the alternatives are
- **Best practice**: the habit to keep for your next projects

---

## 0. The big picture: what happens when you open a page

```
Browser ──HTTP──▶ Apache (Docker "web") ──▶ public/index.php   (front controller)
                                              │
                                              ├─ config/setup.php   load .env, secure session
                                              ├─ Router             "GET home" → FeedController::index
                                              ▼
                                         Controller  ──▶ Model (SQL via PDO) ──▶ MariaDB (Docker "db")
                                              │
                                              ▼
                                         View (PHP template → HTML) ──▶ Browser
```

Keep this picture in mind. Every feature follows the same path.

---

## 1. Docker & Docker Compose

- **What:** A *container* runs a program with everything it needs. Compose starts
  several containers together from one file.
- **Where:** `Dockerfile`, `docker-compose.yml`, `Makefile`
- **Why this choice:** The subject asks for a "one command" deploy. There are 3 services:
  - `web`: PHP 8.2 + Apache, plus the `gd` (images) and `pdo_mysql` (database) extensions.
  - `db`: MariaDB. Files in `sql/` run automatically on the **first** boot.
  - `mailpit`: a fake mail server. Every email the app sends shows up at `localhost:8025`,
    so you can test sign-up without a real mail account.
  - Containers find each other by **service name**: PHP connects to host `db`, not `localhost`.
- **Best practice:**
  - Use named volumes (`db_data`) so data survives restarts.
  - Pin major versions (`mariadb:11`, `php:8.2`) so a future update doesn't break you.
  - `make re` resets the DB. The init scripts only run on an empty volume.

## 2. Secrets in `.env`

- **What:** Passwords and config live in a `.env` file that is **never committed**.
- **Where:** `.env.example` (committed template), `.gitignore`, `config/setup.php`, `docker-compose.yml`
- **Why this choice:** The subject says publicly stored credentials mean you fail. Compose
  reads `.env` and passes the values to containers as environment variables. PHP reads
  them with `getenv()`. `docker-compose.yml` has defaults (`${APP_URL:-http://localhost:8000}`)
  so an old `.env` still works.
- **Best practice:** Commit a `.env.example` with fake values. If a secret ever gets
  committed, **change the password**. Deleting the commit isn't enough, because git history keeps it.

## 3. Front controller + Router

- **What:** *Every* request goes through one file, `public/index.php`. It picks which
  code runs based on `?page=...` and the HTTP method.
- **Where:** `public/index.php` (route table), `app/core/Router.php`
- **Why this choice:**
  - There is one place to see all URLs, and one place for setup (session, errors).
  - We use `?page=login` instead of "pretty URLs" (`/login`), so Apache needs no
    `mod_rewrite` config. It's simpler, and it's enough for this project.
  - The route key is `"POST login"`, so GET and POST to the same page go to different methods.
  - Only `public/` is served by Apache (`config/apache.conf`), so `app/`, `config/`, `.env`
    and `sql/` **can't be downloaded** from the browser.
- **Best practice:** Keep the web root minimal. Unknown route → proper 404 page, not a crash.

## 4. MVC (Model – View – Controller)

- **What:** Split code by role.
  - **Model** (`app/models/`): talks to the database, and nothing else.
  - **View** (`app/views/`): HTML templates that only *display* the variables they're given.
  - **Controller** (`app/controllers/`): reads the request, checks rights and input,
    calls models, then picks a view or redirects.
- **Why this choice:** The subject recommends it. When something breaks you know where
  to look: wrong SQL → model, wrong page → view, wrong logic → controller.
- **Best practice:** No SQL in views, no HTML in models. Views share `partials/header.php`
  and `footer.php`, so the layout is written once.

## 5. Database access: PDO + prepared statements

- **What:** PDO is PHP's built-in database layer. A *prepared statement* sends the SQL
  and the values **separately**, so user input can never change the query.
- **Where:** `config/database.php` (connection), every file in `app/models/`
- **Why this choice:**
  ```php
  // ❌ SQL injection: typing  ' OR 1=1 --  logs you in as anyone
  $pdo->query("SELECT * FROM users WHERE username = '$username'");
  // ✅ the ? is filled by the DB driver, the input is only ever data
  $st = $pdo->prepare('SELECT * FROM users WHERE username = ?');
  $st->execute([$username]);
  ```
  Connection options:
  - `ERRMODE_EXCEPTION`: SQL errors throw exceptions instead of failing silently.
  - `EMULATE_PREPARES => false`: real server-side prepares. As a bonus, ints come back as PHP ints.
  - `charset=utf8mb4`: full Unicode, emojis included.
  - **Singleton** (`Database::pdo()`): one connection per request, reused everywhere.
- **Best practice:** **Never** concatenate input into SQL, not even "just an id". If a value
  can't be a `?` (a column name, for example), pick it from a hard-coded whitelist.

## 6. Schema design

- **Where:** `sql/schema.sql`, `sql/seeds.sql`
- **Key ideas:**
  - `users 1──N images 1──N comments`: *one-to-many* uses a foreign key (`user_id`).
  - `likes`: *many-to-many* between users and images. The **composite primary key**
    `(user_id, image_id)` means the database itself makes it impossible to like twice.
  - `FOREIGN KEY ... ON DELETE CASCADE`: deleting an image automatically deletes its
    likes and comments. There are no orphan rows.
  - `UNIQUE` on username and email: duplicates are impossible, even if two sign-ups
    arrive at the exact same millisecond (a *race condition*). The controller checks
    first for a friendly message, and the DB is the final guarantee (the `catch` in `register()`).
  - Index on `images.created_at`: the gallery sorts by this column.
- **Why this choice:** Rules enforced by the DB can't be forgotten by a bug in PHP.
- **Best practice:** "Let the database protect the data." Use InnoDB, since MyISAM ignores foreign keys.

## 7. Passwords

- **What:** Store a **hash**, never the password. `password_hash()` uses bcrypt, which is
  slow on purpose and adds a random *salt*. `password_verify()` checks a login attempt.
- **Where:** `User::create`, `User::updatePassword`, `AuthController::login`
- **Why this choice:** If the DB leaks, attackers still don't have the passwords. Hashing is
  one-way. Encryption is *reversible*, so it's the wrong tool here. MD5/SHA1 are far too fast to be safe.
- **Complexity rule** (`passwordStrong`): at least 8 characters, with an uppercase letter,
  a digit and a special character. It's checked **on the server**. HTML `required` is only a convenience.
- **Best practice:** Never log passwords. Never email them. Changing your password asks
  for the current one (profile).

## 8. Email tokens (confirm account / reset password)

- **What:** A random, unguessable string in a link: `?page=confirm&token=...`
- **Where:** `User::create`, `User::setResetToken`, `findByVerifyToken`, `findByResetToken`
- **Why this choice:**
  - `bin2hex(random_bytes(32))` gives 64 hex characters from a **cryptographically secure**
    source. `rand()` or `uniqid()` can be predicted.
  - **Expiry**: 24h for confirmation, 1h for reset. It's checked in SQL (`expires_at > NOW()`).
  - **Single use**: the token is set to `NULL` once used.
  - Login is blocked until `is_verified = 1`.
- **Best practice:** Tokens must be unguessable, expiring and single-use. "Forgot password"
  always shows the **same message**, whether or not the email exists. Otherwise attackers
  can test which emails have accounts (*user enumeration*). Login does the same:
  "Invalid username or password".

## 9. Sessions & login

- **What:** PHP gives the browser a cookie with a random session ID. On the server,
  `$_SESSION` stores who you are.
- **Where:** `config/setup.php`, `AuthController::login/logout`, `requireLogin()` in controllers
- **Why this choice:**
  - `session_regenerate_id(true)` on login defeats **session fixation**. An attacker who
    planted a session ID before you logged in can't reuse it afterwards.
  - Cookie `HttpOnly`: JavaScript can't read the session cookie, so an XSS bug can't steal it.
  - Cookie `SameSite=Lax`: the browser doesn't send it on POSTs coming from another site.
    That's an extra layer against CSRF (section 10).
  - `requireLogin()` is at the **top** of every protected action. Hiding a link isn't
    protection: anyone can type the URL.
- **Best practice:** Authorization is always on the server. Add the `Secure` cookie flag once you have HTTPS.

## 10. CSRF (Cross-Site Request Forgery)

- **What:** An evil site contains a hidden form that POSTs to *your* site. Your browser
  adds your session cookie automatically, so without protection the action runs as you.
  This is the subject's "extern form to manipulate private data".
- **Where:** `app/core/Csrf.php`, `Csrf::field()` in every form, `Csrf::verify()` at the start of every POST action
- **Why this choice:** This is the **synchronizer token** pattern. A random token lives in the
  session and is copied into each form. The evil site can't read your pages, so it can't
  know the token. `hash_equals()` compares in constant time, which avoids *timing attacks*.
  AJAX requests send the same token (`gallery.php`, `post()` helper).
- **Best practice:** Every request that **changes** something should be a POST with a CSRF
  token. GET must never change data. The one exception here is logout (see "Known limits").

## 11. XSS (Cross-Site Scripting)

- **What:** A user writes `<script>...</script>` in a comment. If you print it raw, it runs
  in every visitor's browser.
- **Where:** every view (`htmlspecialchars`), `gallery.php` JS (`textContent`, `createTextNode`)
- **Why this choice:** The rule is **escape on output**, at the moment you print:
  - In PHP: `<?= htmlspecialchars($c['content']) ?>` turns `<` into `&lt;`, so it displays as text.
  - In JS: `el.textContent = value` (safe), never `el.innerHTML = value` (dangerous).
  - To pass PHP data into a `<script>`: `json_encode()` (see the `CSRF` variable in `gallery.php`).
- **Best practice:** Store what the user typed as-is, and escape according to *where* it's
  printed (HTML, JS, URL). Plain-text emails need **no** HTML escaping, otherwise the user sees `&amp;`.

## 12. Uploads & image handling (server-side compositing)

- **What:** The browser sends the photo plus the sticker positions. **PHP GD** merges them.
- **Where:** `app/views/editor.php` (JS), `EditorController::capture` and `composite`
- **Flow:**
  1. The webcam (`getUserMedia` → `<video>`) or an uploaded file (`FileReader`) is drawn on a `<canvas>`.
  2. Stickers are drawn **on top only for the preview**. You can drag, resize and double-click to remove them.
  3. On capture, JS exports **only the raw photo** (`canvas.toDataURL('image/png')`) and a
     JSON list `[{id, x, y, w, h}]`.
  4. The server checks everything, then uses GD: resize the photo to 600×600, then
     `imagecopyresampled` each overlay PNG with alpha blending, then save it with a random name.
- **Why this choice:**
  - The subject requires server-side superposition. The server only trusts **overlay IDs**
    and looks up the files itself, so a user can't inject their own "overlay".
  - Overlays must be PNGs with an **alpha channel** (transparency). Otherwise you'd get a rectangle over the face.
  - Uploads go through the same canvas → PNG path, so there's one code path to secure.
- **Upload security checklist** (all in `capture()`):
  - The `data:image/png;base64,` prefix is required, and `base64_decode(..., true)` is strict.
  - Size is limited to 5 MB. Dimensions are checked **before** decoding (`getimagesizefromstring`, max 4000px),
    because a tiny file can claim to be 20000×20000 and eat all memory (a "decompression bomb").
  - `imagecreatefromstring` fails on anything that isn't a real image. A `.php` renamed to `.png` is rejected.
  - The saved file is **re-encoded by GD** under a random name (`bin2hex(random_bytes(16)).png`).
    The user never chooses the filename or the extension.
  - Sticker coordinates are clamped to the canvas, since client numbers are untrusted.
  - At least one **valid** overlay is required. The disabled button is UX, and the server check is the rule.
- **Best practice:** Check type by **content**, never by extension or the browser's MIME type.
  Generate filenames yourself. Keep uploads non-executable.

## 13. Authorization: "only my own images"

- **Where:** `EditorController::delete`
- **Why this choice:** The image id comes from a hidden form field, so anyone can change it
  in dev tools. The server loads the image and compares `user_id` with the session. If they
  don't match → 403. The `(int)` casts make the `!==` comparison safe whatever the types are.
- **Best practice:** Never trust an ID sent by the client. Always check ownership again on the server.

## 14. Gallery: pagination, AJAX, infinite scroll

- **Where:** `FeedController`, `Image::paginate`, `app/views/gallery.php`
- **Pagination:** `ORDER BY created_at DESC LIMIT 5 OFFSET (page-1)*5`. Page links work
  **without JavaScript** (a fallback). With JS they're hidden and **infinite scroll** loads
  `?page=gallery-json&p=N` as you reach the bottom.
- **AJAX likes/comments:** these use `XMLHttpRequest` instead of `fetch()`, and `var` instead of `let`.
  - **Why:** the subject requires Firefox ≥ 41 and Chrome ≥ 46. `fetch` only arrived in
    Firefox 39 / Chrome 42 and some later features are missing, so XHR is the safe choice.
- **Robustness:** a like or comment on an image that no longer exists returns a JSON error.
  Without that check, the foreign key rejects the INSERT and PHP crashes with a 500.
  Comment length (500) is checked on the server as well as with `maxlength`.
- **Best practice:** The server must work without the client's help. JS improves the
  experience, and the server enforces the rules.

## 15. Email notifications

- **What:** When someone comments on your image, you get an email, unless you turned it off in your profile.
- **Where:** `FeedController::commentAjax`, `app/core/Mailer.php`, `config/msmtp.conf`
- **Why this choice:** PHP's built-in `mail()` (standard library, as the subject requires)
  calls `sendmail`. In the container, `sendmail` is **msmtp**, which forwards to Mailpit.
  `notify_on_comment DEFAULT 1` in the schema = "true by default" (subject V.3).
  Commenting on your own image doesn't email you.
- **Best practice:** A mail failure is logged and doesn't crash the request. Don't put user
  input into mail **headers** (header injection). Here only validated emails go there.

## 16. Error handling: no leaks, no console noise

- **Where:** `config/setup.php`, `app/views/error.php`, `404.php`
- **Why this choice:**
  - `display_errors = 0`: a stack trace shows file paths, SQL and sometimes passwords to attackers.
  - `set_exception_handler`: any uncaught error → logged (`make logs`) + a polite 500 page.
  - The subject requires **zero** errors/warnings in both consoles, so every array access
    uses `?? default` and there are no undefined variables.
- **Best practice:** Show users a generic message, and give developers the details in the logs.

## 17. Post/Redirect/Get + flash messages

- **What:** After a POST, the controller **redirects** (`header('Location: ...')`) instead
  of printing a page. Messages ("Password updated!") travel in `$_SESSION` for exactly one
  display, then get `unset`. That's a *flash message*.
- **Why this choice:** Refreshing the page won't re-submit the form (no double comment or
  double sign-up), and the URL stays clean.

## 18. Responsive layout

- **Where:** `public/css/app.css`, the `<meta name="viewport">` in `header.php`
- **Why this choice:** Plain CSS with Flexbox and media queries, no framework. The editor
  is laid out as main + side (Figure V.1) and stacks vertically on small screens.
  CSS Grid and `aspect-ratio` are avoided for old-browser compatibility.
- **Best practice:** Test by making the browser window narrow and using dev-tools device mode. Use relative units (`rem`, `%`).

---

## 🔧 What was fixed while finishing the project (and why)

| # | Problem | Fix | Subject rule |
|---|---------|-----|--------------|
| 1 | Capture button was enabled as soon as the camera started | Enabled only when media is ready **and** ≥1 sticker is placed (`updateCaptureBtn()`) | V.4 "inactive as long as no superposable image selected" |
| 2 | The browser drew the stickers into the photo, *then* the server drew them again (stickers doubled, merging done client-side) | JS now sends only the raw photo + positions | V.4 "superposing must be done on the server side" |
| 3 | The server accepted captures with no overlay | Rejected if the list is empty **or** no ID is valid | V.4 + "never trust the client" |
| 4 | Unused `upload` endpoint that saved images without an overlay | Removed (uploads already go through `capture`) | Less code = less attack surface |
| 5 | No dimension check before decoding the image | `getimagesizefromstring` ≤ 4000px, strict base64 | "unwanted content on the server" |
| 6 | Like/comment on a deleted image → uncaught FK error → 500 | Image existence checked first | "no errors in any console" |
| 7 | Comment length only limited in HTML | Server limit of 500 characters | "correct validations" |
| 8 | Errors could be shown to visitors | `display_errors=0` + global exception handler | Security |
| 9 | Session cookie without flags | `HttpOnly` + `SameSite=Lax` | Security (defense in depth) |
| 10 | An old `.env` without `APP_URL` → broken email links | Defaults in `docker-compose.yml` | One-command deploy |

---

## ⚠️ Known limits (good things to discuss at evaluation)

- **Logout is a GET link.** A foreign site could log you out (harmless, but technically CSRF).
  The fix is a small POST form with `Csrf::field()` in the header.
- **Changing your email doesn't ask you to confirm the new address.** A stricter app would
  send a confirmation link to the new address first.
- **No rate limiting on login.** Someone can try many passwords. Real apps block after N failures.
- **`OFFSET` pagination** gets slow with millions of rows. The fix is "keyset" pagination
  (`WHERE id < last_seen_id`). That doesn't matter at this size.
- **The gallery runs one comments query per image** (the "N+1 queries" pattern). With 5 images
  per page that's fine. For bigger pages, load all comments with one `WHERE image_id IN (...)`.

---

## ✅ Self-test before the evaluation

Try to break your own app:

1. `' OR 1=1 --` as username at login → "Invalid username or password".
2. Comment `<script>alert(1)</script>` → it shows as text, and no alert pops up.
3. Save this as `evil.html` on your desktop, open it while logged in, and submit →
   **403 Invalid CSRF token**.
   ```html
   <form method="post" action="http://localhost:8000/index.php?page=profile">
     <input name="action" value="email"><input name="email" value="hacker@evil.com">
     <button>go</button></form>
   ```
4. In dev tools, change the `image_id` hidden field of a delete form to someone else's image → **Forbidden**.
5. Remove `disabled` from the Capture button in dev tools and click it with no sticker → "Pick at least one overlay first."
6. Rename a `.txt` to `.png` and upload it → the browser can't load it, so nothing is sent. If someone bypasses the browser, GD rejects it on the server anyway.
7. Look in the DB (`make db`, then `SELECT password FROM users;`) → only `$2y$...` bcrypt hashes.
8. Open the browser console and `make logs` on every page → clean.
9. `git status` → `.env` never appears.
10. Fresh clone → `make` → everything works.
