<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= htmlspecialchars($pageTitle ?? 'Camagrrru') ?></title>
    <link rel="stylesheet" href="css/app.css">
</head>
<body>
<nav>
    <a class="brand" href="index.php?page=home">
        <img src="cat-cartoon.png" alt="" class="brand-logo">
        Camagrrru
    </a>
    <a href="index.php?page=home">Galerrry</a>
    <?php if (!empty($_SESSION['user_id'])): ?>
        <a href="index.php?page=editor">📷 Studio</a>
        <span class="spacer"></span>
        <a href="index.php?page=profile"><?= htmlspecialchars($_SESSION['username']) ?></a>
        <a href="index.php?page=logout">Log out</a>
    <?php else: ?>
        <span class="spacer"></span>
        <a href="index.php?page=login">Log in</a>
        <a href="index.php?page=register">Register</a>
    <?php endif ?>
</nav>
<main>
