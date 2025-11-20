# CI/CD

Этот проект теперь содержит GitHub Actions workflow `.github/workflows/ci-cd.yml`, который автоматизирует проверку кода и деплой на продовый сервер.

## Что делает пайплайн

- **CI (job `test`)** — на каждом `push`/`pull_request` в `main`:
  - checkout репозитория;
  - установка Python 3.12 + зависимостей из `requirements.txt` и `tests/requirements-test.txt`;
  - запуск `pytest`.
- **CD (job `deploy`)** — на `push` в `main` после успешных тестов:
  - подключение по SSH к серверу;
  - `git pull` в каталоге проекта;
  - `docker compose up -d --build bot` для пересборки и рестарта контейнера;
  - `docker compose ps` для быстрой проверки статуса.

## Необходимые секреты в GitHub

Создайте следующие **Repository Secrets** (Settings → Secrets and variables → Actions → New repository secret):

- `DEPLOY_HOST` — адрес сервера (например, `85.198.81.133`).
- `DEPLOY_USER` — пользователь SSH (например, `root`).
- `DEPLOY_SSH_KEY` — приватный ключ для подключения (формат OpenSSH, без пароля или с настроенным агентом).
- `DEPLOY_PATH` — абсолютный путь к каталогу проекта на сервере (например, `/root/bots/25-11-17_Nick_Ai_Test`).

> Порт по умолчанию 22. Если на сервере используется другой, добавьте его в настройках action (`appleboy/ssh-action`) или поменяйте SSH-конфиг пользователя.

## Требования на сервере

- Предустановлены Docker и Docker Compose.
- В каталоге `${DEPLOY_PATH}` уже развернут репозиторий и заполнен `.env` (можно по шаблону `.env.example`).
- Пользователь из `DEPLOY_USER` имеет права на выполнение Docker-команд (для `root` это автоматически).

## Ручной прогон деплоя

После настройки секретов и первого пуша в `main` пайплайн запустится автоматически. При необходимости можно запустить `workflow_dispatch` через интерфейс GitHub Actions (Run workflow), чтобы вручную инициировать деплой без нового коммита.

## Проверка результата

В выводе job `deploy` должны быть видны команды `docker compose up -d --build bot` и `docker compose ps`. На сервере можно дополнительно проверить логи бота:

```bash
docker compose logs -f bot
```

И убедиться, что в логах есть сообщения вида `Bot started successfully` / `Polling started` без ошибок соединения с БД или Telegram.
