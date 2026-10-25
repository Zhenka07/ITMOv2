# Инструкция по развертыванию бота на сервере

Данное руководство описывает два способа запуска бота на удаленном Linux-сервере (Ubuntu, Debian и др.):
1. **[Рекомендуемый] Docker & Docker Compose** — изолированный запуск с автоперезапуском и сохранностью базы данных.
2. **Systemd Service** — запуск в виде нативного системного сервиса Linux (без Docker).

---

## Способ 1. Запуск через Docker Compose (Рекомендуемый)

Этот вариант не требует установки Go и gcc на сервере — сборка и запуск происходят в изолированном контейнере.

### 1. Требования к серверу
На сервере должны быть установлены `docker` и `docker compose`:
```bash
# Ubuntu / Debian
curl -fsSL https://get.docker.com | sh
```

### 2. Подготовка файлов на сервере
Склонируйте репозиторий на сервер:
```bash
git clone https://github.com/Zhenka07/TelegramBot.git
cd TelegramBot
```

### 3. Настройка переменных окружения
Скопируйте пример файла конфигурации:
```bash
cp .env.example .env
```
Откройте `.env` через любой текстовый редактор (например, `nano .env`) и укажите ваш токен:
```env
TELEGRAM_API_KEY=123456789:ABCdefGhIJKlmNoPQRstuVwXyz
```

### 4. Сборка и запуск
Запустите контейнер в фоновом режиме:
```bash
docker compose up -d --build
```
или через команду:
```bash
make docker-up
```

> [!NOTE]
> База данных SQLite сохраняется на сервере в папку `./data/storage.db`. Даже при перезапуске, обновлении или пересборке контейнера данные пользователей не пропадут.

### 5. Полезные команды управления:
- **Просмотр логов в реальном времени:**
  ```bash
  docker compose logs -f
  # или: make docker-logs
  ```
- **Остановка бота:**
  ```bash
  docker compose down
  # или: make docker-down
  ```
- **Перезапуск бота:**
  ```bash
  docker compose restart
  ```
- **Обновление бота на новую версию:**
  ```bash
  git pull
  docker compose up -d --build
  ```

---

## Способ 2. Запуск через Systemd (нативный демон)

Используйте этот способ, если на сервере не используется Docker.

### 1. Подготовка окружения на сервере
Для компиляции приложения с драйвером SQLite (`go-sqlite3`) потребуется установленный Go (1.22+) и `gcc`:
```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y build-essential golang git
```

### 2. Размещение файлов бота
Создайте рабочую директорию бота (например, `/opt/telegram-bot`):
```bash
sudo mkdir -p /opt/telegram-bot
sudo chown $USER:$USER /opt/telegram-bot
```

Склонируйте репозиторий или скопируйте файлы:
```bash
cd /opt/telegram-bot
git clone https://github.com/Zhenka07/TelegramBot.git .
```

### 3. Сборка бинарного файла
```bash
make build
```
Это создаст исполняемый файл `bot_app`.

### 4. Конфигурация `.env`
```bash
cp .env.example .env
nano .env
```
Укажите ваш `TELEGRAM_API_KEY`.

### 5. Установка и запуск Systemd-сервиса
Скопируйте готовый unit-файл в системный каталог:
```bash
sudo cp bot.service /etc/systemd/system/bot.service
```

Если путь отличается от `/opt/telegram-bot`, отредактируйте пути в `/etc/systemd/system/bot.service`:
```ini
WorkingDirectory=/opt/telegram-bot
ExecStart=/opt/telegram-bot/bot_app
EnvironmentFile=/opt/telegram-bot/.env
```

Примените изменения и запустите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bot.service
```

### 6. Управление сервисом:
- **Проверка статуса:**
  ```bash
  sudo systemctl status bot
  ```
- **Просмотр логов:**
  ```bash
  sudo journalctl -u bot -f
  ```
- **Перезапуск:**
  ```bash
  sudo systemctl restart bot
  ```
- **Остановка:**
  ```bash
  sudo systemctl stop bot
  ```

---

## 💾 Резервное копирование базы данных

База данных хранится в одном файле SQLite. Для создания резервной копии достаточно скопировать файл:
- Для Docker: `./data/storage.db`
- Для Systemd: `user_data/sqlite/storage.db` (или путь, указанный в `SQLITE_PATH`).
