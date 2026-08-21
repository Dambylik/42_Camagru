# PHP + Apache, with the extensions Camagru needs
FROM php:8.2-apache

# pdo_mysql = talk to MariaDB; gd = image editing (the "camagru" part)
# PDO = PHP Data Objects, PHP's standard, built-in way to talk to a database.
# pdo_mysql = the specific driver that lets PDO speak MySQL/MariaDB. Without it,
# new PDO("mysql:...") throws "could not find driver."
# GD is PHP's image library: create, resize, crop, and stack images on top of
# each other.
RUN apt-get update && apt-get install -y libpng-dev libjpeg-dev \
    && docker-php-ext-configure gd --with-jpeg \
    && docker-php-ext-install pdo_mysql gd \
    && rm -rf /var/lib/apt/lists/*

# Apache serves /var/www/html — your compose volume mounts ./src here
