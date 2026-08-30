<?php $pageTitle = 'Studio — Camagrrru'; require __DIR__ . '/partials/header.php'; ?>

<?php if (!empty($_SESSION['editor_error'])): ?>
    <div class="alert alert-error"><?= htmlspecialchars($_SESSION['editor_error']) ?></div>
    <?php unset($_SESSION['editor_error']); ?>
<?php endif ?>

<div class="editor-wrap">

    <!-- ── Main: webcam + controls ── -->
    <div class="editor-main">
        <div id="preview-wrap">
            <video id="webcam" autoplay playsinline muted style="display:none"></video>
            <canvas id="canvas-preview"></canvas>
        </div>

        <div style="display:flex;gap:.5rem;flex-wrap:wrap">
            <button class="btn btn-primary" id="btn-capture" disabled>📷 Capture</button>
            <button class="btn btn-ghost"   id="btn-retake"  style="display:none">↩ Retake</button>
        </div>

        <!-- Hidden form submitted by JS after capture -->
        <form id="capture-form" method="post" action="index.php?page=capture" style="display:none">
            <?= Csrf::field() ?>
            <input type="hidden" name="image_data" id="image_data">
            <input type="hidden" name="stickers"   id="stickers_data">
        </form>

        <!-- Upload fallback -->
        <details style="margin-top:.5rem">
            <summary style="cursor:pointer;color:var(--muted);font-size:.9rem">Or upload a photo instead</summary>
            <div style="margin-top:.75rem">
                <input type="file" id="file-input" accept="image/*" style="color:var(--text)">
            </div>
        </details>
    </div>

    <!-- ── Side: overlays + thumbnails ── -->
    <div class="editor-side">

        <div class="card">
            <p style="margin-bottom:.5rem;font-size:.9rem;color:var(--muted)">Pick a cat overlay 🐾</p>
            <?php if (empty($overlays)): ?>
                <p style="color:var(--muted);font-size:.85rem">No overlays yet 😿</p>
            <?php else: ?>
            <div class="overlay-list">
                <?php foreach ($overlays as $ov): ?>
                    <div class="overlay-thumb" data-id="<?= $ov['id'] ?>"
                         title="<?= htmlspecialchars($ov['name']) ?>">
                        <img src="overlays/<?= htmlspecialchars($ov['path']) ?>"
                             alt="<?= htmlspecialchars($ov['name']) ?>">
                    </div>
                <?php endforeach ?>
            </div>
            <?php endif ?>
        </div>

        <?php if (!empty($myImages)): ?>
        <div class="card">
            <p style="margin-bottom:.5rem;font-size:.9rem;color:var(--muted)">Your photos 🐱</p>
            <div class="thumb-grid">
                <?php foreach ($myImages as $img): ?>
                    <div class="thumb-item">
                        <img src="uploads/<?= htmlspecialchars($img['path']) ?>"
                             alt="your image">
                        <form method="post" action="index.php?page=delete-image">
                            <?= Csrf::field() ?>
                            <input type="hidden" name="image_id" value="<?= $img['id'] ?>">
                            <button class="del-btn" type="submit"
                                    onclick="return confirm('Delete this image?')">✕</button>
                        </form>
                    </div>
                <?php endforeach ?>
            </div>
        </div>
        <?php endif ?>

    </div>
</div>

