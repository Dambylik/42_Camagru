<?php
// ponytail: smoke test — proves web+db+extensions wired up. Delete once real app exists.
echo "Camagru is running.<br>";
echo "gd: "      . (extension_loaded('gd') ? "yes" : "no") . "<br>";
echo "pdo_mysql: " . (extension_loaded('pdo_mysql') ? "yes" : "no") . "<br>";

try {
    $pdo = new PDO("mysql:host={$_ENV['DB_HOST']};dbname=camagru", $_ENV['DB_USER'], $_ENV['DB_PASSWORD']);
    echo "db: connected";
} catch (Throwable $e) {
    echo "db: " . $e->getMessage();  // likely "connection refused" for a few seconds after start
}
