<?php $pageTitle = 'Error — Camagru'; require __DIR__ . '/partials/header.php'; ?>

<div class="auth-wrap">
    <div class="alert alert-error"><?= htmlspecialchars($message) ?></div>
    <div class="auth-links">
        <a href="index.php?page=home">← Home</a>
    </div>
</div>

<?php require __DIR__ . '/partials/footer.php'; ?>
