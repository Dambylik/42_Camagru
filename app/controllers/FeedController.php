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

        // Attach comments and liked-by-me flag to each image
        $userId = $_SESSION['user_id'] ?? null;
        foreach ($images as &$img) {
            $img['comments'] = Comment::byImage($img['id']);
            $img['liked']    = $userId ? Image::hasLiked($userId, $img['id']) : false;
        }
        unset($img);

        $pageTitle = 'Gallery — Camagru';
        require __DIR__ . '/../views/gallery.php';
    }

    public function like(): void
    {
        if (empty($_SESSION['user_id'])) {
            header('Location: index.php?page=login');
            exit;
        }
        Csrf::verify();
        $imageId = (int) ($_POST['image_id'] ?? 0);
        if ($imageId > 0) {
            Image::toggleLike($_SESSION['user_id'], $imageId);
        }
        $back = (int) ($_POST['p'] ?? 1);
        header('Location: index.php?page=home&p=' . $back . '#img-' . $imageId);
        exit;
    }

    public function comment(): void
    {
        if (empty($_SESSION['user_id'])) {
            header('Location: index.php?page=login');
            exit;
        }
        Csrf::verify();
        $imageId = (int) ($_POST['image_id'] ?? 0);
        $content = trim($_POST['content'] ?? '');
        $back    = (int) ($_POST['p'] ?? 1);

        if ($imageId > 0 && $content !== '') {
            Comment::create($imageId, $_SESSION['user_id'], $content);

            // Notify image owner if they have notifications on
            $image = Image::findById($imageId);
            if ($image && $image['user_id'] !== $_SESSION['user_id']) {
                $owner = User::findById($image['user_id']);
                if ($owner && $owner['notify_on_comment']) {
                    $url = rtrim(getenv('APP_URL'), '/') . '/index.php?page=home#img-' . $imageId;
                    Mailer::send(
                        $owner['email'],
                        'New comment on your Camagru image',
                        "Hi {$owner['username']},\n\n"
                        . htmlspecialchars($_SESSION['username'])
                        . " commented on your image:\n\n\"{$content}\"\n\nView it: {$url}"
                    );
                }
            }
        }

        header('Location: index.php?page=home&p=' . $back . '#img-' . $imageId);
        exit;
    }
}
