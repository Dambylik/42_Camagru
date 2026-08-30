<?php
require_once __DIR__ . '/../core/Database.php';

class User
{
    public static function findByEmail(string $email): array|false
    {
        $st = Database::pdo()->prepare('SELECT * FROM users WHERE email = ? LIMIT 1');
        $st->execute([$email]);
        return $st->fetch();
    }

    public static function findByUsername(string $username): array|false
    {
        $st = Database::pdo()->prepare('SELECT * FROM users WHERE username = ? LIMIT 1');
        $st->execute([$username]);
        return $st->fetch();
    }

    public static function create(string $username, string $email, string $password): int
    {
        $hash  = password_hash($password, PASSWORD_BCRYPT);
        $token = bin2hex(random_bytes(32));

        $st = Database::pdo()->prepare(
            'INSERT INTO users (username, email, password, verify_token, verify_expires_at)
             VALUES (?, ?, ?, ?, DATE_ADD(NOW(), INTERVAL 24 HOUR))'
        );
        $st->execute([$username, $email, $hash, $token]);
        return (int) Database::pdo()->lastInsertId();
    }

    public static function getVerifyToken(int $id): string|null
    {
        $st = Database::pdo()->prepare('SELECT verify_token FROM users WHERE id = ?');
        $st->execute([$id]);
        $row = $st->fetch();
        return $row ? $row['verify_token'] : null;
    }

    public static function findByVerifyToken(string $token): array|false
    {
        $st = Database::pdo()->prepare(
            'SELECT * FROM users WHERE verify_token = ? AND verify_expires_at > NOW() LIMIT 1'
        );
        $st->execute([$token]);
        return $st->fetch();
    }

    public static function verifyToken(int $id): void
    {
        $st = Database::pdo()->prepare(
            'UPDATE users SET is_verified = 1, verify_token = NULL, verify_expires_at = NULL WHERE id = ?'
        );
        $st->execute([$id]);
    }

    public static function setResetToken(int $id): string
    {
        $token = bin2hex(random_bytes(32));
        $st = Database::pdo()->prepare(
            'UPDATE users SET reset_token = ?, reset_expires_at = DATE_ADD(NOW(), INTERVAL 1 HOUR) WHERE id = ?'
        );
        $st->execute([$token, $id]);
        return $token;
    }

    public static function findByResetToken(string $token): array|false
    {
        $st = Database::pdo()->prepare(
            'SELECT * FROM users WHERE reset_token = ? AND reset_expires_at > NOW() LIMIT 1'
        );
        $st->execute([$token]);
        return $st->fetch();
    }

    public static function updatePassword(int $id, string $password): void
    {
        $hash = password_hash($password, PASSWORD_BCRYPT);
        $st = Database::pdo()->prepare(
            'UPDATE users SET password = ?, reset_token = NULL, reset_expires_at = NULL WHERE id = ?'
        );
        $st->execute([$hash, $id]);
    }

    public static function findById(int $id): array|false
    {
        $st = Database::pdo()->prepare('SELECT * FROM users WHERE id = ? LIMIT 1');
        $st->execute([$id]);
        return $st->fetch();
    }

    public static function updateUsername(int $id, string $username): void
    {
        $st = Database::pdo()->prepare('UPDATE users SET username = ? WHERE id = ?');
        $st->execute([$username, $id]);
    }

    public static function updateEmail(int $id, string $email): void
    {
        $st = Database::pdo()->prepare('UPDATE users SET email = ? WHERE id = ?');
        $st->execute([$email, $id]);
    }

    public static function updateNotify(int $id, int $val): void
    {
        $st = Database::pdo()->prepare('UPDATE users SET notify_on_comment = ? WHERE id = ?');
        $st->execute([$val, $id]);
    }
}
