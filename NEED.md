Я проанализирую ваш Django проект и дам рекомендации по подготовке к продакшну. Давайте начнем с изучения основных конфигурационных файлов:
Read file: obsidiantime/config/settings.py
Read file: pyproject.toml
Read file: docker-compose.prod.yml
Read file: Dockerfile

Read file: nginx.conf
Ran tool
Read file: obsidiantime/config/storage_backends.py
Ran tool

Ran tool
Ran tool
Ran tool
Ran tool

Основываясь на анализе вашего Django проекта, я подготовил комплексные рекомендации для подготовки к продакшену. Вот основные области, которые требуют внимания:

## 🔒 **КРИТИЧЕСКИЕ НАСТРОЙКИ БЕЗОПАСНОСТИ**

### 1. Настройки Django (`settings.py`)

```python:obsidiantime/config/settings.py
# ... existing code ...

# Продакшн настройки безопасности
if not DEBUG:
    # HTTPS настройки
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # HSTS настройки
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Cookie безопасность
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    CSRF_COOKIE_SAMESITE = 'Strict'
    
    # Content Security Policy заголовки
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Админка
    ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')
    
    # Дополнительные security middleware
    MIDDLEWARE.insert(0, 'django.middleware.security.SecurityMiddleware')

# Логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/security.log',
            'maxBytes': 1024*1024*15,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
        'django.security': {
            'handlers': ['security', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'obsidiantime': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
    },
}

# Rate limiting (если используете django-ratelimit)
RATELIMIT_ENABLE = True

# Кеширование (Redis)
if os.getenv('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600
if not DEBUG:
    DATABASES['default']['OPTIONS'] = {
        'MAX_CONNS': 20,
        'MIN_CONNS': 5,
    }

# Email настройки для продакшена
if not DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@obsidiantime.ru')
    
    # Отправка ошибок администраторам
    ADMINS = [('Admin', os.getenv('ADMIN_EMAIL', 'admin@obsidiantime.ru'))]
    MANAGERS = ADMINS
```

### 2. Обновленный Dockerfile

```dockerfile:Dockerfile
FROM python:3.11-slim

# Создаем пользователя для запуска приложения
RUN groupadd -r django && useradd -r -g django django

# Устанавливаем системные зависимости
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        libwebp-dev \
        tcl8.6-dev \
        tk8.6-dev \
        python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Настройки окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Рабочая директория
WORKDIR /app

# Устанавливаем зависимости Python
COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main --no-dev

# Копируем код приложения
COPY --chown=django:django . .

# Создаем необходимые директории
RUN mkdir -p /app/logs /app/media /app/staticfiles && \
    chown -R django:django /app

# Переключаемся на непривилегированного пользователя
USER django

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python manage.py check --deploy || exit 1

# Экспонируем порт
EXPOSE 8000

# Команда запуска
CMD ["gunicorn", "obsidiantime.config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
```

### 3. Продакшн nginx конфигурация

```nginx:nginx.prod.conf
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

upstream django_app {
    server web:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name obsidiantime.ru www.obsidiantime.ru;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name obsidiantime.ru www.obsidiantime.ru;

    # SSL конфигурация
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Общие настройки
    client_max_body_size 20M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    # Логирование
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Основное приложение
    location / {
        proxy_pass http://django_app;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limiting для аутентификации
    location /auth/ {
        limit_req zone=auth burst=10 nodelay;
        proxy_pass http://django_app;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $host;
        proxy_redirect off;
    }

    # Статические файлы
    location /static/ {
        alias /app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }

    # Медиа файлы (если не используется S3)
    location /media/ {
        alias /app/media/;
        expires 30d;
        add_header Cache-Control "public";
        add_header X-Content-Type-Options nosniff;
    }

    # Запрет доступа к чувствительным файлам
    location ~ /\. {
        deny all;
    }

    location ~ /(\.env|\.git) {
        deny all;
    }

    # Gzip сжатие
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json
        image/svg+xml;
}
```

### 4. Улучшенный docker-compose.prod.yml

