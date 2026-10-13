# PHP equivalents — subject Version 4.1

The assigned subject permits another backend language when used functionality has a PHP
standard-library equivalent. There is no framework, ORM or template dependency here.
The three external packages supply functionality available in PHP's bundled extensions.
This records our interpretation for review; it cannot guarantee an evaluator's decision.

| Python functionality | PHP equivalent |
| --- | --- |
| PyMySQL connect, execute(sql, parameters), fetchall | PDO connection, parameterized queries, fetchAll |
| commit, rollback, lastrowid, rowcount | PDO commit, rollBack, lastInsertId, rowCount |
| bcrypt hashpw/gensalt/checkpw | password_hash(PASSWORD_BCRYPT), password_verify |
| Pillow open/load, dimensions | GD imagecreatefromstring, getimagesize, imagesx/imagesy |
| RGBA conversion, resize, alpha_composite, PNG save | GD imagecreatetruecolor, imagecopyresampled, alpha blending, imagepng |
| secrets.token_hex / compare_digest | bin2hex(random_bytes()), hash_equals |
| hashlib.sha256 | hash('sha256', ...) |
| html.escape | htmlspecialchars |
| re.compile/fullmatch/search | preg_match with anchors |
| json.loads/dumps | json_decode/json_encode |
| base64.b64decode(validate=True) | base64_decode(..., true) |
| smtplib, EmailMessage | mail() with configured SMTP/sendmail transport |
| SimpleCookie, Set-Cookie | $_COOKIE, setcookie |
| database session lookup/rotation | session_start with custom save handler, session_regenerate_id |
| urlsplit, unquote, parse_qs | parse_url, rawurldecode, parse_str |
| native HTTP request/status/headers | PHP built-in web server, $_SERVER, http_response_code, header |
| mimetypes.guess_type | mime_content_type/finfo |
| pathlib resolve/name/parents/is_file | realpath, basename, dirname, is_file |
| read_bytes/write_bytes/unlink | file_get_contents/file_put_contents/unlink |
| open/context manager/BytesIO | fopen/fclose, memory streams/output buffering |
| os.environ | getenv |
| time.time/monotonic/sleep | time/microtime/hrtime/usleep |
| math.isfinite | is_finite |
| int/str/bool/len/min/max, list/dict/set iteration | casts, strlen/count, min/max, arrays/foreach |
| map/comprehensions/any/isinstance | array_map/foreach, type predicates |
| exceptions, try/except/finally | exceptions, try/catch/finally |
| worker dispatch, bounded semaphore | web-server worker infrastructure; not an application framework |
| traceback and private diagnostic file | exception trace/error_log to a file |

PyMySQL parameterization escapes/binds values through its DB-API interface. It does not
use MariaDB's server-side PREPARE protocol, so do not describe it as PDO native prepares.
No SQL query interpolates user input. Dynamic column names use a fixed internal allowlist.

Primary references:

- https://www.php.net/manual/en/book.pdo.php
- https://www.php.net/manual/en/ref.password.php
- https://www.php.net/manual/en/book.image.php
- https://pymysql.readthedocs.io/en/latest/modules/cursors.html
- https://pillow.readthedocs.io/en/stable/reference/Image.html
- https://pypi.org/project/bcrypt/

Node/Playwright are optional development tools, never loaded by the application.
