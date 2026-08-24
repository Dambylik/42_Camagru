-- Camagru schema. Auto-loaded by the MariaDB container on first boot
-- (mounted into /docker-entrypoint-initdb.d). To reload: docker compose down -v.
-- InnoDB everywhere so foreign keys are actually enforced.

CREATE TABLE users (
    id                 INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    username           VARCHAR(30)   NOT NULL,
    email              VARCHAR(255)  NOT NULL,
    password           VARCHAR(255)  NOT NULL,          -- bcrypt hash, never plain text
    is_verified        TINYINT(1)    NOT NULL DEFAULT 0,
    notify_on_comment  TINYINT(1)    NOT NULL DEFAULT 1, -- V.3: on by default, user can disable
    verify_token       VARCHAR(64)   DEFAULT NULL,
    verify_expires_at  DATETIME      DEFAULT NULL,
    reset_token        VARCHAR(64)   DEFAULT NULL,
    reset_expires_at   DATETIME      DEFAULT NULL,
    created_at         TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Superposable images (frames/props the user stacks on their photo).
CREATE TABLE overlays (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    path        VARCHAR(255) NOT NULL,   -- file on the server (must have an alpha channel)
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- The edited creations. One user -> many images.
CREATE TABLE images (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED NOT NULL,
    path        VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_images_user (user_id),
    KEY idx_images_created (created_at),   -- gallery is ordered by creation date
    CONSTRAINT fk_images_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- One image -> many comments.
CREATE TABLE comments (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    image_id    INT UNSIGNED NOT NULL,
    user_id     INT UNSIGNED NOT NULL,
    content     TEXT         NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_comments_image (image_id),
    CONSTRAINT fk_comments_image FOREIGN KEY (image_id)
        REFERENCES images (id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Many-to-many: users <-> images. Composite PK = one like per user per image.
CREATE TABLE likes (
    user_id     INT UNSIGNED NOT NULL,
    image_id    INT UNSIGNED NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, image_id),
    KEY idx_likes_image (image_id),
    CONSTRAINT fk_likes_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_likes_image FOREIGN KEY (image_id)
        REFERENCES images (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