```yaml:docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: postgres:17
    restart: unless-stopped
    environment:
      POSTGRES_DB: obsidiantime
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 128M

  web:
    build: .
    restart: unless-stopped
    command: >
      bash -c "
        python manage.py migrate &&
        python manage.py collectstatic --noinput &&
        gunicorn obsidiantime.config.wsgi:application 
          --bind 0.0.0.0:8000 
          --workers 3
          --worker-class sync
          --worker-connections 1000
          --max-requests 1000
          --max-requests-jitter 100
          --timeout 120
          --keepalive 5
          --access-logfile -
          --error-logfile -
      "
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - logs_volume:/app/logs
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DB_NAME=obsidiantime
      - DB_USER=postgres
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - USE_S3=true
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME}
      - AWS_S3_REGION_NAME=${AWS_S3_REGION_NAME}
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
      - ADMIN_EMAIL=${ADMIN_EMAIL}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./ssl:/etc/nginx/ssl:ro
      - logs_volume:/var/log/nginx
    depends_on:
      - web
    deploy:
      resources:
        limits:
          memory: 128M

  # Backup сервис
  backup:
    image: postgres:17
    restart: "no"
    environment:
      PGPASSWORD: ${DB_PASSWORD}
    volumes:
      - ./backups:/backups
      - ./scripts:/scripts
    command: /scripts/backup.sh
    depends_on:
      - db
    profiles:
      - backup

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
  logs_volume:
```

## 🛡️ **ДОПОЛНИТЕЛЬНЫЕ ФАЙЛЫ БЕЗОПАСНОСТИ**

### 1. Создайте .env.example

```bash:.env.example
# Django настройки
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=obsidiantime.ru,www.obsidiantime.ru

# База данных
DB_PASSWORD=your-db-password

# Redis
REDIS_PASSWORD=your-redis-password

# S3 Storage
USE_S3=true
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
ADMIN_EMAIL=admin@obsidiantime.ru

# URL админки (для безопасности)
ADMIN_URL=secure-admin-panel/
```

### 2. Скрипт бэкапа

```bash:scripts/backup.sh
#!/bin/bash
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="obsidiantime"
DB_USER="postgres"
DB_HOST="db"

# Создаем бэкап
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Удаляем старые бэкапы (старше 30 дней)
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete

echo "Backup completed: backup_$DATE.sql"
```

### 3. Файл мониторинга здоровья

```python:obsidiantime/main/health.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis

def health_check(request):
    """Проверка состояния всех сервисов"""
    status = {
        'status': 'healthy',
        'services': {}
    }
    
    # Проверка БД
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['services']['database'] = 'healthy'
    except Exception as e:
        status['services']['database'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Проверка Redis
    try:
        cache.set('health_check', 'ok', 30)
        if cache.get('health_check') == 'ok':
            status['services']['cache'] = 'healthy'
        else:
            status['services']['cache'] = 'unhealthy'
            status['status'] = 'unhealthy'
    except Exception as e:
        status['services']['cache'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    return JsonResponse(status)
```

## 📊 **МОНИТОРИНГ И ПРОИЗВОДИТЕЛЬНОСТЬ**

### 1. Обновите requirements

```toml:pyproject.toml
dependencies = [
    # ... existing dependencies ...
    "django-redis (>=5.4.0,<6.0.0)",
    "django-ratelimit (>=4.1.0,<5.0.0)",
    "sentry-sdk[django] (>=2.0.0,<3.0.0)",
    "django-health-check (>=3.18.0,<4.0.0)",
    "whitenoise (>=6.8.2,<7.0.0)",
]
```

### 2. Добавьте Sentry для мониторинга ошибок

```python:obsidiantime/config/settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

# Sentry настройки для продакшена
if not DEBUG and os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(auto_enabling=True),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment="production",
    )
```

## 🚀 **ИТОГОВЫЙ ЧЕКЛИСТ ДЛЯ ПРОДАКШЕНА**

### Обязательные действия:
- [ ] Сгенерировать надежный SECRET_KEY
- [ ] Настроить ALLOWED_HOSTS
- [ ] Установить DEBUG=False
- [ ] Настроить SSL сертификаты
- [ ] Создать .env файл с реальными данными
- [ ] Настроить резервное копирование БД
- [ ] Добавить мониторинг (Sentry)
- [ ] Настроить логирование
- [ ] Протестировать все функции в продакшн окружении

### Рекомендуемые улучшения:
- [ ] Добавить CDN для статических файлов
- [ ] Настроить автоматические обновления безопасности
- [ ] Добавить мониторинг производительности
- [ ] Настроить CI/CD пайплайн
- [ ] Добавить автоматические тесты безопасности

Эти изменения значительно повысят безопасность, стабильность и производительность вашего приложения в продакшене.