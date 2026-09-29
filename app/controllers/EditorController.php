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

    // Called when user clicks "Capture".
    // Receives the raw photo (webcam frame or uploaded file, drawn on a canvas
    // and exported as base64 PNG) + the list of stickers with their positions.
    // Uploads also come through here: the browser re-encodes them as PNG, and
    // GD decoding below rejects anything that is not a real image.
    public function capture(): void
    {
        $this->requireLogin();
        Csrf::verify();

        $dataUrl  = $_POST['image_data'] ?? '';
        $stickers = json_decode($_POST['stickers'] ?? '[]', true);
        if (!is_array($stickers)) $stickers = [];

        // Subject V.4: an overlay is mandatory. The disabled button is only UX,
        // this is the real check (never trust the client).
        if (count($stickers) === 0) {
            $this->editorError('Pick at least one overlay first.');
        }

        $prefix = 'data:image/png;base64,';
        if (!str_starts_with($dataUrl, $prefix)) {
            $this->editorError('Invalid image data.');
        }
        $raw = base64_decode(substr($dataUrl, strlen($prefix)), true); // true = strict
        if ($raw === false || strlen($raw) > self::MAX_BYTES) {
            $this->editorError('Invalid or too large image (max 5 MB).');
        }

        // Read width/height BEFORE decoding: a tiny file can claim to be
        // 20000×20000 px and eat all the memory ("decompression bomb").
        $info = @getimagesizefromstring($raw);
        if (!$info || $info[0] > 4000 || $info[1] > 4000) {
            $this->editorError('Image must be a valid picture, max 4000×4000 px.');
        }

        $base = @imagecreatefromstring($raw);
        if (!$base) $this->editorError('Could not decode captured image.');

        $this->composite($base, $stickers);
    }

    public function delete(): void
    {
        $this->requireLogin();
        Csrf::verify();

        $imageId = (int) ($_POST['image_id'] ?? 0);
        $image   = Image::findById($imageId);

        // Ownership check — never trust the client
        if (!$image || (int) $image['user_id'] !== (int) $_SESSION['user_id']) {
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
        $applied = 0;
        if (!empty($stickers)) {
            $allOverlays = Image::allOverlays();
            $overlayMap  = [];
            foreach ($allOverlays as $o) $overlayMap[(int)$o['id']] = $o;

            imagealphablending($out, true);
            foreach ($stickers as $s) {
                if (!is_array($s)) continue;
                // Clamp to the 600×600 canvas: client values are untrusted
                $id  = (int) ($s['id'] ?? 0);
                $ovX = $this->clamp($s['x'] ?? 0,   0, 600);
                $ovY = $this->clamp($s['y'] ?? 0,   0, 600);
                $ovW = $this->clamp($s['w'] ?? 600, 1, 600);
                $ovH = $this->clamp($s['h'] ?? 600, 1, 600);

                if (!isset($overlayMap[$id])) continue;
                $path = __DIR__ . '/../../public/overlays/' . basename($overlayMap[$id]['path']);
                if (!file_exists($path)) continue;
                $over = @imagecreatefrompng($path);
                if (!$over) continue;
                imagecopyresampled($out, $over, $ovX, $ovY, 0, 0, $ovW, $ovH, imagesx($over), imagesy($over));
                imagedestroy($over);
                $applied++;
            }
        }

        // All sticker ids were fake/unknown -> no overlay -> refuse (subject V.4)
        if ($applied === 0) {
            imagedestroy($out);
            $this->editorError('Pick at least one valid overlay.');
        }

        $filename = bin2hex(random_bytes(16)) . '.png';
        $savePath = self::UPLOAD_DIR . $filename;
        if (!is_dir(self::UPLOAD_DIR) || !is_writable(self::UPLOAD_DIR)) {
            imagedestroy($out);
            $this->editorError('Upload directory is not writable.');
        }
        imagesavealpha($out, true);
        if (!imagepng($out, $savePath)) {
            imagedestroy($out);
            $this->editorError('Could not save the image.');
        }
        imagedestroy($out);

        Image::create($_SESSION['user_id'], $filename);
        $_SESSION['editor_preview'] = $filename;

        header('Location: index.php?page=editor');
        exit;
    }

    private function clamp(mixed $v, int $min, int $max): int
    {
        return max($min, min($max, (int) $v));
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
