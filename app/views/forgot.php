<?php $pageTitle = 'Forgot password — Camagrrru'; require __DIR__ . '/partials/header.php'; ?>

<div class="auth-wrap">
    <h1>Reset your password</h1>

    <?php if (!empty($success)): ?>
        <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
    <?php endif ?>
    <?php if (!empty($error)): ?>
        <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
    <?php endif ?>

    <div class="card">
        <form method="post" action="index.php?page=forgot">
            <?= Csrf::field() ?>
            <div class="form-group">
                <label>Email address</label>
                <input type="email" name="email" required>
            </div>
            <button class="btn btn-primary" type="submit">Send reset link</button>
        </form>
    </div>

    <div class="auth-links">
        <a href="index.php?page=login">Back to login</a>
    </div>
</div>

<?php require __DIR__ . '/partials/footer.php'; ?>
