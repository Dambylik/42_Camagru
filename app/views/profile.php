<?php $pageTitle = 'Edit profile — Camagrrru'; require __DIR__ . '/partials/header.php'; ?>

<h1 style="margin-bottom:1.5rem">🐾 Edit profile</h1>

<?php if (!empty($success)): ?>
    <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
<?php endif ?>
<?php if (!empty($error)): ?>
    <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
<?php endif ?>

<div class="profile-section card" style="margin-bottom:1rem">
    <h2>Username</h2>
    <form method="post" action="index.php?page=profile">
        <?= Csrf::field() ?>
        <input type="hidden" name="action" value="username">
        <div class="form-group">
            <input type="text" name="username" value="<?= htmlspecialchars($user['username']) ?>" required>
        </div>
        <button class="btn btn-primary" type="submit">Update username</button>
    </form>
</div>

<div class="profile-section card" style="margin-bottom:1rem">
    <h2>Email</h2>
    <form method="post" action="index.php?page=profile">
        <?= Csrf::field() ?>
        <input type="hidden" name="action" value="email">
        <div class="form-group">
            <input type="email" name="email" value="<?= htmlspecialchars($user['email']) ?>" required>
        </div>
        <button class="btn btn-primary" type="submit">Update email</button>
    </form>
</div>

<div class="profile-section card" style="margin-bottom:1rem">
    <h2>Password</h2>
    <form method="post" action="index.php?page=profile">
        <?= Csrf::field() ?>
        <input type="hidden" name="action" value="password">
        <div class="form-group">
            <label>Current password</label>
            <input type="password" name="current_password" required>
        </div>
        <div class="form-group">
            <label>New password</label>
            <input type="password" name="new_password" required>
            <small>Min 8 chars, uppercase, digit, special character.</small>
        </div>
        <button class="btn btn-primary" type="submit">Update password</button>
    </form>
</div>

<div class="profile-section card">
    <h2>Notifications</h2>
    <form method="post" action="index.php?page=profile">
        <?= Csrf::field() ?>
        <input type="hidden" name="action" value="notify">
        <label style="display:flex;align-items:center;gap:.5rem;cursor:pointer">
            <input type="checkbox" name="notify_on_comment" value="1"
                <?= $user['notify_on_comment'] ? 'checked' : '' ?>>
            Email me when someone comments on my image
        </label>
        <br>
        <button class="btn btn-ghost" type="submit">Save preference</button>
    </form>
</div>

<?php require __DIR__ . '/partials/footer.php'; ?>
