<?php $pageTitle = 'New password — Camagrrru'; require __DIR__ . '/partials/header.php'; ?>

<div class="auth-wrap">
    <h1>Choose a new password</h1>

    <?php if (!empty($error)): ?>
        <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
    <?php endif ?>

    <div class="card">
        <form method="post" action="index.php?page=reset">
            <?= Csrf::field() ?>
            <input type="hidden" name="token" value="<?= htmlspecialchars($token) ?>">
            <div class="form-group">
                <label>New password</label>
                <input type="password" name="password" required>
                <small>Min 8 chars, uppercase, digit, special character.</small>
            </div>
            <button class="btn btn-primary" type="submit">Set new password</button>
        </form>
    </div>
</div>

<?php require __DIR__ . '/partials/footer.php'; ?>
