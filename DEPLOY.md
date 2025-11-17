# Деплой на сервер

## Шаги на сервере

```bash
# 1. Установить Docker
curl -fsSL https://get.docker.com | sh

# 2. Клонировать репозиторий
git clone <your-repo-url>
cd <repo-name>

# 3. Настроить .env
cp .env.example .env
nano .env  # Заполнить токены

# 4. Запустить
docker compose build
docker compose up -d

# 5. Проверить логи
docker compose logs -f bot
```

## Управление

```bash
# Перезапуск
docker compose restart bot

# Остановка
docker compose down

# Обновление
git pull && docker compose up -d --build bot
```
