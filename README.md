# ObsidianTime

Веб-приложение на Django с мемами, чатом, цитатами и интеграцией с социальными сетями.

## Возможности

- 🎬 **Локальное видео на главной странице** (поддержка MP4, WebM, OGG)
- 💬 **Чат в реальном времени** с голосованиями для авторизованных пользователей
- 🖼️ **Галерея мемов** с системой лайков/дизлайков и комментариев
- 📝 **Коллекция цитат** с возможностью добавления и поиска
- 🔐 **Система регистрации и авторизации**
- 📱 **Адаптивный дизайн** с Bootstrap 5
- 🚀 **Docker-ready** для простого развертывания
- ☁️ **AWS S3 / MinIO интеграция** для хранения медиа файлов

## Установка и запуск

### Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd obsidiantime
```

2. Установите зависимости:
```bash
pip install poetry
poetry install
```

3. Настройте переменные окружения (создайте файл `.env`):
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite по умолчанию для разработки)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Для PostgreSQL
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=obsidiantime
# DB_USER=obsidiantime_user
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432
```

4. Выполните миграции и создайте суперпользователя:
```bash
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
```

5. Загрузите тестовые данные:
```bash
poetry run python manage.py setup_initial_data
```

6. Запустите сервер:
```bash
poetry run python manage.py runserver
```

### Docker-запуск

**Для разработки (MinIO S3-хранилище):**
```bash
# Запустите проект с MinIO
docker-compose up -d

# Настройте MinIO bucket
docker-compose exec web python manage.py setup_minio

# Выполните миграции и создайте тестовые данные
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py setup_initial_data
```

**Для продакшена (AWS S3):**
```bash
# Создайте .env файл с S3 настройками
cp .env.example .env
# Отредактируйте .env файл

# Запустите продакшен версию
docker-compose -f docker-compose.prod.yml up -d

# Выполните миграции и создайте тестовые данные
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py setup_initial_data
```

**Конфигурация хранилища:**

- `docker-compose.yml` - **MinIO S3-хранилище** (локальная разработка с S3 API)
- `docker-compose.prod.yml` - **AWS S3 хранилище** (продакшен)

**Доступ к сервисам:**
- Приложение: http://localhost
- MinIO Console: http://localhost:9001 (obsidiantime / obsidiantime123)
- PostgreSQL: localhost:5432

## Настройка AWS S3 для медиа файлов

### 1. Создание S3 bucket

1. Войдите в AWS Console
2. Перейдите в S3 и создайте новый bucket
3. Настройте public access для медиа файлов
4. Создайте IAM пользователя с правами доступа к bucket

### 2. Настройка переменных окружения

Добавьте в ваш `.env` файл:
```env
# AWS S3 Settings
USE_S3=true
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

### 3. Политика IAM для S3 bucket

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name/*",
                "arn:aws:s3:::your-bucket-name"
            ]
        }
    ]
}
```

### 4. Миграция существующих медиа файлов

```bash
# Просмотр файлов для миграции
python manage.py migrate_media_to_s3 --dry-run

# Выполнение миграции
python manage.py migrate_media_to_s3
```

## Структура проекта

```
obsidiantime/
├── obsidiantime/
│   ├── main/          # Главное приложение (цитаты, главная страница)
│   ├── chat/          # Чат и голосования
│   ├── gallery/       # Галерея мемов
│   └── config/        # Настройки Django
├── templates/         # HTML шаблоны
├── static/           # Статические файлы (CSS, JS, изображения)
├── docker-compose.yml
├── Dockerfile
└── nginx.conf
```

## Использование

### Админ панель
- URL: `/admin/`
- Логин: `admin`
- Пароль: `admin123`

### Тестовые пользователи
- **demo** / `demo123` - обычный пользователь
- **admin** / `admin123` - администратор

### Основные разделы
- **Главная** (`/`) - локальное видео и ссылки на соцсети
- **Чат** (`/chat/`) - общение и голосования
- **Галерея** (`/gallery/`) - просмотр и загрузка мемов
- **Цитаты** (`/quotes/`) - коллекция цитат
- **О проекте** (`/about/`) - статистика проекта

## Настройка видео

### Загрузка видео через админку

1. Войдите в админку: http://localhost/admin/
2. Перейдите в раздел "Настройки сайта"
3. Загрузите видео файл в поле "Видео для рикролла"
4. Поддерживаемые форматы: MP4, WebM, OGG

### Рекомендации для видео

- **Разрешение**: 1280x720 или 1920x1080
- **Формат**: MP4 (H.264) для лучшей совместимости
- **Размер файла**: до 50MB для быстрой загрузки
- **Длительность**: 30-60 секунд оптимально

## Производственное развертывание

### Docker в продакшене

1. Обновите переменные окружения в `docker-compose.yml`:
```yaml
environment:
  - DEBUG=False
  - SECRET_KEY=your-production-secret-key
  - ALLOWED_HOSTS=your-domain.com
  - USE_S3=true
  - AWS_ACCESS_KEY_ID=your-key
  - AWS_SECRET_ACCESS_KEY=your-secret
  - AWS_STORAGE_BUCKET_NAME=your-bucket
```

2. Настройте SSL через reverse proxy (nginx, traefik)
3. Настройте бэкапы базы данных PostgreSQL
4. Мониторинг логов и производительности

### Рекомендации для продакшена

- Используйте PostgreSQL вместо SQLite
- Настройте CDN для статических файлов
- Включите SSL/TLS
- Настройте мониторинг (Sentry, logs)
- Регулярные бэкапы базы данных и S3

## Разработка

### Установка зависимостей для разработки
```bash
poetry install --with dev
```

### Линтинг и форматирование
```bash
poetry run ruff check .
poetry run ruff format .
```

### Создание миграций
```bash
python manage.py makemigrations
python manage.py migrate
```

## Лицензия

MIT License - см. файл LICENSE для деталей.

## Поддержка

При возникновении проблем создайте issue в репозитории проекта.
