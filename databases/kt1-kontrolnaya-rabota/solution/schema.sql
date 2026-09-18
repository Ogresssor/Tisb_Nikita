-- =====================================================================
-- База данных «Страховая компания»
-- Контрольная работа по дисциплине «Базы данных», КТ1
-- СУБД: PostgreSQL 14+
--
-- Примечание: отношение «Должность» реализовано таблицей job_position,
-- так как POSITION — зарезервированное слово стандарта SQL.
-- =====================================================================

DROP TABLE IF EXISTS payout, case_handling, insurance_case, payment,
                     insured_object, contract_coverage, contract,
                     insurance_type, client_company, client_individual,
                     client, employee, job_position, filial CASCADE;

-- --------------------------- Справочники ----------------------------

CREATE TABLE filial (                       -- Филиал
    branch_id   SERIAL       PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    city        VARCHAR(60)  NOT NULL,
    address     VARCHAR(200) NOT NULL,
    phone       VARCHAR(20),
    open_date   DATE         NOT NULL
);

CREATE TABLE job_position (                 -- Должность
    position_id SERIAL        PRIMARY KEY,
    title       VARCHAR(80)   NOT NULL UNIQUE,
    base_salary NUMERIC(10,2) NOT NULL CHECK (base_salary > 0)
);

CREATE TABLE insurance_type (               -- Вид страхования
    type_id     SERIAL       PRIMARY KEY,
    name        VARCHAR(80)  NOT NULL UNIQUE,
    category    VARCHAR(20)  NOT NULL
                CHECK (category IN ('личное','имущественное','ответственности')),
    base_rate   NUMERIC(6,4) NOT NULL CHECK (base_rate > 0 AND base_rate < 1),
    description TEXT
);

-- ---------------------------- Сотрудники ----------------------------

CREATE TABLE employee (                     -- Сотрудник
    employee_id    SERIAL      PRIMARY KEY,
    last_name      VARCHAR(60) NOT NULL,
    first_name     VARCHAR(60) NOT NULL,
    middle_name    VARCHAR(60),
    birth_date     DATE        NOT NULL,
    passport       CHAR(10)    NOT NULL UNIQUE,
    hire_date      DATE        NOT NULL,
    dismissal_date DATE,
    phone          VARCHAR(20),
    email          VARCHAR(80),
    branch_id      INT         NOT NULL REFERENCES filial(branch_id)      ON DELETE RESTRICT,
    position_id    INT         NOT NULL REFERENCES job_position(position_id) ON DELETE RESTRICT,
    manager_id     INT         REFERENCES employee(employee_id)           ON DELETE SET NULL,
    CHECK (dismissal_date IS NULL OR dismissal_date >= hire_date),
    CHECK (manager_id IS NULL OR manager_id <> employee_id)
);

-- ------------------------------ Клиенты -----------------------------

CREATE TABLE client (                       -- Клиент (родовая сущность)
    client_id   SERIAL       PRIMARY KEY,
    client_type CHAR(1)      NOT NULL CHECK (client_type IN ('F','J')),
    reg_date    DATE         NOT NULL DEFAULT CURRENT_DATE,
    phone       VARCHAR(20)  NOT NULL,
    email       VARCHAR(80),
    address     VARCHAR(200) NOT NULL
);

CREATE TABLE client_individual (            -- Физическое лицо (связь 1:1, PK = FK)
    client_id       INT         PRIMARY KEY REFERENCES client(client_id) ON DELETE CASCADE,
    last_name       VARCHAR(60) NOT NULL,
    first_name      VARCHAR(60) NOT NULL,
    middle_name     VARCHAR(60),
    birth_date      DATE        NOT NULL,
    passport_series CHAR(4)     NOT NULL,
    passport_number CHAR(6)     NOT NULL,
    UNIQUE (passport_series, passport_number)
);

CREATE TABLE client_company (               -- Юридическое лицо (связь 1:1, PK = FK)
    client_id    INT          PRIMARY KEY REFERENCES client(client_id) ON DELETE CASCADE,
    company_name VARCHAR(150) NOT NULL,
    inn          CHAR(10)     NOT NULL UNIQUE,
    kpp          CHAR(9),
    ogrn         CHAR(13),
    director     VARCHAR(120) NOT NULL
);

-- ------------------------------ Договоры ----------------------------

CREATE TABLE contract (                     -- Договор страхования
    contract_id     SERIAL        PRIMARY KEY,
    contract_number VARCHAR(20)   NOT NULL UNIQUE,
    sign_date       DATE          NOT NULL,
    start_date      DATE          NOT NULL,
    end_date        DATE          NOT NULL,
    premium         NUMERIC(12,2) NOT NULL CHECK (premium > 0),
    status          VARCHAR(12)   NOT NULL DEFAULT 'действует'
                    CHECK (status IN ('действует','завершён','расторгнут')),
    client_id       INT NOT NULL REFERENCES client(client_id)     ON DELETE RESTRICT,
    agent_id        INT NOT NULL REFERENCES employee(employee_id) ON DELETE RESTRICT,
    branch_id       INT NOT NULL REFERENCES filial(branch_id)     ON DELETE RESTRICT,
    CHECK (end_date > start_date),
    CHECK (sign_date <= start_date)
);

