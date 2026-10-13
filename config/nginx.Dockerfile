FROM nginx:stable-alpine
RUN sed -i 's|error_log .*;|error_log /tmp/camagru-nginx-errors.log warn;|' /etc/nginx/nginx.conf
COPY config/nginx.conf /etc/nginx/conf.d/default.conf
COPY public /usr/share/nginx/html
