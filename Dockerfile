# PHP + Apache, with the extensions Camagru needs
FROM php:8.2-apache

# pdo_mysql = talk to MariaDB; gd = image editing (the "camagru" part)
# PDO = PHP Data Objects, PHP's standard, built-in way to talk to a database.
# pdo_mysql = the specific driver that lets PDO speak MySQL/MariaDB. Without it,
# new PDO("mysql:...") throws "could not find driver."
# GD is PHP's image library: create, resize, crop, and stack images on top of
# each other.
RUN apt-get update && apt-get install -y libpng-dev libjpeg-dev msmtp \
    && docker-php-ext-configure gd --with-jpeg \
    && docker-php-ext-install pdo_mysql gd \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/msmtp /usr/sbin/sendmail

COPY config/msmtp.conf /etc/msmtprc

# Serve only public/ (keeps app/ source out of the web root).
# All requests hit public/index.php?page=... — no rewrite module needed.
COPY config/apache.conf /etc/apache2/sites-available/000-default.conf

# Apache serves /var/www/html/public — compose mounts the whole project at /var/www/html
