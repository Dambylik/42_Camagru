<?php $pageTitle = 'Register — Camagrrru'; require __DIR__ . '/partials/header.php'; ?>

<div class="auth-wrap">
    <img src="cat-cartoon.png" alt="Camagrrru" class="auth-logo">
    <h1>🐾 Join Camagrrru</h1>

    <?php if (!empty($error)): ?>
        <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
    <?php endif ?>

    <div class="card">
        <form method="post" action="index.php?page=register">
            <?= Csrf::field() ?>
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" value="<?= htmlspecialchars($old['username'] ?? '') ?>" required>
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" name="email" value="<?= htmlspecialchars($old['email'] ?? '') ?>" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
                <small>Min 8 chars, uppercase, digit, special character.</small>
            </div>
            <button class="btn btn-primary" type="submit">Register</button>
        </form>
    </div>

    <div class="auth-links">
        <a href="index.php?page=login">Already part of the clowder? Log in</a>
    </div>
</div>

<?php require __DIR__ . '/partials/footer.php'; ?>
