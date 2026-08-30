<?php require __DIR__ . '/partials/header.php'; ?>

<h1 style="margin-bottom:1.5rem">🐱 Galerrry</h1>

<?php if (empty($images)): ?>
    <p style="color:var(--muted)">No photos yet. <a href="index.php?page=editor">Be the first to post! 🐾</a></p>
<?php else: ?>

<div class="gallery-grid">
<?php foreach ($images as $img): ?>
    <div class="gallery-card" id="img-<?= $img['id'] ?>">
        <img src="uploads/<?= htmlspecialchars($img['path']) ?>"
             alt="Image by <?= htmlspecialchars($img['username']) ?>">

        <div class="meta">
            <span><?= htmlspecialchars($img['username']) ?></span>

            <?php if (!empty($_SESSION['user_id'])): ?>
                <form method="post" action="index.php?page=like">
                    <?= Csrf::field() ?>
                    <input type="hidden" name="image_id" value="<?= $img['id'] ?>">
                    <input type="hidden" name="p" value="<?= $page ?>">
                    <button class="like-btn <?= $img['liked'] ? 'liked' : '' ?>" type="submit">
                        💞 <?= $img['like_count'] ?>
                    </button>
                </form>
            <?php else: ?>
                <span>💞 <?= $img['like_count'] ?></span>
            <?php endif ?>
        </div>

        <div class="comments">
            <?php foreach ($img['comments'] as $c): ?>
                <div class="comment">
                    <span class="author"><?= htmlspecialchars($c['username']) ?></span>
                    <?= htmlspecialchars($c['content']) ?>
                </div>
            <?php endforeach ?>

            <?php if (!empty($_SESSION['user_id'])): ?>
                <form class="comment-form" method="post" action="index.php?page=comment">
                    <?= Csrf::field() ?>
                    <input type="hidden" name="image_id" value="<?= $img['id'] ?>">
                    <input type="hidden" name="p" value="<?= $page ?>">
                    <input type="text" name="content" placeholder="Say something nice... 🐱" maxlength="500" required>
                    <button class="btn btn-ghost" type="submit">Post</button>
                </form>
            <?php endif ?>
        </div>
    </div>
<?php endforeach ?>
</div>

<?php if ($pages > 1): ?>
<div class="pagination">
    <?php if ($page > 1): ?>
        <a href="index.php?page=home&p=<?= $page - 1 ?>">‹ Prev</a>
    <?php endif ?>
    <?php for ($i = 1; $i <= $pages; $i++): ?>
        <?php if ($i === $page): ?>
            <span class="current"><?= $i ?></span>
        <?php else: ?>
            <a href="index.php?page=home&p=<?= $i ?>"><?= $i ?></a>
        <?php endif ?>
    <?php endfor ?>
    <?php if ($page < $pages): ?>
        <a href="index.php?page=home&p=<?= $page + 1 ?>">Next ›</a>
    <?php endif ?>
</div>
<?php endif ?>

<?php endif ?>

<?php require __DIR__ . '/partials/footer.php'; ?>
