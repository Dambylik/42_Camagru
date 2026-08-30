<?php
require_once __DIR__ . '/../core/Database.php';

class Image
{
    // ── Overlays ─────────────────────────────────────────────────────────────

    public static function allOverlays(): array
    {
        return Database::pdo()->query('SELECT * FROM overlays ORDER BY name')->fetchAll();
    }

    // ── Save image ────────────────────────────────────────────────────────────

    public static function create(int $userId, string $path): int
    {
        $st = Database::pdo()->prepare('INSERT INTO images (user_id, path) VALUES (?, ?)');
        $st->execute([$userId, $path]);
        return (int) Database::pdo()->lastInsertId();
    }

    // ── Gallery (all images, paginated) ───────────────────────────────────────

    public static function paginate(int $page, int $perPage = 5): array
    {
        $offset = ($page - 1) * $perPage;
        $st = Database::pdo()->prepare(
            'SELECT i.*, u.username,
                    (SELECT COUNT(*) FROM likes l WHERE l.image_id = i.id) AS like_count,
                    (SELECT COUNT(*) FROM comments c WHERE c.image_id = i.id) AS comment_count
             FROM images i
             JOIN users u ON u.id = i.user_id
             ORDER BY i.created_at DESC
             LIMIT ? OFFSET ?'
        );
        $st->execute([$perPage, $offset]);
        return $st->fetchAll();
    }

    public static function count(): int
    {
        return (int) Database::pdo()->query('SELECT COUNT(*) FROM images')->fetchColumn();
    }

    // ── Single image ──────────────────────────────────────────────────────────

    public static function findById(int $id): array|false
    {
        $st = Database::pdo()->prepare(
            'SELECT i.*, u.username FROM images i JOIN users u ON u.id = i.user_id WHERE i.id = ?'
        );
        $st->execute([$id]);
        return $st->fetch();
    }

    // ── User's own images ─────────────────────────────────────────────────────

    public static function byUser(int $userId): array
    {
        $st = Database::pdo()->prepare(
            'SELECT * FROM images WHERE user_id = ? ORDER BY created_at DESC'
        );
        $st->execute([$userId]);
        return $st->fetchAll();
    }

    // ── Delete (ownership checked in controller) ──────────────────────────────

    public static function delete(int $id): string|false
    {
        $st = Database::pdo()->prepare('SELECT path FROM images WHERE id = ?');
        $st->execute([$id]);
        $row = $st->fetch();
        if (!$row) return false;

        $st = Database::pdo()->prepare('DELETE FROM images WHERE id = ?');
        $st->execute([$id]);
        return $row['path'];
    }

    // ── Likes ─────────────────────────────────────────────────────────────────

    public static function hasLiked(int $userId, int $imageId): bool
    {
        $st = Database::pdo()->prepare('SELECT 1 FROM likes WHERE user_id = ? AND image_id = ?');
        $st->execute([$userId, $imageId]);
        return (bool) $st->fetch();
    }

    public static function toggleLike(int $userId, int $imageId): void
    {
        if (self::hasLiked($userId, $imageId)) {
            $st = Database::pdo()->prepare('DELETE FROM likes WHERE user_id = ? AND image_id = ?');
        } else {
            $st = Database::pdo()->prepare('INSERT INTO likes (user_id, image_id) VALUES (?, ?)');
        }
        $st->execute([$userId, $imageId]);
    }

    public static function likeCount(int $imageId): int
    {
        $st = Database::pdo()->prepare('SELECT COUNT(*) FROM likes WHERE image_id = ?');
        $st->execute([$imageId]);
        return (int) $st->fetchColumn();
    }
}
