<?php
// Single PDO connection, reused across the request. Creds come from env only.
class Database
{
    private static ?PDO $pdo = null;

    public static function pdo(): PDO
    {
        if (self::$pdo !== null) {
            return self::$pdo;
        }

        $host = getenv('DB_HOST') ?: 'db';
        $name = getenv('DB_NAME') ?: 'camagru';
        $user = getenv('DB_USER');
        $pass = getenv('DB_PASSWORD');

        $dsn = "mysql:host={$host};dbname={$name};charset=utf8mb4";

        try {
            self::$pdo = new PDO($dsn, $user, $pass, [
                // Throw on errors instead of returning false — lets us catch and handle.
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                // fetch() returns associative arrays by default.
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                // Real prepared statements (server-side), not PHP-side emulation.
                PDO::ATTR_EMULATE_PREPARES   => false,
            ]);
        } catch (PDOException $e) {
            // Log the real reason server-side; never leak DSN/creds/stack to the user.
            error_log('DB connection failed: ' . $e->getMessage());
            throw new RuntimeException('Database unavailable');
        }

        return self::$pdo;
    }
}
