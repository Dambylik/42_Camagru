<?php
require_once __DIR__ . '/../models/Image.php';
require_once __DIR__ . '/../models/Comment.php';
require_once __DIR__ . '/../models/User.php';
require_once __DIR__ . '/../core/Mailer.php';

class FeedController
{
    private const PER_PAGE = 5;

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
        if ($imageId > 0) {
            Image::toggleLike($_SESSION['user_id'], $imageId);
        }
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

        if ($imageId <= 0 || $content === '') {
            echo json_encode(['error' => 'invalid']); exit;
        }

        Comment::create($imageId, $_SESSION['user_id'], $content);

        $image = Image::findById($imageId);
        if ($image && $image['user_id'] !== $_SESSION['user_id']) {
            $owner = User::findById($image['user_id']);
            if ($owner && $owner['notify_on_comment']) {
                $url = rtrim(getenv('APP_URL'), '/') . '/index.php?page=home#img-' . $imageId;
                Mailer::send(
                    $owner['email'],
                    'New comment on your Camagrrru image',
                    "Hi {$owner['username']},\n\n"
                    . htmlspecialchars($_SESSION['username'])
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
