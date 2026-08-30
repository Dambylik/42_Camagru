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
            <input type="hidden" name="image_data"   id="image_data">
            <input type="hidden" name="overlay_id"   id="overlay_id_capture">
            <input type="hidden" name="overlay_x"    id="overlay_x">
            <input type="hidden" name="overlay_y"    id="overlay_y">
            <input type="hidden" name="overlay_w"    id="overlay_w">
            <input type="hidden" name="overlay_h"    id="overlay_h">
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
    const video          = document.getElementById('webcam');
    const canvas         = document.getElementById('canvas-preview');
    const ctx            = canvas.getContext('2d');
    const btnCapture     = document.getElementById('btn-capture');
    const btnRetake      = document.getElementById('btn-retake');
    const captureForm    = document.getElementById('capture-form');
    const imageData      = document.getElementById('image_data');
    const overlayCapture = document.getElementById('overlay_id_capture');
    const thumbs         = document.querySelectorAll('.overlay-thumb');
    const fileInput      = document.getElementById('file-input');

    const SIZE = 600;
    canvas.width  = SIZE;
    canvas.height = SIZE;
    canvas.style.display = 'block';

    let overlayImg    = null;
    let selectedId    = 0;
    let animFrame     = null;
    let frozen        = false;

    // Overlay position/size state (in canvas coords)
    let ov = { x: 100, y: 100, w: 400, h: 400 };

    // Drag state
    const HANDLE = 16; // px — resize handle corner size
    let drag   = null; // 'move' | 'resize'
    let dragOx = 0, dragOy = 0; // offset at drag start

    // ── Draw loop ────────────────────────────────────────────────────────────
    function draw() {
        if (frozen) return;
        ctx.clearRect(0, 0, SIZE, SIZE);
        ctx.drawImage(video, 0, 0, SIZE, SIZE);
        if (overlayImg) {
            ctx.drawImage(overlayImg, ov.x, ov.y, ov.w, ov.h);
            drawHandles();
        }
        animFrame = requestAnimationFrame(draw);
    }

    function drawHandles() {
        // Border
        ctx.strokeStyle = 'rgba(255,255,255,0.8)';
        ctx.lineWidth   = 1.5;
        ctx.setLineDash([5, 4]);
        ctx.strokeRect(ov.x, ov.y, ov.w, ov.h);
        ctx.setLineDash([]);
        // Resize handle (bottom-right)
        ctx.fillStyle = '#fff';
        ctx.fillRect(ov.x + ov.w - HANDLE, ov.y + ov.h - HANDLE, HANDLE, HANDLE);
        ctx.strokeStyle = '#7c3aed';
        ctx.lineWidth = 1;
        ctx.strokeRect(ov.x + ov.w - HANDLE, ov.y + ov.h - HANDLE, HANDLE, HANDLE);
    }

    // ── Canvas coords from mouse/touch event ─────────────────────────────────
    function canvasXY(e) {
        const r   = canvas.getBoundingClientRect();
        const src = e.touches ? e.touches[0] : e;
        return {
            x: (src.clientX - r.left) * (SIZE / r.width),
            y: (src.clientY - r.top)  * (SIZE / r.height)
        };
    }

    function inHandle(x, y) {
        return x >= ov.x + ov.w - HANDLE && x <= ov.x + ov.w
            && y >= ov.y + ov.h - HANDLE && y <= ov.y + ov.h;
    }

    function inOverlay(x, y) {
        return x >= ov.x && x <= ov.x + ov.w
            && y >= ov.y && y <= ov.y + ov.h;
    }

    // ── Pointer events ───────────────────────────────────────────────────────
    function onDown(e) {
        if (!overlayImg || frozen) return;
        e.preventDefault();
        const { x, y } = canvasXY(e);
        if (inHandle(x, y)) {
            drag = 'resize';
        } else if (inOverlay(x, y)) {
            drag   = 'move';
            dragOx = x - ov.x;
            dragOy = y - ov.y;
        }
    }

    function onMove(e) {
        if (!drag || frozen) return;
        e.preventDefault();
        const { x, y } = canvasXY(e);
        if (drag === 'move') {
            ov.x = Math.max(0, Math.min(SIZE - ov.w, x - dragOx));
            ov.y = Math.max(0, Math.min(SIZE - ov.h, y - dragOy));
        } else {
            const minSize = 40;
            ov.w = Math.max(minSize, Math.min(SIZE - ov.x, x - ov.x));
            ov.h = Math.max(minSize, Math.min(SIZE - ov.y, y - ov.y));
        }
        // Update cursor
        canvas.style.cursor = drag === 'resize' ? 'nwse-resize' : 'grabbing';
    }

    function onUp() {
        drag = null;
        canvas.style.cursor = 'default';
    }

    function onHover(e) {
        if (!overlayImg || frozen || drag) return;
        const { x, y } = canvasXY(e);
        if (inHandle(x, y))       canvas.style.cursor = 'nwse-resize';
        else if (inOverlay(x, y)) canvas.style.cursor = 'grab';
        else                      canvas.style.cursor = 'default';
    }

    canvas.addEventListener('mousedown',  onDown);
    canvas.addEventListener('mousemove',  onMove);
    canvas.addEventListener('mousemove',  onHover);
    canvas.addEventListener('mouseup',    onUp);
    canvas.addEventListener('mouseleave', onUp);
    canvas.addEventListener('touchstart', onDown,  { passive: false });
    canvas.addEventListener('touchmove',  onMove,  { passive: false });
    canvas.addEventListener('touchend',   onUp);

    // ── File upload → canvas ─────────────────────────────────────────────────
    let uploadedBase = null; // holds the uploaded Image object

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = e => {
            const img = new Image();
            img.onload = () => {
                // Stop camera
                cancelAnimationFrame(animFrame);
                if (video.srcObject) {
                    video.srcObject.getTracks().forEach(t => t.stop());
                    video.srcObject = null;
                }
                uploadedBase = img;
                frozen = false;
                // Replace draw loop source with the uploaded image
                drawUpload();
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });

    function drawUpload() {
        if (frozen) return;
        ctx.clearRect(0, 0, SIZE, SIZE);
        ctx.drawImage(uploadedBase, 0, 0, SIZE, SIZE);
        if (overlayImg) {
            ctx.drawImage(overlayImg, ov.x, ov.y, ov.w, ov.h);
            drawHandles();
        }
        animFrame = requestAnimationFrame(drawUpload);
    }

    // ── Webcam ───────────────────────────────────────────────────────────────
    <?php if ($previewImage): ?>
    const previewSrc = 'uploads/<?= htmlspecialchars($previewImage) ?>';
    <?php else: ?>
    const previewSrc = null;
    <?php endif ?>

    if (previewSrc) {
        // Show the just-saved result instead of the live camera
        const img = new Image();
        img.onload = () => {
            frozen = true;
            ctx.drawImage(img, 0, 0, SIZE, SIZE);
        };
        img.src = previewSrc;
        btnCapture.style.display = 'none';
        btnRetake.style.display  = 'inline-block';
    } else if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
                video.addEventListener('playing', () => draw());
            })
            .catch(() => {
                document.getElementById('preview-wrap').insertAdjacentHTML(
                    'beforeend',
                    '<p style="color:var(--muted);padding:.5rem">Camera not available — use upload instead.</p>'
                );
            });
    }

    // ── Overlay selection ────────────────────────────────────────────────────
    thumbs.forEach(t => {
        t.addEventListener('click', () => {
            thumbs.forEach(x => x.classList.remove('selected'));
            t.classList.add('selected');
            selectedId           = parseInt(t.dataset.id, 10);
            overlayCapture.value = selectedId;
            btnCapture.disabled  = false;

            const img  = new Image();
            img.src    = t.querySelector('img').src;
            img.onload = () => { overlayImg = img; };

            // Reset overlay to centred default size
            ov = { x: 100, y: 100, w: 400, h: 400 };
        });
    });

    // ── Capture ──────────────────────────────────────────────────────────────
    btnCapture.addEventListener('click', () => {
        if (!selectedId) return;
        cancelAnimationFrame(animFrame);
        frozen = true;

        // Final draw without handles — use uploaded image or webcam
        const source = uploadedBase || video;
        ctx.drawImage(source, 0, 0, SIZE, SIZE);
        if (overlayImg) ctx.drawImage(overlayImg, ov.x, ov.y, ov.w, ov.h);

        imageData.value = canvas.toDataURL('image/png');
        document.getElementById('overlay_x').value = Math.round(ov.x);
        document.getElementById('overlay_y').value = Math.round(ov.y);
        document.getElementById('overlay_w').value = Math.round(ov.w);
        document.getElementById('overlay_h').value = Math.round(ov.h);

        btnCapture.style.display = 'none';
        btnRetake.style.display  = 'inline-block';
        captureForm.submit();
    });

    // ── Retake ───────────────────────────────────────────────────────────────
    btnRetake.addEventListener('click', () => {
        frozen = false;
        uploadedBase = null;
        btnCapture.style.display = 'inline-block';
        btnRetake.style.display  = 'none';
        // Restart camera
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    video.srcObject = stream;
                    video.addEventListener('playing', () => draw(), { once: true });
                });
        }
    });
})();
</script>

<?php require __DIR__ . '/partials/footer.php'; ?>
