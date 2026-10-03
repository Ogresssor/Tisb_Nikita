-- =====================================================================
-- База данных «Кинотеатр»
-- Курсовой проект по дисциплине «Базы данных». Этап 1
-- СУБД: SQLite (файл базы данных kinoteatr.db)
-- =====================================================================

PRAGMA foreign_keys = ON;

-- Справочник жанров
CREATE TABLE zhanr (
    id_zhanra INTEGER PRIMARY KEY AUTOINCREMENT,
    nazvanie  TEXT NOT NULL UNIQUE
);

-- Фильмы
CREATE TABLE film (
    id_filma           INTEGER PRIMARY KEY AUTOINCREMENT,
    nazvanie           TEXT    NOT NULL,
    rezhisser          TEXT,
    strana             TEXT,
    god_vypuska        INTEGER CHECK (god_vypuska BETWEEN 1895 AND 2100),
    dlitelnost_min     INTEGER NOT NULL CHECK (dlitelnost_min > 0),
    vozrastnoy_reyting TEXT    CHECK (vozrastnoy_reyting IN ('0+','6+','12+','16+','18+'))
);

-- Связующая таблица: разрешение связи «многие ко многим» между фильмами и жанрами
CREATE TABLE film_zhanr (
    id_filma  INTEGER NOT NULL REFERENCES film(id_filma)   ON DELETE CASCADE,
    id_zhanra INTEGER NOT NULL REFERENCES zhanr(id_zhanra) ON DELETE RESTRICT,
    PRIMARY KEY (id_filma, id_zhanra)
);

-- Залы кинотеатра
CREATE TABLE zal (
    id_zala            INTEGER PRIMARY KEY AUTOINCREMENT,
    nazvanie           TEXT    NOT NULL UNIQUE,
    kolichestvo_ryadov INTEGER NOT NULL CHECK (kolichestvo_ryadov > 0),
    mest_v_ryadu       INTEGER NOT NULL CHECK (mest_v_ryadu > 0),
    tip_zala           TEXT    NOT NULL CHECK (tip_zala IN ('2D','3D','IMAX','VIP')),
    -- вычисляемый столбец: общее количество мест в зале
    vsego_mest         INTEGER GENERATED ALWAYS AS (kolichestvo_ryadov * mest_v_ryadu) VIRTUAL
);

-- Сеансы
CREATE TABLE seans (
    id_seansa      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_filma       INTEGER NOT NULL REFERENCES film(id_filma) ON DELETE RESTRICT,
    id_zala        INTEGER NOT NULL REFERENCES zal(id_zala)   ON DELETE RESTRICT,
    data_seansa    TEXT    NOT NULL,
    vremya_nachala TEXT    NOT NULL,
    bazovaya_cena  REAL    NOT NULL CHECK (bazovaya_cena > 0),
    format_pokaza  TEXT    NOT NULL CHECK (format_pokaza IN ('2D','3D','IMAX')),
    UNIQUE (id_zala, data_seansa, vremya_nachala)
);

-- Клиенты (зарегистрированные покупатели)
CREATE TABLE klient (
    id_klienta       INTEGER PRIMARY KEY AUTOINCREMENT,
    familiya         TEXT NOT NULL,
    imya             TEXT NOT NULL,
    telefon          TEXT UNIQUE,
    email            TEXT,
    data_registracii TEXT NOT NULL,
    skidka_procent   REAL NOT NULL DEFAULT 0 CHECK (skidka_procent BETWEEN 0 AND 50)
);

-- Сотрудники кинотеатра
CREATE TABLE sotrudnik (
    id_sotrudnika INTEGER PRIMARY KEY AUTOINCREMENT,
    familiya      TEXT NOT NULL,
    imya          TEXT NOT NULL,
    dolzhnost     TEXT NOT NULL,
    telefon       TEXT,
    data_priema   TEXT NOT NULL
);

-- Билеты
CREATE TABLE bilet (
    id_bileta       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_seansa       INTEGER NOT NULL REFERENCES seans(id_seansa)         ON DELETE RESTRICT,
    id_klienta      INTEGER          REFERENCES klient(id_klienta)       ON DELETE SET NULL,
    id_sotrudnika   INTEGER NOT NULL REFERENCES sotrudnik(id_sotrudnika) ON DELETE RESTRICT,
    ryad            INTEGER NOT NULL CHECK (ryad > 0),
    mesto           INTEGER NOT NULL CHECK (mesto > 0),
    data_prodazhi   TEXT    NOT NULL,
    cena_bez_skidki REAL    NOT NULL CHECK (cena_bez_skidki > 0),
    skidka_procent  REAL    NOT NULL DEFAULT 0 CHECK (skidka_procent BETWEEN 0 AND 50),
    status          TEXT    NOT NULL DEFAULT 'продан'
                    CHECK (status IN ('продан','забронирован','возвращён')),
    -- вычисляемый столбец: итоговая цена билета с учётом скидки
    itogovaya_cena  REAL GENERATED ALWAYS AS
                    (ROUND(cena_bez_skidki * (1 - skidka_procent / 100.0), 2)) VIRTUAL,
    UNIQUE (id_seansa, ryad, mesto)
);

-- Индексы для ускорения поиска и отбора данных
CREATE INDEX idx_seans_data    ON seans(data_seansa);
CREATE INDEX idx_seans_film    ON seans(id_filma);
CREATE INDEX idx_seans_zal     ON seans(id_zala);
CREATE INDEX idx_bilet_seans   ON bilet(id_seansa);
CREATE INDEX idx_bilet_klient  ON bilet(id_klienta);
CREATE INDEX idx_bilet_sotr    ON bilet(id_sotrudnika);
CREATE INDEX idx_fz_zhanr      ON film_zhanr(id_zhanra);

-- Представление: расписание сеансов с названием фильма и зала
CREATE VIEW v_raspisanie AS
SELECT s.id_seansa,
       s.data_seansa,
       s.vremya_nachala,
       f.nazvanie AS film,
       f.dlitelnost_min,
       z.nazvanie AS zal,
       s.format_pokaza,
       s.bazovaya_cena
FROM seans s
JOIN film f ON f.id_filma = s.id_filma
JOIN zal  z ON z.id_zala  = s.id_zala;

-- Представление: сводка по сеансам — продано билетов, выручка, заполненность зала
CREATE VIEW v_seans_svodka AS
SELECT s.id_seansa,
       s.data_seansa,
       s.vremya_nachala,
       f.nazvanie AS film,
       z.nazvanie AS zal,
       z.vsego_mest,
       COUNT(b.id_bileta)                                   AS prodano_biletov,
       IFNULL(SUM(b.itogovaya_cena), 0)                     AS vyruchka,
       ROUND(100.0 * COUNT(b.id_bileta) / z.vsego_mest, 1)  AS zapolnennost_procent
FROM seans s
JOIN film f ON f.id_filma = s.id_filma
JOIN zal  z ON z.id_zala  = s.id_zala
LEFT JOIN bilet b ON b.id_seansa = s.id_seansa AND b.status = 'продан'
GROUP BY s.id_seansa, s.data_seansa, s.vremya_nachala, f.nazvanie, z.nazvanie, z.vsego_mest;
