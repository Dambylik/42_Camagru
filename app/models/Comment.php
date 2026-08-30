<?php
require_once __DIR__ . '/../core/Database.php';

class Comment
{
    public static function byImage(int $imageId): array
    {
        $st = Database::pdo()->prepare(
            'SELECT c.*, u.username FROM comments c
             JOIN users u ON u.id = c.user_id
             WHERE c.image_id = ?
             ORDER BY c.created_at ASC'
        );
        $st->execute([$imageId]);
        return $st->fetchAll();
    }

    public static function create(int $imageId, int $userId, string $content): void
    {
        $st = Database::pdo()->prepare(
            'INSERT INTO comments (image_id, user_id, content) VALUES (?, ?, ?)'
        );
        $st->execute([$imageId, $userId, $content]);
    }
}
