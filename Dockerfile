FROM python:3.10-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --disable-pip-version-check --root-user-action=ignore --no-cache-dir -r requirements.txt \
    && groupadd --gid 1000 camagru \
    && useradd --uid 1000 --gid camagru --no-create-home camagru
COPY backend ./backend
COPY public ./public
COPY config/docker-entrypoint.sh /usr/local/bin/camagru-entrypoint
RUN chmod +x /usr/local/bin/camagru-entrypoint
EXPOSE 8000
ENTRYPOINT ["camagru-entrypoint"]
