### HotelBooking

Backend системы бронирования номеров отеля.

Система ведёт номерной фонд, ищет свободные номера на даты, оформляет брони и отслеживает их жизненный цикл (подтверждение, заселение, выселение, отмена), учитывает оплаты и строит отчёты. Двойное бронирование одного номера на пересекающиеся даты запрещено на уровне базы данных.

Техническое задание: [docs/TZ.md](docs/TZ.md)
ER-диаграмма: [docs/er/er-diagram.png](docs/er/er-diagram.png)

### Стек

| Слой | Технология |
| --- | --- |
| API | Python 3.12, FastAPI, Uvicorn |
| Доступ к данным | SQLAlchemy 2 (ORM), psycopg2 |
| Миграции | Alembic |
| СУБД | PostgreSQL 16 (+ расширение btree_gist) |
| Протоколы | HTTP/REST, WebSocket (этап 5) |

### Статус

- [x] Этап 1. ТЗ, ER-модель, SQL-схема
- [x] Этап 2. Каркас backend: конфигурация, пул соединений, ORM-модели, миграции, тестовые данные
- [x] Этап 3. CRUD API, Swagger, Postman-коллекция
- [ ] Этап 4. Бизнес-логика: поиск свободных номеров, брони и статусы, JWT и роли, отчёты
- [ ] Этап 5. WebSocket-уведомления, тесты
- [ ] Этап 6. Тесты устойчивости, CI, нагрузочный тест

### Структура проекта

```
hotel-booking/
├── app/
│   ├── main.py            точка входа FastAPI
│   ├── config.py          настройки из .env (pydantic-settings)
│   ├── database.py        engine с пулом соединений, сессии, get_db()
│   ├── seed.py            тестовые данные через ORM
│   ├── core/security.py   хэширование паролей (bcrypt)
│   ├── core/errors.py     ошибки предметной области (400, 404, 409)
│   ├── models/            ORM-модели: users, room_types, rooms, bookings, booking_rooms, payments
│   ├── schemas/           Pydantic-схемы: что API принимает и что возвращает
│   ├── routers/           HTTP-эндпоинты (контроллеры)
│   ├── services/          бизнес-логика и транзакции
│   └── repositories/      запросы к БД через ORM
├── alembic/versions/      миграции схемы БД
├── postman/               Postman-коллекция с тестами всех эндпоинтов
├── docs/
│   ├── TZ.md              техническое задание
│   ├── er/                ER-диаграмма (PNG, SVG, исходники Graphviz и DBML)
│   └── sql/               SQL-скрипт схемы и тестовых данных
├── docker-compose.yml     PostgreSQL + API одной командой
├── Dockerfile
├── requirements.txt
└── .env.example           шаблон настроек (сам .env в Git не попадает)
```

### Запуск локально

Нужны Python 3.12+ и PostgreSQL 16.

**1. Окружение и зависимости**

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. База данных** (один раз)

```bash
psql -U postgres -c "CREATE USER hotel WITH PASSWORD 'hotel';"
psql -U postgres -c "CREATE DATABASE hotel_booking OWNER hotel;"
```

**3. Настройки**

```bash
cp .env.example .env            # Windows: copy .env.example .env
```

**4. Схема и тестовые данные**

```bash
alembic upgrade head            # создать таблицы
python -m app.seed              # заполнить тестовыми данными
```

**5. Сервер**