<script>
(function () {
    const video       = document.getElementById('webcam');
    const canvas      = document.getElementById('canvas-preview');
    const ctx         = canvas.getContext('2d');
    const btnCapture  = document.getElementById('btn-capture');
    const btnRetake   = document.getElementById('btn-retake');
    const captureForm = document.getElementById('capture-form');
    const thumbs      = document.querySelectorAll('.overlay-thumb');
    const fileInput   = document.getElementById('file-input');

    const SIZE = 600;
    canvas.width  = SIZE;
    canvas.height = SIZE;
    canvas.style.display = 'block';

    let animFrame    = null;
    let frozen       = false;
    let hasMedia     = false;
    let uploadedBase = null;

    // ── Multiple stickers ────────────────────────────────────────────────────
    // Each sticker: { id, img, x, y, w, h }
    let stickers  = [];   // placed stickers
    let active    = null; // index of sticker being dragged/resized

    const HANDLE = 20;

    function addSticker(id, imgEl) {
        const img = new Image();
        img.src = imgEl.src;
        img.onload = () => {
            stickers.push({ id, img, x: 100, y: 100, w: 400, h: 400 });
        };
    }

    // ── Draw ─────────────────────────────────────────────────────────────────
    function redraw(source) {
        ctx.clearRect(0, 0, SIZE, SIZE);
        ctx.drawImage(source, 0, 0, SIZE, SIZE);
        stickers.forEach((s, i) => {
            ctx.drawImage(s.img, s.x, s.y, s.w, s.h);
            drawHandles(s, i === active);
        });
    }

    function drawHandles(s, isActive) {
        ctx.strokeStyle = isActive ? 'rgba(224,96,126,0.9)' : 'rgba(255,255,255,0.6)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 4]);
        ctx.strokeRect(s.x, s.y, s.w, s.h);
        ctx.setLineDash([]);
        corners(s).forEach(c => {
            ctx.fillStyle = '#fff';
            ctx.fillRect(c.x - HANDLE/2, c.y - HANDLE/2, HANDLE, HANDLE);
            ctx.strokeStyle = '#e0607e';
            ctx.lineWidth = 1.5;
            ctx.strokeRect(c.x - HANDLE/2, c.y - HANDLE/2, HANDLE, HANDLE);
        });
    }

    function loop() {
        if (frozen) return;
        redraw(uploadedBase || video);
        animFrame = requestAnimationFrame(loop);
    }

    // ── Corner helpers ───────────────────────────────────────────────────────
    function corners(s) {
        return [
            { x: s.x,       y: s.y       },
            { x: s.x + s.w, y: s.y       },
            { x: s.x,       y: s.y + s.h },
            { x: s.x + s.w, y: s.y + s.h },
        ];
    }

    function nearCorner(s, x, y) {
        const c = corners(s).reduce((best, c) => {
            const d = Math.hypot(c.x - x, c.y - y);
            return d < best.d ? { c, d } : best;
        }, { c: null, d: Infinity }).c;
        return c && Math.hypot(c.x - x, c.y - y) <= HANDLE ? c : null;
    }

    function inSticker(s, x, y) {
        return x >= s.x && x <= s.x + s.w && y >= s.y && y <= s.y + s.h;
    }

    // ── Canvas coords ────────────────────────────────────────────────────────
    function canvasXY(e) {
        const r = canvas.getBoundingClientRect();
        const src = e.touches ? e.touches[0] : e;
        return {
            x: (src.clientX - r.left) * (SIZE / r.width),
            y: (src.clientY - r.top)  * (SIZE / r.height)
        };
    }

    // ── Drag state ───────────────────────────────────────────────────────────
    let drag = null, dragOx = 0, dragOy = 0, anchorX = 0, anchorY = 0;

    function onDown(e) {
        if (frozen) return;
        e.preventDefault();
        const { x, y } = canvasXY(e);
        // Hit-test in reverse order (topmost sticker first)
        for (let i = stickers.length - 1; i >= 0; i--) {
            const s = stickers[i];
            const c = nearCorner(s, x, y);
            if (c) {
                active = i; drag = 'resize';
                anchorX = c.x === s.x ? s.x + s.w : s.x;
                anchorY = c.y === s.y ? s.y + s.h : s.y;
                return;
            }
            if (inSticker(s, x, y)) {
                active = i; drag = 'move';
                dragOx = x - s.x; dragOy = y - s.y;
                return;
            }
        }
        active = null;
    }

    function onMove(e) {
        if (!drag || frozen) return;
        e.preventDefault();
        const { x, y } = canvasXY(e);
        const s = stickers[active];
        const min = 40;
        if (drag === 'move') {
            s.x = Math.max(0, Math.min(SIZE - s.w, x - dragOx));
            s.y = Math.max(0, Math.min(SIZE - s.h, y - dragOy));
        } else {
            s.x = Math.max(0, Math.min(anchorX - min, Math.min(x, anchorX)));
            s.y = Math.max(0, Math.min(anchorY - min, Math.min(y, anchorY)));
            s.w = Math.max(min, Math.abs(x - anchorX));
            s.h = Math.max(min, Math.abs(y - anchorY));
        }
        canvas.style.cursor = drag === 'resize' ? 'nwse-resize' : 'grabbing';
    }

    function onUp() { drag = null; canvas.style.cursor = 'default'; }

    function onHover(e) {
        if (frozen || drag) return;
        const { x, y } = canvasXY(e);
        for (let i = stickers.length - 1; i >= 0; i--) {
            if (nearCorner(stickers[i], x, y)) { canvas.style.cursor = 'nwse-resize'; return; }
            if (inSticker(stickers[i], x, y))  { canvas.style.cursor = 'grab'; return; }
        }
        canvas.style.cursor = 'default';
    }

    canvas.addEventListener('mousedown',  onDown);
    canvas.addEventListener('mousemove',  onMove);
    canvas.addEventListener('mousemove',  onHover);
    canvas.addEventListener('mouseup',    onUp);
    canvas.addEventListener('mouseleave', onUp);
    canvas.addEventListener('touchstart', onDown, { passive: false });
    canvas.addEventListener('touchmove',  onMove, { passive: false });
    canvas.addEventListener('touchend',   onUp);

    // ── Overlay selection — click adds a new sticker ──────────────────────────
    thumbs.forEach(t => {
        t.addEventListener('click', () => {
            if (!hasMedia) return;
            addSticker(parseInt(t.dataset.id, 10), t.querySelector('img'));
        });
    });

    // ── File upload ───────────────────────────────────────────────────────────
    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = ev => {
            const img = new Image();
            img.onload = () => {
                cancelAnimationFrame(animFrame);
                if (video.srcObject) { video.srcObject.getTracks().forEach(t => t.stop()); video.srcObject = null; }
                uploadedBase = img;
                frozen = false;
                hasMedia = true;
                btnCapture.disabled = false;
                loop();
            };
            img.src = ev.target.result;
        };
        reader.readAsDataURL(file);
    });

    // ── Webcam ────────────────────────────────────────────────────────────────
    <?php if ($previewImage): ?>
    const previewSrc = 'uploads/<?= htmlspecialchars($previewImage) ?>';
    <?php else: ?>
    const previewSrc = null;
    <?php endif ?>

    if (previewSrc) {
        const img = new Image();
        img.onload = () => { frozen = true; ctx.drawImage(img, 0, 0, SIZE, SIZE); };
        img.src = previewSrc;
        btnCapture.style.display = 'none';
        btnRetake.style.display  = 'inline-block';
    } else if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
                video.addEventListener('playing', () => {
                    hasMedia = true;
                    btnCapture.disabled = false;
                    loop();
                });
            })
            .catch(() => {
                document.getElementById('preview-wrap').insertAdjacentHTML(
                    'beforeend',
                    '<p style="color:var(--muted);padding:.5rem">Camera not available — use upload instead.</p>'
                );
            });
    }

    // ── Capture ───────────────────────────────────────────────────────────────
    btnCapture.addEventListener('click', () => {
        cancelAnimationFrame(animFrame);
        frozen = true;
        // Final draw without handles
        ctx.clearRect(0, 0, SIZE, SIZE);
        ctx.drawImage(uploadedBase || video, 0, 0, SIZE, SIZE);
        stickers.forEach(s => ctx.drawImage(s.img, s.x, s.y, s.w, s.h));

        document.getElementById('image_data').value   = canvas.toDataURL('image/png');
        document.getElementById('stickers_data').value = JSON.stringify(
            stickers.map(s => ({ id: s.id, x: Math.round(s.x), y: Math.round(s.y), w: Math.round(s.w), h: Math.round(s.h) }))
        );
        btnCapture.style.display = 'none';
        btnRetake.style.display  = 'inline-block';
        captureForm.submit();
    });

    // ── Retake ────────────────────────────────────────────────────────────────
    btnRetake.addEventListener('click', () => {
        frozen = false; uploadedBase = null; hasMedia = false; stickers = []; active = null;
        btnCapture.disabled = true;
        btnCapture.style.display = 'inline-block';
        btnRetake.style.display  = 'none';
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    video.srcObject = stream;
                    video.addEventListener('playing', function onPlaying() {
                        video.removeEventListener('playing', onPlaying);
                        hasMedia = true; btnCapture.disabled = false; loop();
                    });
                });
        }
    });
})();
</script>

<?php require __DIR__ . '/partials/footer.php'; ?>
