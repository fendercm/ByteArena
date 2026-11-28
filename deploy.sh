#!/usr/bin/env sh
# Обновить сервер до свежего main одной командой: ./deploy.sh
# Запускать на сервере в папке проекта. Миграции базы бэкенд применяет сам при старте.
set -eu
cd "$(dirname "$0")"

COMPOSE="docker compose -f docker-compose.prod.yml"

# Защита от опасных настроек: без https-cookie и с отладочным входом сайт выкладывать нельзя
if ! grep -qE '^COOKIE_SECURE=true[[:space:]]*$' .env; then
  echo "В .env должно быть COOKIE_SECURE=true: на сервере сайт работает по https" >&2
  exit 1
fi
if grep -qE '^DEBUG_AUTH_ENABLED=true[[:space:]]*$' .env; then
  echo "В .env DEBUG_AUTH_ENABLED=true: на сервере вход без Discord должен быть выключен" >&2
  exit 1
fi

git pull --ff-only

# Образы собираются по очереди: на сервере 1 ГБ памяти, две сборки сразу его не выдержат
$COMPOSE build backend
$COMPOSE build frontend

$COMPOSE up -d --remove-orphans
# старые образы и кэш сборки: на сервере мало места на диске
docker image prune -f
docker builder prune -f
$COMPOSE ps
