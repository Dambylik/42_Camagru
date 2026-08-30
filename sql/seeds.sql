-- Seed overlays. Runs on first DB boot after schema.sql.
-- Overlay PNG files must exist in public/overlays/
INSERT INTO overlays (name, path) VALUES
    ('Cat',       'cat-kitten-humour-puppy-mouse-cat.png'),
    ('Nose Rose', 'nose-rose.png'),
    ('Nose',      'nose.png'),
    ('Whiskers 1','whiskers-kitten-domestic-short-haired.png'),
    ('Whiskers 2','whiskers-meme-japanese-bobtail.png'),
    ('Whiskers 3','whiskers-meme-sticker.png');
