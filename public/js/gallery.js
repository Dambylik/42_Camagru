(function () {
    var config = document.getElementById("gallery-config").dataset;
    var csrfToken = config.csrf;
    var isLoggedIn = config.loggedIn === "true";
    var currentPage = Number(config.page);
    var lastPage = Number(config.pages);
    var isLoading = false;
    var hasLoadFailed = false;

    var galleryGrid = document.querySelector(".gallery-grid");
    var scrollMarker = document.getElementById("scroll-sentinel");
    var loadingMessage = document.getElementById("scroll-loader");
    var retryButton = document.getElementById("scroll-retry");
    var pagination = document.getElementById("pagination");

    // Hide page numbers because this page loads more photos while scrolling.
    if (pagination) {
        pagination.style.display = "none";
    }

    function makeFormBody(data) {
        var keys = Object.keys(data);
        var fields = [];
        var i;
        var key;
        var field;

        for (i = 0; i < keys.length; i += 1) {
            key = keys[i];
            field = encodeURIComponent(key) + "="
                + encodeURIComponent(data[key]);
            fields.push(field);
        }

        return fields.join("&");
    }

    function sendPostRequest(url, data, onSuccess) {
        var request = new XMLHttpRequest();

        data["_csrf_token"] = csrfToken;

        request.open("POST", url, true);
        request.setRequestHeader(
            "Content-Type",
            "application/x-www-form-urlencoded"
        );

        request.onload = function () {
            var result;

            if (request.status !== 200) {
                return;
            }

            try {
                result = JSON.parse(request.responseText);
            } catch (error) {
                return;
            }

            onSuccess(result);
        };

        request.send(makeFormBody(data));
    }

    function sendGetRequest(url, onSuccess, onFailure, onComplete) {
        var request = new XMLHttpRequest();
        var isFinished = false;

        function finishRequest(hasError, result) {
            if (isFinished) {
                return;
            }

            isFinished = true;

            try {
                if (hasError) {
                    onFailure();
                } else {
                    onSuccess(result);
                }
            } catch (error) {
                onFailure();
            } finally {
                onComplete();
            }
        }

        try {
            request.open("GET", url, true);
            request.timeout = 15000;

            request.onload = function () {
                var result;

                if (request.status !== 200) {
                    finishRequest(true);
                    return;
                }

                try {
                    result = JSON.parse(request.responseText);
                } catch (error) {
                    finishRequest(true);
                    return;
                }

                finishRequest(false, result);
            };

            request.onerror = function () {
                finishRequest(true);
            };

            request.ontimeout = function () {
                finishRequest(true);
            };

            request.onabort = function () {
                finishRequest(true);
            };

            request.send();
        } catch (error) {
            finishRequest(true);
        }
    }

    function makeComment(username, content) {
        var comment = document.createElement("div");
        var author = document.createElement("span");

        comment.className = "comment";
        author.className = "author";
        author.textContent = username;
        comment.appendChild(author);
        comment.appendChild(document.createTextNode(content));

        return comment;
    }

    function addLikeButton(meta, image) {
        var button = document.createElement("button");
        var heart = document.createTextNode("💞 ");
        var count = document.createElement("span");
        var className = "like-btn";

        if (image.liked) {
            className += " liked";
        }

        button.className = className;
        button.setAttribute("data-id", image.id);
        count.className = "like-count";
        count.textContent = image.like_count;

        button.appendChild(heart);
        button.appendChild(count);
        bindLikeButton(button);
        meta.appendChild(button);
    }

    function addLikeCount(meta, image) {
        var count = document.createElement("span");
        count.textContent = "💞 " + image.like_count;
        meta.appendChild(count);
    }

    function addCommentForm(comments, image) {
        var form = document.createElement("form");
        var input = document.createElement("input");
        var submitButton = document.createElement("button");

        form.className = "comment-form";
        form.setAttribute("data-id", image.id);

        input.type = "text";
        input.name = "content";
        input.placeholder = "Say something nice... 🐱";
        input.maxLength = 500;
        input.required = true;

        submitButton.className = "btn btn-ghost";
        submitButton.type = "submit";
        submitButton.textContent = "Post";

        form.appendChild(input);
        form.appendChild(submitButton);
        bindCommentForm(form);
        comments.appendChild(form);
    }

    function makeGalleryCard(image) {
        var card = document.createElement("div");
        var photo = document.createElement("img");
        var meta = document.createElement("div");
        var username = document.createElement("span");
        var comments = document.createElement("div");
        var commentList = document.createElement("div");
        var i;
        var commentData;

        card.className = "gallery-card";
        card.id = "img-" + image.id;

        photo.src = "uploads/" + image.path;
        photo.alt = "Image by " + image.username;
        card.appendChild(photo);

        meta.className = "meta";
        username.textContent = image.username;
        meta.appendChild(username);

        if (isLoggedIn) {
            addLikeButton(meta, image);
        } else {
            addLikeCount(meta, image);
        }

        card.appendChild(meta);

        comments.className = "comments";
        commentList.className = "comment-list";

        for (i = 0; i < image.comments.length; i += 1) {
            commentData = image.comments[i];
            commentList.appendChild(
                makeComment(commentData.username, commentData.content)
            );
        }

        comments.appendChild(commentList);

        if (isLoggedIn) {
            addCommentForm(comments, image);
        }

        card.appendChild(comments);
        return card;
    }

    function bindLikeButton(button) {
        button.addEventListener("click", function () {
            var imageId = button.getAttribute("data-id");

            sendPostRequest(
                "/?page=like-ajax",
                { image_id: imageId },
                function (result) {
                    var count;

                    if (result.error) {
                        return;
                    }

                    count = button.querySelector(".like-count");
                    count.textContent = result.count;

                    if (result.liked) {
                        button.classList.add("liked");
                    } else {
                        button.classList.remove("liked");
                    }
                }
            );
        });
    }

    function bindCommentForm(form) {
        form.addEventListener("submit", function (event) {
            var imageId;
            var input;
            var content;

            event.preventDefault();

            imageId = form.getAttribute("data-id");
            input = form.querySelector("input[name=content]");
            content = input.value.trim();

            if (!content) {
                return;
            }

            sendPostRequest(
                "/?page=comment-ajax",
                { image_id: imageId, content: content },
                function (result) {
                    var commentList;

                    if (result.error) {
                        return;
                    }

                    commentList = document.querySelector(
                        "#img-" + imageId + " .comment-list"
                    );
                    commentList.appendChild(
                        makeComment(result.username, result.content)
                    );
                    input.value = "";
                }
            );
        });
    }

    function bindExistingButtons() {
        var likeButtons = document.querySelectorAll(".like-btn[data-id]");
        var commentForms = document.querySelectorAll(".comment-form[data-id]");
        var i;

        for (i = 0; i < likeButtons.length; i += 1) {
            bindLikeButton(likeButtons[i]);
        }

        for (i = 0; i < commentForms.length; i += 1) {
            bindCommentForm(commentForms[i]);
        }
    }

    function isValidGalleryResponse(result, expectedPage) {
        if (!result) {
            return false;
        }

        if (result.page !== expectedPage) {
            return false;
        }

        if (typeof result.pages !== "number") {
            return false;
        }

        if (!Array.isArray(result.images)) {
            return false;
        }

        return true;
    }

    function addImagesToGallery(images) {
        var fragment = document.createDocumentFragment();
        var i;

        for (i = 0; i < images.length; i += 1) {
            fragment.appendChild(makeGalleryCard(images[i]));
        }

        galleryGrid.appendChild(fragment);
    }

    function loadNextPage() {
        var nextPage;
        var url;

        if (isLoading || currentPage >= lastPage) {
            return;
        }

        isLoading = true;
        hasLoadFailed = false;
        retryButton.style.display = "none";
        loadingMessage.style.display = "block";

        nextPage = currentPage + 1;
        url = "/?page=gallery-json&p=" + nextPage;

        sendGetRequest(
            url,
            function (result) {
                if (!isValidGalleryResponse(result, nextPage)) {
                    throw new Error("Invalid gallery response");
                }

                // Build all cards first, then add them together.
                addImagesToGallery(result.images);
                currentPage = result.page;
                lastPage = result.pages;
            },
            function () {
                hasLoadFailed = true;
                retryButton.style.display = "inline-block";
            },
            function () {
                loadingMessage.style.display = "none";
                isLoading = false;
            }
        );
    }

    function handleWindowScroll() {
        var markerBounds = scrollMarker.getBoundingClientRect();
        var shouldLoadMore = markerBounds.top <= window.innerHeight + 200;

        if (!hasLoadFailed && shouldLoadMore) {
            loadNextPage();
        }
    }

    bindExistingButtons();
    retryButton.addEventListener("click", loadNextPage);
    window.addEventListener("scroll", handleWindowScroll);

    // Load another page immediately if the first page is shorter than the screen.
    loadNextPage();
})();
