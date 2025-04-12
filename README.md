<div style="text-align: center;">

  C O N F E R E N C E - B A C K E N D

  Backend-сервис для мобильного приложения ComfortComfy

 [Mobile app](https://github.com/EgorSborschikov/comfort_confy/)

</div>

> [!IMPORTANT]
> Проект относится к типу "С окрытым исходным кодом" и не способен выдержать большую нагрузку!

> [!IMPORTANT]
> [Документация к REST API](http://127.0.0.1:8000/docs)

## Технологический стек:

![Python](https://img.shields.io/badge/-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

### API Frameworks:
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![WebSocket](https://img.shields.io/badge/-WebSocket-000000?style=for-the-badge&logo=websocket&logoColor=white)

### Валидация моделей:
![Pydantic](https://img.shields.io/badge/-Pydantic-306998?style=for-the-badge&logo=pydantic&logoColor=white)

### Менеджер пакетов:
![Poetry](https://img.shields.io/badge/-Poetry-60A5FA?style=for-the-badge&logo=poetry&logoColor=white)

## Прочие инструменты:

### Хранилище данных:
![Supabase](https://img.shields.io/badge/-Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)

### Контейнеризация:
![Docker](https://img.shields.io/badge/-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

### Тестирование API:
![Postman](https://img.shields.io/badge/-Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white)


## REST API:

Сервер для выполнение базовых операций с конференциями (создание, присоединение, покидание, список конференций, история конференций).

### Маршруты 

- [X] **/create_conference**: Создание конференции (название конференции, UUID автора);
- [X] **/join_conference{room_id}**: Присоединение к конференции (по идентификатору комнаты);
- [X] **/leave_conference{room_id}**: Покидание конференции (по идентификатору текущей комнаты);
- [X] **list_conferences?created_by**: Вывод списка конференций (фильтрация по UUID автора для истории созданных конференций);
- [X] **update_conference_name**: Обновление названия конференции(идентификатор комнаты, новое название);
- [X] **delete_conference**: удаление конференции (по идентификатору комнаты);

## WebSocket:

Сервер для обработки входящих потоков бинарных данных и последующей передачей обработнных данных в комнату конференции по сокету.

- [X] **ws://host:port/ws/{room_id}**: Конечная точка для обмена сообщениями в реальном времени

## Установка и запуск:

1. Для работы с сервером необходимо склонировать репозиторий с исходным кодом:
    ```shell
    git clone https://github.com/EgorSborschikov/conferences_backend

2. Необходимо создать проект реляционной базы данных в [Supabase](https://supabase.com) и создать базу данных;

3. В корневом каталоге склонированного проекта необходимо создать файл .env и записать в него данные о supabase_key (их можно посмотреть в инструкции по подключению для выбранной технологии или выполнив cURL-запрос по supabaseURL (В разделе Project Settings > General)):
    ``` shell
    curl -X GET '{supabaseUrl}/rest/v1/todos' \
    -H "apikey: {supabaseKey}" \
    -H "Authorization: Bearer {supabaseKey}" 
    ```

4. В Docker Engine запускаем контейнер с Backend:
    ```shell
    docker-compose --env-file server/conferences/.env -f server/docker/docker-compose.yml --project-directory server/conferences/ up --build
    ```