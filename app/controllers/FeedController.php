<?php
require_once __DIR__ . '/../models/Image.php';
require_once __DIR__ . '/../models/Comment.php';
require_once __DIR__ . '/../models/User.php';
require_once __DIR__ . '/../core/Mailer.php';

class FeedController
{
    private const PER_PAGE    = 5;
    private const MAX_COMMENT = 500; // same as maxlength="500" in the HTML

    public function index(): void
    {
        $page   = max(1, (int) ($_GET['p'] ?? 1));
        $images = Image::paginate($page, self::PER_PAGE);
        $total  = Image::count();
        $pages  = (int) ceil($total / self::PER_PAGE);

        $userId = $_SESSION['user_id'] ?? null;
        foreach ($images as &$img) {
            $img['comments'] = Comment::byImage($img['id']);
            $img['liked']    = $userId ? Image::hasLiked($userId, $img['id']) : false;
        }
        unset($img);

        $pageTitle = 'Galerrry — Camagrrru';
        require __DIR__ . '/../views/gallery.php';
    }

    public function galleryJson(): void
    {
        header('Content-Type: application/json');
        $page   = max(1, (int) ($_GET['p'] ?? 1));
        $images = Image::paginate($page, self::PER_PAGE);
        $total  = Image::count();
        $pages  = (int) ceil($total / self::PER_PAGE);
        $userId = $_SESSION['user_id'] ?? null;
        foreach ($images as &$img) {
            $img['comments'] = Comment::byImage($img['id']);
            $img['liked']    = $userId ? Image::hasLiked($userId, $img['id']) : false;
            $img['is_owner'] = $userId && (int)$img['user_id'] === (int)$userId;
        }
        unset($img);
        echo json_encode(['images' => $images, 'page' => $page, 'pages' => $pages]);
        exit;
    }

    public function likeAjax(): void
    {
        header('Content-Type: application/json');
        if (empty($_SESSION['user_id'])) {
            echo json_encode(['error' => 'unauthenticated']); exit;
        }
        Csrf::verify();
        $imageId = (int) ($_POST['image_id'] ?? 0);
        // Image may have been deleted meanwhile: without this check the
        // foreign key rejects the INSERT and PHP crashes with a 500.
        if (!Image::findById($imageId)) {
            echo json_encode(['error' => 'not found']); exit;
        }
        Image::toggleLike($_SESSION['user_id'], $imageId);
        echo json_encode([
            'liked' => Image::hasLiked($_SESSION['user_id'], $imageId),
            'count' => Image::likeCount($imageId),
        ]);
        exit;
    }

    public function commentAjax(): void
    {
        header('Content-Type: application/json');
        if (empty($_SESSION['user_id'])) {
            echo json_encode(['error' => 'unauthenticated']); exit;
        }
        Csrf::verify();
        $imageId = (int) ($_POST['image_id'] ?? 0);
        $content = trim($_POST['content'] ?? '');

        // maxlength in HTML is easy to bypass, so the server re-checks it
        if ($content === '' || mb_strlen($content) > self::MAX_COMMENT) {
            echo json_encode(['error' => 'invalid']); exit;
        }
        $image = Image::findById($imageId);
        if (!$image) {
            echo json_encode(['error' => 'not found']); exit;
        }

        Comment::create($imageId, $_SESSION['user_id'], $content);

        // Notify the author (not when commenting on your own image)
        if ((int) $image['user_id'] !== (int) $_SESSION['user_id']) {
            $owner = User::findById($image['user_id']);
            if ($owner && $owner['notify_on_comment']) {
                $url = rtrim(getenv('APP_URL'), '/') . '/index.php?page=home#img-' . $imageId;
                Mailer::send(
                    $owner['email'],
                    'New comment on your Camagrrru image',
                    "Hi {$owner['username']},\n\n"
                    . $_SESSION['username']
                    . " commented on your image:\n\n\"{$content}\"\n\nView it: {$url}"
                );
            }
        }

        echo json_encode([
            'username' => $_SESSION['username'],
            'content'  => $content,
        ]);
        exit;
    }
}
