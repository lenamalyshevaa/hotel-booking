-- HotelBooking — схема БД (PostgreSQL 16)
-- DDL + ключевое ограничение на пересечение дат + тестовые данные
--
-- В приложении схему создают миграции Alembic (alembic upgrade head),
-- а тестовые данные с настоящими bcrypt-хэшами паролей загружает
-- python -m app.seed. Точный SQL миграций: alembic upgrade head --sql

-- CREATE DATABASE hotel_booking;  -- выполнить отдельно от остального скрипта
-- \c hotel_booking

-- Расширение для exclusion constraint (защита от двойного бронирования)
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Перечисления
CREATE TYPE user_role      AS ENUM ('guest', 'admin', 'manager');
CREATE TYPE booking_status AS ENUM ('pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled');
CREATE TYPE room_status    AS ENUM ('available', 'maintenance');
CREATE TYPE payment_method AS ENUM ('cash', 'card', 'transfer');

-- Таблицы
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(100) NOT NULL,
    phone         VARCHAR(20),
    role          user_role    NOT NULL DEFAULT 'guest',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE room_types (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(50)   NOT NULL UNIQUE,
    capacity        INT           NOT NULL CHECK (capacity > 0),
    price_per_night DECIMAL(10,2) NOT NULL CHECK (price_per_night >= 0),
    description     TEXT
);

CREATE TABLE rooms (
    id           SERIAL PRIMARY KEY,
    number       VARCHAR(10) NOT NULL UNIQUE,
    floor        INT         NOT NULL,
    room_type_id INT         NOT NULL REFERENCES room_types(id),
    status       room_status NOT NULL DEFAULT 'available'
);

CREATE TABLE bookings (
    id          SERIAL PRIMARY KEY,
    guest_id    INT            NOT NULL REFERENCES users(id),
    check_in    DATE           NOT NULL,
    check_out   DATE           NOT NULL,
    status      booking_status NOT NULL DEFAULT 'pending',
    total_price DECIMAL(10,2)  NOT NULL CHECK (total_price >= 0),
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (check_out > check_in)
);

-- Ассоциативная сущность (M:N bookings <-> rooms).
-- price_per_night — цена на момент брони (историчность, осознанная денормализация).
CREATE TABLE booking_rooms (
    id              SERIAL PRIMARY KEY,
    booking_id      INT           NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    room_id         INT           NOT NULL REFERENCES rooms(id),
    price_per_night DECIMAL(10,2) NOT NULL CHECK (price_per_night >= 0),
    UNIQUE (booking_id, room_id)
);

CREATE TABLE payments (
    id         SERIAL PRIMARY KEY,
    booking_id INT            NOT NULL REFERENCES bookings(id),
    amount     DECIMAL(10,2)  NOT NULL CHECK (amount > 0),
    paid_at    TIMESTAMPTZ    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    method     payment_method NOT NULL
);

-- Ключевое бизнес-ограничение
-- Нет двух АКТИВНЫХ броней одного номера с пересекающимися датами.
-- Интервал полуоткрытый [check_in, check_out): день выезда = день заезда следующего гостя.
-- Денормализованные колонки дат в booking_rooms поддерживаются триггером,
-- чтобы exclusion constraint работал на уровне "номер + интервал".
ALTER TABLE booking_rooms
    ADD COLUMN check_in  DATE,
    ADD COLUMN check_out DATE,
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;

CREATE OR REPLACE FUNCTION sync_booking_rooms_dates() RETURNS trigger AS $$
BEGIN
    IF TG_TABLE_NAME = 'booking_rooms' THEN
        SELECT b.check_in, b.check_out,
               b.status IN ('pending', 'confirmed', 'checked_in')
          INTO NEW.check_in, NEW.check_out, NEW.is_active
          FROM bookings b WHERE b.id = NEW.booking_id;
        RETURN NEW;
    ELSE  -- bookings: при смене статуса/дат обновляем строки booking_rooms
        UPDATE booking_rooms
           SET check_in  = NEW.check_in,
               check_out = NEW.check_out,
               is_active = NEW.status IN ('pending', 'confirmed', 'checked_in')
         WHERE booking_id = NEW.id;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_booking_rooms_sync
    BEFORE INSERT OR UPDATE ON booking_rooms
    FOR EACH ROW EXECUTE FUNCTION sync_booking_rooms_dates();

CREATE TRIGGER trg_bookings_sync
    AFTER UPDATE OF check_in, check_out, status ON bookings
    FOR EACH ROW EXECUTE FUNCTION sync_booking_rooms_dates();

-- Само ограничение: для активных строк интервалы дат одного номера не пересекаются
ALTER TABLE booking_rooms
    ADD CONSTRAINT no_overlapping_active_bookings
    EXCLUDE USING gist (
        room_id WITH =,
        daterange(check_in, check_out, '[)') WITH &&
    ) WHERE (is_active);

