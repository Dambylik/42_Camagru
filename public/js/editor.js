function startEditor() {
    var video = document.getElementById("webcam");
    var canvas = document.getElementById("canvas-preview");
    var context = canvas.getContext("2d");
    var captureButton = document.getElementById("btn-capture");
    var retakeButton = document.getElementById("btn-retake");
    var captureForm = document.getElementById("capture-form");
    var overlayButtons = document.querySelectorAll(".overlay-thumb");
    var fileInput = document.getElementById("file-input");
    var placeholder = document.getElementById("camera-placeholder");
    var previewWrap = document.getElementById("preview-wrap");

    var CANVAS_SIZE = 600;
    var HANDLE_SIZE = 20;

    canvas.width = CANVAS_SIZE;
    canvas.height = CANVAS_SIZE;
    canvas.style.display = "block";

    var animationFrame = null;
    var isFrozen = false;
    var hasMedia = false;
    var uploadedPhoto = null;
    var stickers = [];
    var activeStickerIndex = null;

    // These variables remember what the user is doing with the mouse or finger.
    var dragMode = null;
    var dragOffsetX = 0;
    var dragOffsetY = 0;
    var resizeAnchorX = 0;
    var resizeAnchorY = 0;
    var resizingFromLeft = false;
    var resizingFromTop = false;

    function addSticker(id, thumbnailImage) {
        var stickerImage = new Image();
        stickerImage.src = thumbnailImage.src;

        stickerImage.onload = function () {
            var sticker = {
                id: id,
                img: stickerImage,
                x: 100,
                y: 100,
                w: 400,
                h: 400,
            };

            stickers.push(sticker);
            updateCaptureButton();
        };
    }

    // Capture is available only when there is a photo and at least one sticker.
    function updateCaptureButton() {
        captureButton.disabled = !(hasMedia && stickers.length > 0);
    }

    function getStickerCorners(sticker) {
        return [
            { x: sticker.x, y: sticker.y },
            { x: sticker.x + sticker.w, y: sticker.y },
            { x: sticker.x, y: sticker.y + sticker.h },
            { x: sticker.x + sticker.w, y: sticker.y + sticker.h },
        ];
    }

    function drawStickerHandles(sticker, isActive) {
        var corners;
        var i;
        var corner;
        var handleX;
        var handleY;

        if (isActive) {
            context.strokeStyle = "rgba(224,96,126,0.9)";
        } else {
            context.strokeStyle = "rgba(255,255,255,0.6)";
        }

        context.lineWidth = 1.5;
        context.setLineDash([5, 4]);
        context.strokeRect(sticker.x, sticker.y, sticker.w, sticker.h);
        context.setLineDash([]);

        corners = getStickerCorners(sticker);
        for (i = 0; i < corners.length; i += 1) {
            corner = corners[i];
            handleX = corner.x - HANDLE_SIZE / 2;
            handleY = corner.y - HANDLE_SIZE / 2;

            context.fillStyle = "#fff";
            context.fillRect(handleX, handleY, HANDLE_SIZE, HANDLE_SIZE);
            context.strokeStyle = "#e0607e";
            context.lineWidth = 1.5;
            context.strokeRect(handleX, handleY, HANDLE_SIZE, HANDLE_SIZE);
        }
    }

    function redraw(source) {
        var i;
        var sticker;

        context.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
        context.drawImage(source, 0, 0, CANVAS_SIZE, CANVAS_SIZE);

        for (i = 0; i < stickers.length; i += 1) {
            sticker = stickers[i];
            context.drawImage(
                sticker.img,
                sticker.x,
                sticker.y,
                sticker.w,
                sticker.h
            );
            drawStickerHandles(sticker, i === activeStickerIndex);
        }
    }

    function drawNextFrame() {
        var source;

        if (isFrozen) {
            return;
        }

        source = uploadedPhoto || video;
        redraw(source);
        animationFrame = requestAnimationFrame(drawNextFrame);
    }

    function findNearbyCorner(sticker, x, y) {
        var corners = getStickerCorners(sticker);
        var closestCorner = null;
        var closestDistance = Infinity;
        var i;
        var corner;
        var distance;

        for (i = 0; i < corners.length; i += 1) {
            corner = corners[i];
            distance = Math.hypot(corner.x - x, corner.y - y);

            if (distance < closestDistance) {
                closestCorner = corner;
                closestDistance = distance;
            }
        }

        if (closestDistance <= HANDLE_SIZE) {
            return closestCorner;
        }

        return null;
    }

    function isPointInsideSticker(sticker, x, y) {
        var isInsideHorizontally = x >= sticker.x && x <= sticker.x + sticker.w;
        var isInsideVertically = y >= sticker.y && y <= sticker.y + sticker.h;

        return isInsideHorizontally && isInsideVertically;
    }

    function getCanvasPosition(event) {
        var canvasBounds = canvas.getBoundingClientRect();
        var pointer;

        if (event.touches) {
            pointer = event.touches[0];
        } else {
            pointer = event;
        }

        return {
            x: (pointer.clientX - canvasBounds.left)
                * (CANVAS_SIZE / canvasBounds.width),
            y: (pointer.clientY - canvasBounds.top)
                * (CANVAS_SIZE / canvasBounds.height),
        };
    }

    function handlePointerDown(event) {
        var position;
        var i;
        var sticker;
        var corner;

        if (isFrozen) {
            return;
        }

        event.preventDefault();
        position = getCanvasPosition(event);

        // Check the front-most sticker first, because it was drawn last.
        for (i = stickers.length - 1; i >= 0; i -= 1) {
            sticker = stickers[i];
            corner = findNearbyCorner(sticker, position.x, position.y);

            if (corner) {
                activeStickerIndex = i;
                dragMode = "resize";
                resizingFromLeft = corner.x === sticker.x;
                resizingFromTop = corner.y === sticker.y;

                if (resizingFromLeft) {
                    resizeAnchorX = sticker.x + sticker.w;
                } else {
                    resizeAnchorX = sticker.x;
                }

                if (resizingFromTop) {
                    resizeAnchorY = sticker.y + sticker.h;
                } else {
                    resizeAnchorY = sticker.y;
                }

                return;
            }

            if (isPointInsideSticker(sticker, position.x, position.y)) {
                activeStickerIndex = i;
                dragMode = "move";
                dragOffsetX = position.x - sticker.x;
                dragOffsetY = position.y - sticker.y;
                return;
            }
        }

        activeStickerIndex = null;
    }

    function handlePointerMove(event) {
        var position;
        var sticker;
        var minimumSize = 40;
        var newLeft;
        var newTop;

        if (!dragMode || isFrozen) {
            return;
        }

        event.preventDefault();
        position = getCanvasPosition(event);
        sticker = stickers[activeStickerIndex];

        if (dragMode === "move") {
            sticker.x = Math.max(
                0,
                Math.min(CANVAS_SIZE - sticker.w, position.x - dragOffsetX)
            );
            sticker.y = Math.max(
                0,
                Math.min(CANVAS_SIZE - sticker.h, position.y - dragOffsetY)
            );
        } else {
            if (resizingFromLeft) {
                newLeft = Math.max(
                    0,
                    Math.min(resizeAnchorX - minimumSize, position.x)
                );
            } else {
                newLeft = Math.min(
                    CANVAS_SIZE,
                    Math.max(resizeAnchorX + minimumSize, position.x)
                );
            }

            if (resizingFromTop) {
                newTop = Math.max(
                    0,
                    Math.min(resizeAnchorY - minimumSize, position.y)
                );
            } else {
                newTop = Math.min(
                    CANVAS_SIZE,
                    Math.max(resizeAnchorY + minimumSize, position.y)
                );
            }

            if (resizingFromLeft) {
                sticker.x = newLeft;
            } else {
                sticker.x = resizeAnchorX;
            }

            if (resizingFromTop) {
                sticker.y = newTop;
            } else {
                sticker.y = resizeAnchorY;
            }

            sticker.w = Math.abs(newLeft - resizeAnchorX);
            sticker.h = Math.abs(newTop - resizeAnchorY);
        }

        if (dragMode === "resize") {
            canvas.style.cursor = "nwse-resize";
        } else {
            canvas.style.cursor = "grabbing";
        }
    }

    function handlePointerUp() {
        dragMode = null;
        canvas.style.cursor = "default";
    }

    function handlePointerHover(event) {
        var position;
        var i;
        var sticker;

        if (isFrozen || dragMode) {
            return;
        }

        position = getCanvasPosition(event);

        for (i = stickers.length - 1; i >= 0; i -= 1) {
            sticker = stickers[i];

            if (findNearbyCorner(sticker, position.x, position.y)) {
                canvas.style.cursor = "nwse-resize";
                return;
            }

            if (isPointInsideSticker(sticker, position.x, position.y)) {
                canvas.style.cursor = "grab";
                return;
            }
        }

        canvas.style.cursor = "default";
    }

    function handleDoubleClick(event) {
        var position;
        var i;

        if (isFrozen) {
            return;
        }

        position = getCanvasPosition(event);

        for (i = stickers.length - 1; i >= 0; i -= 1) {
            if (isPointInsideSticker(stickers[i], position.x, position.y)) {
                stickers.splice(i, 1);
                activeStickerIndex = null;
                updateCaptureButton();
                return;
            }
        }
    }

    function handleOverlayClick(event) {
        var button = event.currentTarget;
        var image = button.querySelector("img");
        var overlayId;

        if (!hasMedia) {
            return;
        }

        overlayId = parseInt(button.dataset.id, 10);
        addSticker(overlayId, image);
    }

    function handleUploadedImageLoad(image) {
        var i;
        var tracks;

        if (image.width > 4000 || image.height > 4000) {
            alert("Image must be at most 4000 × 4000 pixels.");
            return;
        }

        cancelAnimationFrame(animationFrame);

        if (video.srcObject) {
            tracks = video.srcObject.getTracks();
            for (i = 0; i < tracks.length; i += 1) {
                tracks[i].stop();
            }
            video.srcObject = null;
        }

        uploadedPhoto = image;
        isFrozen = false;
        hasMedia = true;
        placeholder.style.display = "none";
        updateCaptureButton();
        drawNextFrame();
    }

    function handleFileSelection() {
        var file = fileInput.files[0];
        var reader;

        if (!file) {
            return;
        }

        if (
            file.size > 5 * 1024 * 1024
            || !/^image\/(png|jpeg|webp)$/.test(file.type)
        ) {
            alert("Choose a PNG, JPEG or WebP image up to 5 MB.");
            return;
        }

        reader = new FileReader();
        reader.onload = function (event) {
            var image = new Image();

            image.onerror = function () {
                alert("Could not read this image.");
            };

            image.onload = function () {
                handleUploadedImageLoad(image);
            };

            image.src = event.target.result;
        };

        reader.readAsDataURL(file);
    }

    function handleCameraPlaying() {
        hasMedia = true;
        placeholder.style.display = "none";
        updateCaptureButton();
        drawNextFrame();
    }

    function showCameraUnavailableMessage() {
        previewWrap.insertAdjacentHTML(
            "afterend",
            '<p class="editor-help" role="status">Camera not available, choose a photo below.</p>'
        );
    }

    function showExistingPreview(previewSource) {
        var previewImage = new Image();

        placeholder.style.display = "none";

        previewImage.onload = function () {
            isFrozen = true;
            context.drawImage(
                previewImage,
                0,
                0,
                CANVAS_SIZE,
                CANVAS_SIZE
            );
        };

        previewImage.src = previewSource;
        captureButton.style.display = "none";
        retakeButton.style.display = "inline-block";
    }

    function requestCameraForFirstTime() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function (stream) {
                video.srcObject = stream;
                video.addEventListener("playing", handleCameraPlaying);
            })
            .catch(function () {
                showCameraUnavailableMessage();
            });
    }

    function handleRetakeCameraPlaying() {
        video.removeEventListener("playing", handleRetakeCameraPlaying);
        hasMedia = true;
        placeholder.style.display = "none";
        updateCaptureButton();
        drawNextFrame();
    }

    function requestCameraAgain() {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function (stream) {
                video.srcObject = stream;
                video.addEventListener("playing", handleRetakeCameraPlaying);
            })
            .catch(function () {
                hasMedia = false;
                updateCaptureButton();
            });
    }

    function capturePhoto() {
        var imageDataField = document.getElementById("image_data");
        var stickersDataField = document.getElementById("stickers_data");
        var stickerData = [];
        var i;
        var sticker;

        cancelAnimationFrame(animationFrame);
        isFrozen = true;

        // The server adds the stickers to the saved photo.
        context.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
        context.drawImage(
            uploadedPhoto || video,
            0,
            0,
            CANVAS_SIZE,
            CANVAS_SIZE
        );

        for (i = 0; i < stickers.length; i += 1) {
            sticker = stickers[i];
            stickerData.push({
                id: sticker.id,
                x: Math.round(sticker.x),
                y: Math.round(sticker.y),
                w: Math.round(sticker.w),
                h: Math.round(sticker.h),
            });
        }

        imageDataField.value = canvas.toDataURL("image/png");
        stickersDataField.value = JSON.stringify(stickerData);
        captureButton.style.display = "none";
        retakeButton.style.display = "inline-block";
        captureForm.submit();
    }

    function retakePhoto() {
        isFrozen = false;
        uploadedPhoto = null;
        hasMedia = false;
        stickers = [];
        activeStickerIndex = null;
        updateCaptureButton();
        captureButton.style.display = "inline-block";
        retakeButton.style.display = "none";

        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            requestCameraAgain();
        }
    }

    canvas.addEventListener("dblclick", handleDoubleClick);
    canvas.addEventListener("mousedown", handlePointerDown);
    canvas.addEventListener("mousemove", handlePointerMove);
    canvas.addEventListener("mousemove", handlePointerHover);
    canvas.addEventListener("mouseup", handlePointerUp);
    canvas.addEventListener("mouseleave", handlePointerUp);
    canvas.addEventListener("touchstart", handlePointerDown, { passive: false });
    canvas.addEventListener("touchmove", handlePointerMove, { passive: false });
    canvas.addEventListener("touchend", handlePointerUp);

    var i;
    for (i = 0; i < overlayButtons.length; i += 1) {
        overlayButtons[i].addEventListener("click", handleOverlayClick);
    }

    fileInput.addEventListener("change", handleFileSelection);
    captureButton.addEventListener("click", capturePhoto);
    retakeButton.addEventListener("click", retakePhoto);

    var previewSource = canvas.dataset.preview;

    if (previewSource) {
        showExistingPreview(previewSource);
    } else if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        requestCameraForFirstTime();
    }
}

startEditor();
