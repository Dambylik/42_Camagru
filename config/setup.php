<?php
// Load .env file into environment
$env = __DIR__ . '/../.env';
if (file_exists($env)) {
    foreach (file($env, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        if ($line[0] === '#' || !str_contains($line, '=')) continue;
        [$k, $v] = explode('=', $line, 2);
        putenv(trim($k) . '=' . trim($v));
    }
}

// Never show PHP errors/stack traces to visitors (they leak paths & SQL).
// They still go to the server log: `make logs` to read them.
ini_set('display_errors', '0');
ini_set('log_errors', '1');

// Any uncaught exception (DB down, bug...) -> log it + polite 500 page.
set_exception_handler(function (Throwable $e) {
    error_log($e);
    http_response_code(500);
    $message = 'Something went wrong. Please try again later.';
    require __DIR__ . '/../app/views/error.php';
});

// HttpOnly: JavaScript can't read the session cookie (limits XSS damage).
// SameSite=Lax: browser doesn't send it on cross-site POSTs (extra CSRF shield).
session_start([
    'cookie_httponly' => true,
    'cookie_samesite' => 'Lax',
]);
