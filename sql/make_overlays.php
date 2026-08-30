<?php
// Run once inside the container: docker compose exec web php /var/www/html/sql/make_overlays.php
// Generates simple semi-transparent overlay PNGs for testing.

$dir = __DIR__ . '/../public/overlays/';

$overlays = [
    'sunglasses.png' => function (\GdImage $img): void {
        // Two dark ellipses = sunglasses lenses
        $dark = imagecolorallocatealpha($img, 20, 20, 20, 40);
        $rim  = imagecolorallocatealpha($img, 80, 80, 80, 10);
        imagefilledellipse($img, 210, 270, 160, 90, $dark);
        imagefilledellipse($img, 390, 270, 160, 90, $dark);
        imageellipse($img, 210, 270, 162, 92, $rim);
        imageellipse($img, 390, 270, 162, 92, $rim);
        // Bridge
        imageline($img, 290, 270, 310, 270, $rim);
    },
    'hat.png' => function (\GdImage $img): void {
        // Simple top hat
        $col  = imagecolorallocatealpha($img, 30, 30, 30, 10);
        $brim = imagecolorallocatealpha($img, 20, 20, 20, 10);
        imagefilledrectangle($img, 200, 120, 400, 260, $col);  // crown
        imagefilledrectangle($img, 140, 255, 460, 285, $brim); // brim
    },
    'mustache.png' => function (\GdImage $img): void {
        // Two curved filled ellipses
        $col = imagecolorallocatealpha($img, 40, 25, 10, 20);
        imagefilledellipse($img, 240, 360, 130, 55, $col);
        imagefilledellipse($img, 360, 360, 130, 55, $col);
    },
];

foreach ($overlays as $file => $draw) {
    $img = imagecreatetruecolor(600, 600);
    imagealphablending($img, false);
    imagesavealpha($img, true);
    $transparent = imagecolorallocatealpha($img, 0, 0, 0, 127);
    imagefill($img, 0, 0, $transparent);
    imagealphablending($img, true);

    $draw($img);

    imagesavealpha($img, true);
    imagepng($img, $dir . $file);
    imagedestroy($img);
    echo "Created $file\n";
}
echo "Done.\n";