-- Разрешение связи М:М «договор ↔ вид страхования»
CREATE TABLE contract_coverage (            -- Покрытие по договору
    contract_id INT           NOT NULL REFERENCES contract(contract_id)      ON DELETE CASCADE,
    type_id     INT           NOT NULL REFERENCES insurance_type(type_id)    ON DELETE RESTRICT,
    insured_sum NUMERIC(14,2) NOT NULL CHECK (insured_sum > 0),
    rate        NUMERIC(6,4)  NOT NULL CHECK (rate > 0 AND rate < 1),
    franchise   NUMERIC(12,2) CHECK (franchise IS NULL OR franchise >= 0),
    PRIMARY KEY (contract_id, type_id)
);

CREATE TABLE insured_object (               -- Объект страхования
    object_id       SERIAL        PRIMARY KEY,
    contract_id     INT           NOT NULL REFERENCES contract(contract_id) ON DELETE CASCADE,
    object_kind     VARCHAR(20)   NOT NULL
                    CHECK (object_kind IN ('ТС','недвижимость','имущество','жизнь')),
    description     VARCHAR(200)  NOT NULL,
    appraised_value NUMERIC(14,2) NOT NULL CHECK (appraised_value > 0),
    object_ref      VARCHAR(40)
);

CREATE TABLE payment (                      -- Платёж (страховой взнос)
    payment_id    SERIAL        PRIMARY KEY,
    contract_id   INT           NOT NULL REFERENCES contract(contract_id) ON DELETE CASCADE,
    instalment_no SMALLINT      NOT NULL CHECK (instalment_no > 0),
    due_date      DATE          NOT NULL,
    paid_date     DATE,
    amount        NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    method        VARCHAR(20) CHECK (method IN ('наличные','карта','безналичный расчёт')),
    status        VARCHAR(12)   NOT NULL DEFAULT 'ожидается'
                  CHECK (status IN ('ожидается','оплачен','просрочен')),
    UNIQUE (contract_id, instalment_no),
    CHECK ((status = 'оплачен') = (paid_date IS NOT NULL))
);

-- -------------------------- Страховые случаи ------------------------

CREATE TABLE insurance_case (               -- Страховой случай
    case_id        SERIAL        PRIMARY KEY,
    contract_id    INT           NOT NULL,
    type_id        INT           NOT NULL,
    event_date     DATE          NOT NULL,
    report_date    DATE          NOT NULL,
    description    TEXT          NOT NULL,
    claimed_amount NUMERIC(14,2) NOT NULL CHECK (claimed_amount > 0),
    status         VARCHAR(20)   NOT NULL DEFAULT 'заявлен'
                   CHECK (status IN ('заявлен','на рассмотрении','признан','отказано')),
    CHECK (report_date >= event_date),
    -- случай наступает по конкретному покрытию договора (составной внешний ключ)
    FOREIGN KEY (contract_id, type_id)
        REFERENCES contract_coverage(contract_id, type_id) ON DELETE RESTRICT
);

-- Разрешение связи М:М «сотрудник ↔ страховой случай»
CREATE TABLE case_handling (                -- Урегулирование
    case_id     INT         NOT NULL REFERENCES insurance_case(case_id)  ON DELETE CASCADE,
    employee_id INT         NOT NULL REFERENCES employee(employee_id)    ON DELETE RESTRICT,
    role        VARCHAR(20) NOT NULL CHECK (role IN ('эксперт','оценщик','юрист')),
    assign_date DATE        NOT NULL,
    conclusion  TEXT,
    PRIMARY KEY (case_id, employee_id, role)
);

CREATE TABLE payout (                       -- Выплата
    payout_id   SERIAL        PRIMARY KEY,
    case_id     INT           NOT NULL REFERENCES insurance_case(case_id) ON DELETE RESTRICT,
    payout_date DATE          NOT NULL,
    amount      NUMERIC(14,2) NOT NULL CHECK (amount > 0),
    doc_number  VARCHAR(20)   NOT NULL
);

-- ------------------------------ Индексы -----------------------------

