<?php
// ponytail: stub — smoke test lives here for now. Replace with the real feed view.
require_once __DIR__ . '/../core/Database.php';

class FeedController
{
    public function index(): void
    {
        echo "Camagru is running.<br>";
        echo "gd: "        . (extension_loaded('gd') ? "yes" : "no") . "<br>";
        echo "pdo_mysql: " . (extension_loaded('pdo_mysql') ? "yes" : "no") . "<br>";

        try {
            // Prepared statement, even for a constant — proves the pattern works.
            $stmt = Database::pdo()->prepare('SELECT :n AS test');
            $stmt->execute([':n' => 1]);
            $row = $stmt->fetch();
            echo "db: connected (test query returned {$row['test']})";
        } catch (RuntimeException $e) {
            // Generic message only — the real cause is in the server log.
            echo "db: " . htmlspecialchars($e->getMessage());
        }
    }
}
