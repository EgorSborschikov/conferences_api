# Используемые библиотеки
Все используемые библиотеки находятся в файле pyproject.toml в разделе "[tool.poetry.dependencies]"

# Запуск сервера

    - Запуск Nginx:
    ```
    nginx -c /path/to/nginx.conf
    ```

    - Запуск серверной части из корневого каталога:
    ```
    uvicorn main:conferences.app --host 0.0.0.0 --port 8000
    ``` 

# Рекомендации

## Масштабирование:

    - Используйте Docker для контейнеризации

    - Добавьте балансировщик нагрузки (HAProxy)

    - Рассмотрите использование Kubernetes

## Безопасность:

    - Включите SSL для RTMP (rtmps)

    - Реализуйте JWT проверку в колбэках

    - Используйте Firebase App Check

## Оптимизация:

    - Добавьте CDN для медиапотоков

    - Реализуйте адаптивный битрейт

    - Используйте аппаратное ускорение на сервере

# Настройка Supabase:

    - Включите Realtime для таблиц

    - Настройте Row Level Security