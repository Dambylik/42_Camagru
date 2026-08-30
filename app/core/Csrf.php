<?php
class Csrf
{
    private const KEY = '_csrf_token';

    public static function generate(): string
    {
        if (empty($_SESSION[self::KEY])) {
            $_SESSION[self::KEY] = bin2hex(random_bytes(32));
        }
        return $_SESSION[self::KEY];
    }

    public static function verify(): void
    {
        $token = $_POST['_csrf_token'] ?? '';
        if (!hash_equals($_SESSION[self::KEY] ?? '', $token)) {
            http_response_code(403);
            exit('Invalid CSRF token.');
        }
    }

    public static function field(): string
    {
        return '<input type="hidden" name="_csrf_token" value="'
            . htmlspecialchars(self::generate()) . '">';
    }
}