```bash
uvicorn app.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Проверка БД: http://localhost:8000/health

### Запуск в Docker

```bash
docker compose up --build                       # PostgreSQL + API, миграции применяются сами
docker compose exec api python -m app.seed      # тестовые данные
```

PostgreSQL из Docker проброшен на порт **5433**, чтобы не конфликтовать с локальной установкой. Подключиться к нему из DBeaver/pgAdmin: `localhost:5433`, база `hotel_booking`, пользователь и пароль `hotel`.

### API

Полная документация с возможностью отправлять запросы: http://localhost:8000/docs

| Ресурс | Эндпоинты |
| --- | --- |
| Категории номеров | `POST /room-types`, `GET /room-types`, `GET /room-types/{id}`, `PUT /room-types/{id}`, `PATCH /room-types/{id}`, `DELETE /room-types/{id}` |
| Номера | `POST /rooms`, `GET /rooms`, `GET /rooms/{id}`, `PUT /rooms/{id}`, `PATCH /rooms/{id}`, `DELETE /rooms/{id}` |
| Пользователи | `POST /users`, `GET /users`, `GET /users/{id}`, `PUT /users/{id}`, `PATCH /users/{id}`, `DELETE /users/{id}` |
| Служебные | `GET /`, `GET /health` |

Списки поддерживают пагинацию `skip` и `limit` (не больше 100), номера фильтруются по `room_type_id`, `status` и `floor`, пользователи по `role`. PUT заменяет объект целиком, PATCH меняет только присланные поля.

Код устроен по слоям Controller → Service → Repository: роутер принимает HTTP-запрос и проверяет формат данных, сервис применяет бизнес-правила и управляет транзакцией, репозиторий выполняет запросы к БД.

| Код | Когда |
| --- | --- |
| 200, 201, 204 | Успешное чтение или изменение, создание, удаление |
| 400 | Нарушено бизнес-правило: занятое название, номер или email, несуществующая категория |
| 404 | Объект с таким id не найден |
| 409 | Удаление нарушит целостность: у категории есть номера, у номера или пользователя есть брони |
| 422 | Данные не прошли проверку схемы: неверный тип, пустое поле, отрицательная цена, некорректный email |

#### Postman

Коллекция `postman/HotelBooking.postman_collection.json`: 34 запроса с проверками, включая граничные случаи и ошибки. Импорт: Postman → Import → выбрать файл, затем Run collection. Запросы выполняются по порядку, созданные объекты удаляются в конце, поэтому коллекцию можно прогонять сколько угодно раз. Нужны запущенный сервер и тестовые данные.

Из командной строки: `npx newman run postman/HotelBooking.postman_collection.json`

### Тестовые пользователи

Пароль у всех: `Password123!`

| Email | Роль |
| --- | --- |
| manager@hotel.ru | менеджер |
| admin@hotel.ru, admin2@hotel.ru | администратор |
| ivanov@mail.ru, petrova@mail.ru, sidorov@mail.ru и ещё 7 | гость |

Тестовые данные: 13 пользователей, 6 категорий, 20 номеров (2 на ремонте), 16 броней во всех статусах (даты считаются от текущего дня), 11 оплат. Перезаполнить: `python -m app.seed --reset`.

### Защита от двойного бронирования

Таблица `booking_rooms` содержит exclusion constraint:

```sql
EXCLUDE USING gist (room_id WITH =, daterange(check_in, check_out, '[)') WITH &&)
WHERE (is_active)
```

Для активных броней (ожидает, подтверждена, заселён) один номер не может иметь пересекающиеся интервалы дат. Интервал полуоткрытый, поэтому выезд одного гостя и заезд другого в один день допустимы. Даты и признак активности копирует в `booking_rooms` триггер, подробности в `alembic/versions/0001_initial_schema.py`.

Проверка в psql или DBeaver на тестовых данных: номер 101 занят подтверждённой бронью с послезавтра на 3 ночи, пробуем пересекающуюся бронь.

```sql
BEGIN;
INSERT INTO bookings (guest_id, check_in, check_out, status, total_price)
VALUES (13, CURRENT_DATE + 3, CURRENT_DATE + 4, 'pending', 2500);

INSERT INTO booking_rooms (booking_id, room_id, price_per_night)
VALUES (currval('bookings_id_seq'), 1, 2500);
-- ERROR: conflicting key value violates exclusion constraint "no_overlapping_active_bookings"
ROLLBACK;
```

Ограничение срабатывает и при одновременных запросах: вторая транзакция ждёт первую и получает отказ, поэтому гонка двух клиентов за один номер невозможна.

### Миграции

```bash
alembic upgrade head                                  # применить все
alembic downgrade -1                                  # откатить последнюю
alembic revision --autogenerate -m "описание"         # новая миграция по изменениям моделей
alembic check                                         # совпадают ли модели и БД
alembic upgrade head --sql                            # показать SQL, не выполняя
```