CREATE INDEX idx_employee_branch     ON employee(branch_id);
CREATE INDEX idx_employee_position   ON employee(position_id);
CREATE INDEX idx_employee_manager    ON employee(manager_id);
CREATE INDEX idx_contract_client     ON contract(client_id);
CREATE INDEX idx_contract_agent      ON contract(agent_id);
CREATE INDEX idx_contract_branch     ON contract(branch_id);
CREATE INDEX idx_contract_end_date   ON contract(end_date);
CREATE INDEX idx_contract_sign_date  ON contract(sign_date);
CREATE INDEX idx_coverage_type       ON contract_coverage(type_id);
CREATE INDEX idx_object_contract     ON insured_object(contract_id);
CREATE INDEX idx_payment_contract    ON payment(contract_id);
CREATE INDEX idx_payment_due         ON payment(status, due_date);
CREATE INDEX idx_case_contract       ON insurance_case(contract_id, type_id);
CREATE INDEX idx_case_event_date     ON insurance_case(event_date);
CREATE INDEX idx_handling_employee   ON case_handling(employee_id);
CREATE INDEX idx_payout_case         ON payout(case_id);

-- --------------------- Ограничения предметной области ---------------

-- Правило 6: клиент не может быть одновременно физическим и юридическим лицом
CREATE OR REPLACE FUNCTION trg_client_exclusive() RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'client_individual'
       AND EXISTS (SELECT 1 FROM client_company WHERE client_id = NEW.client_id) THEN
        RAISE EXCEPTION 'Клиент % уже зарегистрирован как юридическое лицо', NEW.client_id;
    END IF;
    IF TG_TABLE_NAME = 'client_company'
       AND EXISTS (SELECT 1 FROM client_individual WHERE client_id = NEW.client_id) THEN
        RAISE EXCEPTION 'Клиент % уже зарегистрирован как физическое лицо', NEW.client_id;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER chk_individual_exclusive BEFORE INSERT OR UPDATE ON client_individual
    FOR EACH ROW EXECUTE FUNCTION trg_client_exclusive();
CREATE TRIGGER chk_company_exclusive    BEFORE INSERT OR UPDATE ON client_company
    FOR EACH ROW EXECUTE FUNCTION trg_client_exclusive();

-- Правило 8: дата события должна попадать в срок действия договора
-- Правило 11: агент договора не должен быть уволен на дату заключения
CREATE OR REPLACE FUNCTION trg_case_in_contract_period() RETURNS TRIGGER AS $$
DECLARE d RECORD;
BEGIN
    SELECT start_date, end_date INTO d FROM contract WHERE contract_id = NEW.contract_id;
    IF NEW.event_date NOT BETWEEN d.start_date AND d.end_date THEN
        RAISE EXCEPTION 'Дата события % вне срока действия договора (% .. %)',
              NEW.event_date, d.start_date, d.end_date;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER chk_case_period BEFORE INSERT OR UPDATE ON insurance_case
    FOR EACH ROW EXECUTE FUNCTION trg_case_in_contract_period();

CREATE OR REPLACE FUNCTION trg_agent_active() RETURNS TRIGGER AS $$
DECLARE dd DATE;
BEGIN
    SELECT dismissal_date INTO dd FROM employee WHERE employee_id = NEW.agent_id;
    IF dd IS NOT NULL AND dd < NEW.sign_date THEN
        RAISE EXCEPTION 'Агент % уволен и не может заключать договор', NEW.agent_id;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER chk_agent_active BEFORE INSERT OR UPDATE ON contract
    FOR EACH ROW EXECUTE FUNCTION trg_agent_active();

-- Правило 9: выплата только по признанному страховому случаю
-- Правило 10: сумма выплат не превышает страховую сумму по договору
CREATE OR REPLACE FUNCTION trg_payout_allowed() RETURNS TRIGGER AS $$
DECLARE st TEXT; limit_sum NUMERIC; paid NUMERIC;
BEGIN
    SELECT ic.status INTO st FROM insurance_case ic WHERE ic.case_id = NEW.case_id;
    IF st <> 'признан' THEN
        RAISE EXCEPTION 'Выплата возможна только по признанному страховому случаю (статус: %)', st;
    END IF;
    SELECT cc.insured_sum INTO limit_sum
      FROM contract_coverage cc
      JOIN insurance_case ic ON ic.contract_id = cc.contract_id AND ic.type_id = cc.type_id
     WHERE ic.case_id = NEW.case_id;
    SELECT COALESCE(SUM(amount), 0) INTO paid FROM payout WHERE case_id = NEW.case_id;
    IF paid + NEW.amount > limit_sum THEN
        RAISE EXCEPTION 'Сумма выплат (%) превышает страховую сумму по покрытию (%)',
              paid + NEW.amount, limit_sum;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER chk_payout BEFORE INSERT ON payout
    FOR EACH ROW EXECUTE FUNCTION trg_payout_allowed();

-- ---------------------------- Представление -------------------------

CREATE OR REPLACE VIEW v_contract_totals AS
SELECT c.contract_id,
       c.contract_number,
       SUM(cc.insured_sum) AS total_insured_sum,
       c.premium,
       COALESCE((SELECT SUM(p.amount) FROM payment p
                  WHERE p.contract_id = c.contract_id AND p.status = 'оплачен'), 0) AS paid_amount
FROM contract c
JOIN contract_coverage cc ON cc.contract_id = c.contract_id
GROUP BY c.contract_id, c.contract_number, c.premium;
