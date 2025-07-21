# Мониторинг с Django-Prometheus

Этот проект настроен для мониторинга с использованием Django-Prometheus, Prometheus и Grafana.

## Компоненты мониторинга

### 1. Django-Prometheus
- Автоматически собирает метрики Django
- Предоставляет endpoint `/metrics` для Prometheus
- Отслеживает запросы, базу данных, кеш и другие компоненты

### 2. Кастомные метрики
- Метрики пользователей (регистрации, логины)
- Метрики галереи (загрузки мемов, просмотры)
- Метрики чата (сообщения)
- Метрики обратной связи
- Метрики производительности (время запросов, запросы к БД)
- Метрики состояния системы (активные пользователи, количество мемов)

### 3. Prometheus
- Собирает метрики с Django приложения
- Хранит исторические данные
- Предоставляет API для запросов

### 4. Grafana
- Визуализация метрик
- Создание дашбордов
- Настройка алертов

## Установка и запуск

### 1. Установка зависимостей
```bash
poetry install
```

### 2. Запуск с Docker Compose
```bash
docker-compose up -d
```

### 3. Применение миграций
```bash
docker-compose exec web python manage.py migrate
```

### 4. Создание суперпользователя
```bash
docker-compose exec web python manage.py createsuperuser
```

## Доступ к сервисам

- **Django приложение**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **MinIO Console**: http://localhost:9001 (obsidiantime/obsidiantime123)

## Метрики

### Автоматические метрики Django-Prometheus
- `django_http_requests_total` - общее количество HTTP запросов
- `django_http_requests_latency_seconds` - время выполнения запросов
- `django_http_responses_total` - количество ответов по статус кодам
- `django_db_connections_total` - подключения к базе данных
- `django_cache_operations_total` - операции с кешем

### Кастомные метрики
- `django_user_registrations_total` - регистрации пользователей
- `django_user_logins_total` - логины пользователей
- `django_meme_uploads_total` - загрузки мемов
- `django_meme_views_total` - просмотры мемов
- `django_chat_messages_total` - сообщения в чате
- `django_feedback_submissions_total` - отправки обратной связи
- `django_request_duration_seconds` - время выполнения запросов
- `django_active_users` - количество активных пользователей
- `django_total_memes` - общее количество мемов
- `django_total_feedback` - общее количество обратной связи

## Обновление метрик

Для обновления метрик состояния системы:
```bash
docker-compose exec web python manage.py update_metrics
```

## Настройка Grafana

### 1. Добавление Prometheus как источника данных
- URL: `http://prometheus:9090`
- Access: Server (default)

### 2. Полезные запросы для дашбордов

#### Запросы в секунду
```
rate(django_http_requests_total[5m])
```

#### Среднее время ответа
```
rate(django_http_requests_latency_seconds_sum[5m]) / rate(django_http_requests_latency_seconds_count[5m])
```

#### Ошибки (4xx, 5xx)
```
rate(django_http_responses_total{status=~"4..|5.."}[5m])
```

#### Активные пользователи
```
django_active_users
```

#### Количество мемов
```
django_total_memes
```

## Алерты

Можно настроить алерты в Prometheus или Grafana для:
- Высокой нагрузки (больше 1000 запросов в минуту)
- Медленных ответов (больше 2 секунд)
- Высокого количества ошибок (больше 5% от всех запросов)
- Проблем с базой данных

## Переменные окружения

- `ENABLE_MONITORING` - включение/выключение мониторинга (по умолчанию: true)
- `PROMETHEUS_METRICS_EXPORT_PORT` - порт для экспорта метрик (по умолчанию: 8000)
- `PROMETHEUS_METRICS_EXPORT_ADDRESS` - адрес для экспорта метрик (по умолчанию: "")

## Troubleshooting

### Проблемы с метриками
1. Проверьте, что django-prometheus добавлен в INSTALLED_APPS
2. Убедитесь, что middleware добавлены в правильном порядке
3. Проверьте endpoint `/metrics` в браузере

### Проблемы с Prometheus
1. Проверьте конфигурацию в `prometheus.yml`
2. Убедитесь, что Django приложение доступно по адресу `web:8000`
3. Проверьте логи Prometheus: `docker-compose logs prometheus`

### Проблемы с Grafana
1. Проверьте подключение к Prometheus
2. Убедитесь, что URL источника данных правильный
3. Проверьте логи Grafana: `docker-compose logs grafana` 