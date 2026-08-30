<?php $pageTitle = 'Log in — Camagrrru'; require __DIR__ . '/partials/header.php'; ?>

<div class="auth-wrap">
    <img src="cat-cartoon.png" alt="Camagrrru" class="auth-logo">
    <h1>Welcome back</h1>

    <?php if (!empty($success)): ?>
        <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
    <?php endif ?>
    <?php if (!empty($error)): ?>
        <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
    <?php endif ?>

    <div class="card">
        <form method="post" action="index.php?page=login">
            <?= Csrf::field() ?>
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" value="<?= htmlspecialchars($old['username'] ?? '') ?>" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button class="btn btn-primary" type="submit">Log in</button>
        </form>
    </div>

    <div class="auth-links">
        <a href="index.php?page=register">New to Camagrrru? Join the clowder 🐾</a>
        <a href="index.php?page=forgot">Forgot your password?</a>
    </div>
</div>

<?php require __DIR__ . '/partials/footer.php'; ?>
