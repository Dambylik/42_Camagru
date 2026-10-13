
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
            updateCaptureBtn();
        };
    }

    // Subject V.4: capture stays disabled until a camera/photo is ready
    // AND at least one overlay is selected. (The server checks this again.)
    function updateCaptureBtn() {
        btnCapture.disabled = !(hasMedia && stickers.length > 0);
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
    let drag = null, dragOx = 0, dragOy = 0, anchorX = 0, anchorY = 0, resizeLeft = false, resizeTop = false;

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
                resizeLeft = c.x === s.x;
                resizeTop = c.y === s.y;
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
            const edgeX = resizeLeft ? Math.max(0, Math.min(anchorX - min, x))
                                     : Math.min(SIZE, Math.max(anchorX + min, x));
            const edgeY = resizeTop ? Math.max(0, Math.min(anchorY - min, y))
                                    : Math.min(SIZE, Math.max(anchorY + min, y));
            s.x = resizeLeft ? edgeX : anchorX;
            s.y = resizeTop ? edgeY : anchorY;
            s.w = Math.abs(edgeX - anchorX);
            s.h = Math.abs(edgeY - anchorY);
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

    // ── Double-click to remove sticker ───────────────────────────────────────
    function onDblClick(e) {
        if (frozen) return;
        const { x, y } = canvasXY(e);
        for (let i = stickers.length - 1; i >= 0; i--) {
            if (inSticker(stickers[i], x, y)) {
                stickers.splice(i, 1);
                active = null;
                updateCaptureBtn();
                return;
            }
        }
    }

    canvas.addEventListener('dblclick', onDblClick);
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
        if (file.size > 5 * 1024 * 1024 || !/^image\/(png|jpeg|webp)$/.test(file.type)) {
            alert('Choose a PNG, JPEG or WebP image up to 5 MB.'); return;
        }
        const reader = new FileReader();
        reader.onload = ev => {
            const img = new Image();
            img.onerror = () => { alert('Could not read this image.'); };
            img.onload = () => {
                if (img.width > 4000 || img.height > 4000) { alert('Image must be at most 4000 × 4000 pixels.'); return; }
                cancelAnimationFrame(animFrame);
                if (video.srcObject) { video.srcObject.getTracks().forEach(t => t.stop()); video.srcObject = null; }
                uploadedBase = img;
                frozen = false;
                hasMedia = true;
                document.getElementById('camera-placeholder').style.display = 'none';
                updateCaptureBtn();
                loop();
            };
            img.src = ev.target.result;
        };
        reader.readAsDataURL(file);
    });

    // ── Webcam ────────────────────────────────────────────────────────────────
    const previewSrc = document.getElementById("canvas-preview").dataset.preview || null;

    if (previewSrc) {
        document.getElementById('camera-placeholder').style.display = 'none';
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
                document.getElementById('camera-placeholder').style.display = 'none';
                    updateCaptureBtn();
                    loop();
                });
            })
            .catch(() => {
                document.getElementById('preview-wrap').insertAdjacentHTML(
                    'afterend',
                    '<p class="editor-help" role="status">Camera not available — choose a photo below.</p>'
                );
            });
    }

    // ── Capture ───────────────────────────────────────────────────────────────
    btnCapture.addEventListener('click', () => {
        cancelAnimationFrame(animFrame);
        frozen = true;
        // Send ONLY the raw photo. The stickers are sent as positions and the
        // server composites them (subject V.4: superposition is server-side).
        ctx.clearRect(0, 0, SIZE, SIZE);
        ctx.drawImage(uploadedBase || video, 0, 0, SIZE, SIZE);

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
        updateCaptureBtn();
        btnCapture.style.display = 'inline-block';
        btnRetake.style.display  = 'none';
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    video.srcObject = stream;
                    video.addEventListener('playing', function onPlaying() {
                        video.removeEventListener('playing', onPlaying);
                        hasMedia = true;
                document.getElementById('camera-placeholder').style.display = 'none'; updateCaptureBtn(); loop();
                    });
                }).catch(() => { hasMedia = false; updateCaptureBtn(); });
        }
    });
})();
