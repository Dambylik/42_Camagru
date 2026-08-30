<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= htmlspecialchars($pageTitle ?? 'Camagrrru') ?></title>
    <link rel="stylesheet" href="css/app.css">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🐱</text></svg>">
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
