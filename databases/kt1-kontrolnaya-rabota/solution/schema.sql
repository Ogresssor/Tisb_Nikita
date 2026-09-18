-- Создание таблиц базы данных «Страховая компания»

CREATE TABLE filial (
    id_filiala INT PRIMARY KEY,
    nazvanie   VARCHAR(100) NOT NULL,
    gorod      VARCHAR(50)  NOT NULL,
    adres      VARCHAR(150),
    telefon    VARCHAR(20)
);

CREATE TABLE dolzhnost (
    id_dolzhnosti INT PRIMARY KEY,
    nazvanie      VARCHAR(50) NOT NULL,
    oklad         DECIMAL(10,2)
);

CREATE TABLE sotrudnik (
    id_sotrudnika   INT PRIMARY KEY,
    familiya        VARCHAR(50) NOT NULL,
    imya            VARCHAR(50) NOT NULL,
    otchestvo       VARCHAR(50),
    data_rozhdeniya DATE,
    telefon         VARCHAR(20),
    data_priema     DATE,
    id_filiala      INT REFERENCES filial(id_filiala),
    id_dolzhnosti   INT REFERENCES dolzhnost(id_dolzhnosti)
);

CREATE TABLE klient (
    id_klienta  INT PRIMARY KEY,
    tip_klienta VARCHAR(10) NOT NULL,
    nazvanie    VARCHAR(150) NOT NULL,
    dokument    VARCHAR(20),
    telefon     VARCHAR(20),
    adres       VARCHAR(150)
);

CREATE TABLE vid_strahovaniya (
    id_vida  INT PRIMARY KEY,
    nazvanie VARCHAR(80) NOT NULL,
    tarif    DECIMAL(5,4) NOT NULL
);

CREATE TABLE dogovor (
    id_dogovora        INT PRIMARY KEY,
    nomer              VARCHAR(20) NOT NULL UNIQUE,
    data_zaklyucheniya DATE NOT NULL,
    data_nachala       DATE NOT NULL,
    data_okonchaniya   DATE NOT NULL,
    premiya            DECIMAL(10,2) NOT NULL,
    status             VARCHAR(15) NOT NULL,
    id_klienta         INT REFERENCES klient(id_klienta),
    id_sotrudnika      INT REFERENCES sotrudnik(id_sotrudnika),
    id_filiala         INT REFERENCES filial(id_filiala),
    CHECK (data_okonchaniya > data_nachala),
    CHECK (premiya > 0)
);

CREATE TABLE pokrytie (
    id_dogovora      INT REFERENCES dogovor(id_dogovora),
    id_vida          INT REFERENCES vid_strahovaniya(id_vida),
    strahovaya_summa DECIMAL(12,2) NOT NULL,
    tarif            DECIMAL(5,4) NOT NULL,
    PRIMARY KEY (id_dogovora, id_vida)
);

CREATE TABLE platezh (
    id_platezha   INT PRIMARY KEY,
    id_dogovora   INT REFERENCES dogovor(id_dogovora),
    data_platezha DATE NOT NULL,
    summa         DECIMAL(10,2) NOT NULL,
    sposob        VARCHAR(20)
);

CREATE TABLE sluchay (
    id_sluchaya      INT PRIMARY KEY,
    id_dogovora      INT REFERENCES dogovor(id_dogovora),
    data_sobytiya    DATE NOT NULL,
    opisanie         VARCHAR(200),
    summa_ushcherba  DECIMAL(12,2),
    status           VARCHAR(20) NOT NULL,
    id_sotrudnika    INT REFERENCES sotrudnik(id_sotrudnika)
);

CREATE TABLE vyplata (
    id_vyplaty  INT PRIMARY KEY,
    id_sluchaya INT REFERENCES sluchay(id_sluchaya),
    data_vyplaty DATE NOT NULL,
    summa       DECIMAL(12,2) NOT NULL
);