-- Индексы
CREATE INDEX idx_rooms_room_type_id      ON rooms(room_type_id);
CREATE INDEX idx_bookings_guest_id       ON bookings(guest_id);
CREATE INDEX idx_bookings_status         ON bookings(status);
CREATE INDEX idx_bookings_dates          ON bookings(check_in, check_out);
CREATE INDEX idx_booking_rooms_booking   ON booking_rooms(booking_id);
CREATE INDEX idx_booking_rooms_room      ON booking_rooms(room_id);
CREATE INDEX idx_payments_booking_id     ON payments(booking_id);

-- Тестовые данные (DML)
INSERT INTO users (email, password_hash, full_name, phone, role) VALUES
('manager@hotel.ru', '$2b$12$examplehashmanager000000000000000000000000000000000', 'Ирина Петрова',   '+7-900-111-00-01', 'manager'),
('admin@hotel.ru',   '$2b$12$examplehashadmin00000000000000000000000000000000000', 'Олег Смирнов',    '+7-900-111-00-02', 'admin'),
('ivanov@mail.ru',   '$2b$12$examplehashguest00000000000000000000000000000000001', 'Иван Иванов',     '+7-900-222-00-01', 'guest'),
('petrova@mail.ru',  '$2b$12$examplehashguest00000000000000000000000000000000002', 'Анна Петрова',    '+7-900-222-00-02', 'guest'),
('sidorov@mail.ru',  '$2b$12$examplehashguest00000000000000000000000000000000003', 'Пётр Сидоров',    '+7-900-222-00-03', 'guest');

INSERT INTO room_types (name, capacity, price_per_night, description) VALUES
('Стандарт',       2, 3500.00, 'Двухместный номер с одной большой или двумя раздельными кроватями'),
('Стандарт плюс',  3, 4500.00, 'Увеличенный номер с диваном, до 3 гостей'),
('Люкс',           2, 8000.00, 'Номер повышенной комфортности с гостиной зоной'),
('Семейный',       4, 6500.00, 'Два смежных помещения, до 4 гостей');

INSERT INTO rooms (number, floor, room_type_id, status) VALUES
('101', 1, 1, 'available'),
('102', 1, 1, 'available'),
('103', 1, 2, 'available'),
('201', 2, 1, 'available'),
('202', 2, 2, 'available'),
('203', 2, 4, 'available'),
('301', 3, 3, 'available'),
('302', 3, 3, 'maintenance'),
('303', 3, 4, 'available'),
('304', 3, 1, 'available');

-- Брони (guest_id: 3=Иванов, 4=Петрова, 5=Сидоров)
INSERT INTO bookings (guest_id, check_in, check_out, status, total_price) VALUES
(3, '2026-11-02', '2026-11-05', 'confirmed',  10500.00),  -- 3 ночи, Стандарт
(4, '2026-11-03', '2026-11-07', 'pending',    32000.00),  -- 4 ночи, Люкс
(5, '2026-11-05', '2026-11-06', 'confirmed',   3500.00),  -- заезд в день выезда Иванова — допустимо
(3, '2026-11-20', '2026-11-25', 'pending',    22500.00),  -- 5 ночей, Стандарт плюс
(4, '2026-10-10', '2026-10-12', 'checked_out', 9000.00),  -- прошлая завершённая
(5, '2026-10-15', '2026-10-18', 'cancelled',  10500.00);  -- отменённая: даты могут пересекаться с кем угодно

INSERT INTO booking_rooms (booking_id, room_id, price_per_night) VALUES
(1, 1, 3500.00),   -- Иванов, номер 101, 2–5 ноября
(2, 7, 8000.00),   -- Петрова, люкс 301, 3–7 ноября
(3, 1, 3500.00),   -- Сидоров, номер 101, 5–6 ноября (полуоткрытый интервал — конфликта нет)
(4, 5, 4500.00),   -- Иванов, номер 202, 20–25 ноября
(5, 5, 4500.00),   -- завершённая бронь Петровой, номер 202
(6, 4, 3500.00);   -- отменённая бронь Сидорова, is_active=false

INSERT INTO payments (booking_id, amount, method) VALUES
(1, 10500.00, 'card'),
(2, 16000.00, 'transfer'),  -- предоплата 50%
(3,  3500.00, 'cash'),
(5,  9000.00, 'card');

-- Проверка ограничения (должно упасть с ошибкой exclusion constraint):
-- INSERT INTO bookings (guest_id, check_in, check_out, status, total_price)
--   VALUES (4, '2026-11-03', '2026-11-04', 'pending', 3500.00);
-- INSERT INTO booking_rooms (booking_id, room_id, price_per_night) VALUES (7, 1, 3500.00);
