<?php
require_once __DIR__ . '/../models/Image.php';
require_once __DIR__ . '/../models/User.php';

class EditorController
{
    private const UPLOAD_DIR = __DIR__ . '/../../public/uploads/';
    private const MAX_BYTES  = 5 * 1024 * 1024; // 5 MB

    public function show(): void
    {
        $this->requireLogin();
        $overlays      = Image::allOverlays();
        $myImages      = Image::byUser($_SESSION['user_id']);
        $previewImage  = $_SESSION['editor_preview'] ?? null;
        unset($_SESSION['editor_preview']);
        $pageTitle     = 'Editor — Camagru';
        require __DIR__ . '/../views/editor.php';
    }

    // Called when user clicks "Capture" — receives base64 PNG from canvas
    public function capture(): void
    {
        $this->requireLogin();
        Csrf::verify();

        $dataUrl  = $_POST['image_data'] ?? '';
        $stickers = json_decode($_POST['stickers'] ?? '[]', true);
        if (!is_array($stickers)) $stickers = [];

        if (!preg_match('/^data:image\/png;base64,/', $dataUrl)) {
            $this->editorError('Invalid image data.');
        }
        $raw  = base64_decode(substr($dataUrl, strpos($dataUrl, ',') + 1));
        $base = @imagecreatefromstring($raw);
        if (!$base) $this->editorError('Could not decode captured image.');

        $this->composite($base, $stickers);
    }

    // Called when user uploads a file instead of using webcam
    public function upload(): void
    {
        $this->requireLogin();
        Csrf::verify();

        $file = $_FILES['photo'] ?? null;
        if (!$file || $file['error'] !== UPLOAD_ERR_OK) $this->editorError('Upload failed.');
        if ($file['size'] > self::MAX_BYTES) $this->editorError('File too large (max 5 MB).');

        $info = @getimagesize($file['tmp_name']);
        if (!$info || !in_array($info['mime'], ['image/jpeg', 'image/png', 'image/gif', 'image/webp'], true)) {
            $this->editorError('Only JPEG, PNG, GIF or WebP images are accepted.');
        }

        $base = @imagecreatefromstring(file_get_contents($file['tmp_name']));
        if (!$base) $this->editorError('Could not read uploaded image.');

        $this->composite($base, []);
    }

    public function delete(): void
    {
        $this->requireLogin();
        Csrf::verify();

        $imageId = (int) ($_POST['image_id'] ?? 0);
        $image   = Image::findById($imageId);

        // Ownership check — never trust the client
        if (!$image || $image['user_id'] !== $_SESSION['user_id']) {
            http_response_code(403);
            exit('Forbidden.');
        }

        $path = Image::delete($imageId);
        if ($path) {
            $file = self::UPLOAD_DIR . basename($path);
            if (file_exists($file)) {
                unlink($file);
            }
        }

        header('Location: index.php?page=editor');
        exit;
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private function composite(\GdImage $base, array $stickers): void
    {
        // Resize base to 600×600
        $out = imagecreatetruecolor(600, 600);
        imagecopyresampled($out, $base, 0, 0, 0, 0, 600, 600, imagesx($base), imagesy($base));
        imagedestroy($base);

        // Composite each sticker in order
        if (!empty($stickers)) {
            $allOverlays = Image::allOverlays();
            $overlayMap  = [];
            foreach ($allOverlays as $o) $overlayMap[(int)$o['id']] = $o;

            imagealphablending($out, true);
            foreach ($stickers as $s) {
                $id  = (int) ($s['id'] ?? 0);
                $ovX = (int) ($s['x']  ?? 0);
                $ovY = (int) ($s['y']  ?? 0);
                $ovW = (int) ($s['w']  ?? 600);
                $ovH = (int) ($s['h']  ?? 600);

                if (!isset($overlayMap[$id])) continue;
                $path = __DIR__ . '/../../public/overlays/' . basename($overlayMap[$id]['path']);
                if (!file_exists($path)) continue;
                $over = @imagecreatefrompng($path);
                if (!$over) continue;
                imagecopyresampled($out, $over, $ovX, $ovY, 0, 0, $ovW, $ovH, imagesx($over), imagesy($over));
                imagedestroy($over);
            }
        }

        $filename = bin2hex(random_bytes(16)) . '.png';
        $savePath = self::UPLOAD_DIR . $filename;
        imagesavealpha($out, true);
        imagepng($out, $savePath);
        imagedestroy($out);

        Image::create($_SESSION['user_id'], $filename);
        $_SESSION['editor_preview'] = $filename;

        header('Location: index.php?page=editor');
        exit;
    }

    private function requireLogin(): void
    {
        if (empty($_SESSION['user_id'])) {
            header('Location: index.php?page=login');
            exit;
        }
    }

    private function editorError(string $msg): never
    {
        $_SESSION['editor_error'] = $msg;
        header('Location: index.php?page=editor');
        exit;
    }
}
