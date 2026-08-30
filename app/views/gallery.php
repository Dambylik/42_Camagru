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
                <button class="like-btn <?= $img['liked'] ? 'liked' : '' ?>"
                        data-id="<?= $img['id'] ?>">
                    💞 <span class="like-count"><?= $img['like_count'] ?></span>
                </button>
            <?php else: ?>
                <span>💞 <?= $img['like_count'] ?></span>
            <?php endif ?>
        </div>

        <div class="comments">
            <div class="comment-list">
            <?php foreach ($img['comments'] as $c): ?>
                <div class="comment">
                    <span class="author"><?= htmlspecialchars($c['username']) ?></span>
                    <?= htmlspecialchars($c['content']) ?>
                </div>
            <?php endforeach ?>
            </div>

            <?php if (!empty($_SESSION['user_id'])): ?>
                <form class="comment-form" data-id="<?= $img['id'] ?>">
                    <input type="text" name="content" placeholder="Say something nice... 🐱" maxlength="500" required>
                    <button class="btn btn-ghost" type="submit">Post</button>
                </form>
            <?php endif ?>
        </div>
    </div>
<?php endforeach ?>
</div>

<?php if ($pages > 1): ?>
<div class="pagination" id="pagination">
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

<div id="scroll-sentinel" style="height:1px"></div>
<p id="scroll-loader" style="text-align:center;color:var(--muted);padding:1rem;display:none">🐾 Loading...</p>

<script>
(function () {
    var CSRF    = <?= json_encode(Csrf::generate()) ?>;
    var loggedIn = <?= !empty($_SESSION['user_id']) ? 'true' : 'false' ?>;
    var curPage  = <?= (int)$page ?>;
    var maxPages = <?= (int)$pages ?>;
    var loading  = false;
    var grid     = document.querySelector('.gallery-grid');
    var sentinel = document.getElementById('scroll-sentinel');
    var loader   = document.getElementById('scroll-loader');
    var pagination = document.getElementById('pagination');

    // Hide static pagination — infinite scroll takes over
    if (pagination) pagination.style.display = 'none';

    function post(url, data, cb) {
        data['_csrf_token'] = CSRF;
        var body = Object.keys(data).map(function(k) {
            return encodeURIComponent(k) + '=' + encodeURIComponent(data[k]);
        }).join('&');
        var xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        xhr.onload = function() {
            if (xhr.status === 200) { try { cb(JSON.parse(xhr.responseText)); } catch(e) {} }
        };
        xhr.send(body);
    }

    function get(url, cb) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.onload = function() {
            if (xhr.status === 200) { try { cb(JSON.parse(xhr.responseText)); } catch(e) {} }
        };
        xhr.send();
    }

    // ── Build a card from JSON data ───────────────────────────────────────────
    function buildCard(img) {
        var card = document.createElement('div');
        card.className = 'gallery-card';
        card.id = 'img-' + img.id;

        var image = document.createElement('img');
        image.src = 'uploads/' + img.path;
        image.alt = 'Image by ' + img.username;
        card.appendChild(image);

        var meta = document.createElement('div');
        meta.className = 'meta';
        var uname = document.createElement('span');
        uname.textContent = img.username;
        meta.appendChild(uname);

        if (loggedIn) {
            var btn = document.createElement('button');
            btn.className = 'like-btn' + (img.liked ? ' liked' : '');
            btn.setAttribute('data-id', img.id);
            btn.innerHTML = '💞 <span class="like-count">' + img.like_count + '</span>';
            bindLike(btn);
            meta.appendChild(btn);
        } else {
            var lspan = document.createElement('span');
            lspan.textContent = '💞 ' + img.like_count;
            meta.appendChild(lspan);
        }
        card.appendChild(meta);

        var comments = document.createElement('div');
        comments.className = 'comments';
        var list = document.createElement('div');
        list.className = 'comment-list';
        img.comments.forEach(function(c) {
            list.appendChild(buildComment(c.username, c.content));
        });
        comments.appendChild(list);

        if (loggedIn) {
            var form = document.createElement('form');
            form.className = 'comment-form';
            form.setAttribute('data-id', img.id);
            var input = document.createElement('input');
            input.type = 'text'; input.name = 'content';
            input.placeholder = 'Say something nice... 🐱';
            input.maxLength = 500; input.required = true;
            var submitBtn = document.createElement('button');
            submitBtn.className = 'btn btn-ghost';
            submitBtn.type = 'submit';
            submitBtn.textContent = 'Post';
            form.appendChild(input); form.appendChild(submitBtn);
            bindComment(form);
            comments.appendChild(form);
        }
        card.appendChild(comments);
        return card;
    }

    function buildComment(username, content) {
        var div = document.createElement('div');
        div.className = 'comment';
        var author = document.createElement('span');
        author.className = 'author';
        author.textContent = username;
        div.appendChild(author);
        div.appendChild(document.createTextNode(content));
        return div;
    }

    // ── Bind like ─────────────────────────────────────────────────────────────
    function bindLike(btn) {
        btn.addEventListener('click', function() {
            var id = btn.getAttribute('data-id');
            post('index.php?page=like-ajax', { image_id: id }, function(res) {
                if (res.error) return;
                btn.querySelector('.like-count').textContent = res.count;
                if (res.liked) btn.classList.add('liked');
                else           btn.classList.remove('liked');
            });
        });
    }

    // ── Bind comment ──────────────────────────────────────────────────────────
    function bindComment(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var id      = form.getAttribute('data-id');
            var input   = form.querySelector('input[name=content]');
            var content = input.value.trim();
            if (!content) return;
            post('index.php?page=comment-ajax', { image_id: id, content: content }, function(res) {
                if (res.error) return;
                var list = document.querySelector('#img-' + id + ' .comment-list');
                list.appendChild(buildComment(res.username, res.content));
                input.value = '';
            });
        });
    }

    // ── Bind existing cards ───────────────────────────────────────────────────
    var likeBtns = document.querySelectorAll('.like-btn[data-id]');
    for (var i = 0; i < likeBtns.length; i++) bindLike(likeBtns[i]);
    var commentForms = document.querySelectorAll('.comment-form[data-id]');
    for (var j = 0; j < commentForms.length; j++) bindComment(commentForms[j]);

    // ── Load next page ────────────────────────────────────────────────────────
    function loadNext() {
        if (loading || curPage >= maxPages) return;
        loading = true;
        loader.style.display = 'block';
        get('index.php?page=gallery-json&p=' + (curPage + 1), function(res) {
            curPage  = res.page;
            maxPages = res.pages;
            res.images.forEach(function(img) {
                grid.appendChild(buildCard(img));
            });
            loader.style.display = 'none';
            loading = false;
        });
    }

    // ── Scroll listener ───────────────────────────────────────────────────────
    window.addEventListener('scroll', function() {
        var rect = sentinel.getBoundingClientRect();
        if (rect.top <= window.innerHeight + 200) loadNext();
    });

    // trigger immediately in case first page doesn't fill the viewport
    loadNext();
})();
</script>

<?php require __DIR__ . '/partials/footer.php'; ?>
