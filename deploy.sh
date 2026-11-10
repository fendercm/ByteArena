#!/usr/bin/env sh
# Обновить сервер до свежего main одной командой: ./deploy.sh
# Запускать на сервере в папке проекта. Миграции базы бэкенд применяет сам при старте.
set -eu
cd "$(dirname "$0")"

COMPOSE="docker compose -f docker-compose.prod.yml"

git pull --ff-only

# Образы собираются по очереди: на сервере 1 ГБ памяти, две сборки сразу его не выдержат
$COMPOSE build backend
$COMPOSE build frontend

$COMPOSE up -d --remove-orphans
docker image prune -f
$COMPOSE ps
