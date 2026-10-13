(function () {
    var config = document.getElementById("gallery-config").dataset;
    var CSRF = config.csrf;
    var loggedIn = config.loggedIn === "true";
    var curPage = Number(config.page);
    var maxPages = Number(config.pages);
    var loading = false;
    var failed = false;
    var grid = document.querySelector(".gallery-grid");
    var sentinel = document.getElementById("scroll-sentinel");
    var loader = document.getElementById("scroll-loader");
    var retry = document.getElementById("scroll-retry");
    var pagination = document.getElementById("pagination");

    // Hide static pagination — infinite scroll takes over
    if (pagination) pagination.style.display = "none";

    function post(url, data, cb) {
        data["_csrf_token"] = CSRF;
        var body = Object.keys(data)
            .map(function (k) {
                return encodeURIComponent(k) + "=" + encodeURIComponent(data[k]);
            })
            .join("&");
        var xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        xhr.onload = function () {
            if (xhr.status === 200) {
                try {
                    cb(JSON.parse(xhr.responseText));
                } catch (e) {}
            }
        };
        xhr.send(body);
    }

    function get(url, cb, fail, done) {
        var xhr = new XMLHttpRequest();
        var settled = false;
        function finish(error, result) {
            if (settled) return;
            settled = true;
            try {
                if (error) fail();
                else cb(result);
            } catch (e) {
                fail();
            } finally {
                done();
            }
        }
        try {
            xhr.open("GET", url, true);
            xhr.timeout = 15000;
            xhr.onload = function () {
                if (xhr.status !== 200) {
                    finish(true);
                    return;
                }
                var result;
                try {
                    result = JSON.parse(xhr.responseText);
                } catch (e) {
                    finish(true);
                    return;
                }
                finish(false, result);
            };
            xhr.onerror =
                xhr.ontimeout =
                xhr.onabort =
                    function () {
                        finish(true);
                    };
            xhr.send();
        } catch (e) {
            finish(true);
        }
    }

    // ── Build a card from JSON data ───────────────────────────────────────────
    function buildCard(img) {
        var card = document.createElement("div");
        card.className = "gallery-card";
        card.id = "img-" + img.id;

        var image = document.createElement("img");
        image.src = "uploads/" + img.path;
        image.alt = "Image by " + img.username;
        card.appendChild(image);

        var meta = document.createElement("div");
        meta.className = "meta";
        var uname = document.createElement("span");
        uname.textContent = img.username;
        meta.appendChild(uname);

        if (loggedIn) {
            var btn = document.createElement("button");
            btn.className = "like-btn" + (img.liked ? " liked" : "");
            btn.setAttribute("data-id", img.id);
            btn.innerHTML = '💞 <span class="like-count">' + img.like_count + "</span>";
            bindLike(btn);
            meta.appendChild(btn);
        } else {
            var lspan = document.createElement("span");
            lspan.textContent = "💞 " + img.like_count;
            meta.appendChild(lspan);
        }
        card.appendChild(meta);

        var comments = document.createElement("div");
        comments.className = "comments";
        var list = document.createElement("div");
        list.className = "comment-list";
        img.comments.forEach(function (c) {
            list.appendChild(buildComment(c.username, c.content));
        });
        comments.appendChild(list);

        if (loggedIn) {
            var form = document.createElement("form");
            form.className = "comment-form";
            form.setAttribute("data-id", img.id);
            var input = document.createElement("input");
            input.type = "text";
            input.name = "content";
            input.placeholder = "Say something nice... 🐱";
            input.maxLength = 500;
            input.required = true;
            var submitBtn = document.createElement("button");
            submitBtn.className = "btn btn-ghost";
            submitBtn.type = "submit";
            submitBtn.textContent = "Post";
            form.appendChild(input);
            form.appendChild(submitBtn);
            bindComment(form);
            comments.appendChild(form);
        }
        card.appendChild(comments);
        return card;
    }

    function buildComment(username, content) {
        var div = document.createElement("div");
        div.className = "comment";
        var author = document.createElement("span");
        author.className = "author";
        author.textContent = username;
        div.appendChild(author);
        div.appendChild(document.createTextNode(content));
        return div;
    }

    // ── Bind like ─────────────────────────────────────────────────────────────
    function bindLike(btn) {
        btn.addEventListener("click", function () {
            var id = btn.getAttribute("data-id");
            post("/?page=like-ajax", { image_id: id }, function (res) {
                if (res.error) return;
                btn.querySelector(".like-count").textContent = res.count;
                if (res.liked) btn.classList.add("liked");
                else btn.classList.remove("liked");
            });
        });
    }

    // ── Bind comment ──────────────────────────────────────────────────────────
    function bindComment(form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            var id = form.getAttribute("data-id");
            var input = form.querySelector("input[name=content]");
            var content = input.value.trim();
            if (!content) return;
            post(
                "/?page=comment-ajax",
                { image_id: id, content: content },
                function (res) {
                    if (res.error) return;
                    var list = document.querySelector("#img-" + id + " .comment-list");
                    list.appendChild(buildComment(res.username, res.content));
                    input.value = "";
                },
            );
        });
    }

    // ── Bind existing cards ───────────────────────────────────────────────────
    var likeBtns = document.querySelectorAll(".like-btn[data-id]");
    for (var i = 0; i < likeBtns.length; i++) bindLike(likeBtns[i]);
    var commentForms = document.querySelectorAll(".comment-form[data-id]");
    for (var j = 0; j < commentForms.length; j++) bindComment(commentForms[j]);

    // ── Load next page ────────────────────────────────────────────────────────
    function loadNext() {
        if (loading || curPage >= maxPages) return;
        loading = true;
        failed = false;
        retry.style.display = "none";
        loader.style.display = "block";
        var nextPage = curPage + 1;
        get(
            "/?page=gallery-json&p=" + nextPage,
            function (res) {
                if (
                    !res ||
                    res.page !== nextPage ||
                    typeof res.pages !== "number" ||
                    !Array.isArray(res.images)
                )
                    throw new Error("Invalid gallery response");
                // Build before appending so a malformed card cannot partially duplicate a page.
                var fragment = document.createDocumentFragment();
                res.images.forEach(function (img) {
                    fragment.appendChild(buildCard(img));
                });
                grid.appendChild(fragment);
                curPage = res.page;
                maxPages = res.pages;
            },
            function () {
                failed = true;
                retry.style.display = "inline-block";
            },
            function () {
                loader.style.display = "none";
                loading = false;
            },
        );
    }

    retry.addEventListener("click", loadNext);

    // ── Scroll listener ───────────────────────────────────────────────────────
    window.addEventListener("scroll", function () {
        var rect = sentinel.getBoundingClientRect();
        if (!failed && rect.top <= window.innerHeight + 200) loadNext();
    });

    // trigger immediately in case first page doesn't fill the viewport
    loadNext();
})();
