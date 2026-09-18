-- =====================================================================
-- Заполнение БД «Страховая компания» информацией — экземпляр БД
-- Выполнять после schema.sql
-- =====================================================================

-- Филиалы
INSERT INTO filial (branch_id, name, city, address, phone, open_date) VALUES
 (1, 'Головной офис',      'Москва',          'ул. Тверская, 12', '+7 495 100-10-10', '2005-03-01'),
 (2, 'Филиал «Северный»',  'Санкт-Петербург', 'Невский пр., 84',  '+7 812 200-20-20', '2011-09-15');

-- Должности
INSERT INTO job_position (position_id, title, base_salary) VALUES
 (1, 'Директор филиала',   180000.00),
 (2, 'Страховой агент',     60000.00),
 (3, 'Эксперт по убыткам',  90000.00),
 (4, 'Юрист',               95000.00);

-- Сотрудники (manager_id — рекурсивная связь «руководитель — подчинённый»)
INSERT INTO employee (employee_id, last_name, first_name, middle_name, birth_date, passport,
                      hire_date, dismissal_date, phone, email, branch_id, position_id, manager_id) VALUES
 (1, 'Фёдоров',   'Игорь',   'Александрович', '1975-05-02', '4501123456', '2005-03-01', NULL,
     '+7 495 100-10-11', 'fedorov@insur.ru',  1, 1, NULL),
 (2, 'Смирнова',  'Анна',    'Сергеевна',     '1990-11-17', '4502234567', '2018-06-11', NULL,
     '+7 916 500-10-12', 'smirnova@insur.ru', 1, 2, 1),
 (3, 'Кузнецов',  'Павел',   'Олегович',      '1988-02-23', '4003345678', '2019-02-04', NULL,
     '+7 921 500-10-13', 'kuznecov@insur.ru', 2, 2, 1),
 (4, 'Волкова',   'Мария',   'Ивановна',      '1986-09-30', '4504456789', '2016-10-20', NULL,
     '+7 916 500-10-14', 'volkova@insur.ru',  1, 3, 1),
 (5, 'Орлов',     'Дмитрий', 'Петрович',      '1983-12-05', '4505567890', '2020-01-13', NULL,
     '+7 916 500-10-15', 'orlov@insur.ru',    1, 4, 1);

-- Клиенты: родовая сущность
INSERT INTO client (client_id, client_type, reg_date, phone, email, address) VALUES
 (1, 'F', '2021-04-05', '+7 916 111-22-33', 'ivanov@mail.ru',    'г. Москва, ул. Лесная, 5-17'),
 (2, 'F', '2022-08-19', '+7 921 222-33-44', 'petrova@mail.ru',   'г. Санкт-Петербург, пр. Науки, 3-40'),
 (3, 'J', '2020-11-30', '+7 495 333-44-55', 'info@logtrade.ru',  'г. Москва, Варшавское ш., 1');

-- Специализация 1:1 — физические лица
INSERT INTO client_individual (client_id, last_name, first_name, middle_name, birth_date,
                               passport_series, passport_number) VALUES
 (1, 'Иванов',  'Сергей', 'Петрович', '1985-07-12', '4510', '654321'),
 (2, 'Петрова', 'Ольга',  'Ивановна', '1992-03-26', '4012', '123987');

-- Специализация 1:1 — юридические лица
INSERT INTO client_company (client_id, company_name, inn, kpp, ogrn, director) VALUES
 (3, 'ООО «Логистик-Трейд»', '7701234567', '770101001', '1207700123456', 'Николаев А. В.');

-- Виды страхования
INSERT INTO insurance_type (type_id, name, category, base_rate, description) VALUES
 (1, 'ОСАГО',                        'ответственности', 0.0500, 'Обязательное страхование гражданской ответственности'),
 (2, 'КАСКО',                        'имущественное',   0.0700, 'Добровольное страхование транспортного средства'),
 (3, 'Страхование жизни и здоровья', 'личное',          0.0150, 'Страхование водителя и пассажиров'),
 (4, 'Страхование недвижимости',     'имущественное',   0.0040, 'Квартиры, дома, коммерческая недвижимость'),
 (5, 'Страхование грузов',           'имущественное',   0.0090, 'Страхование груза на время перевозки');

-- Договоры
INSERT INTO contract (contract_id, contract_number, sign_date, start_date, end_date,
                      premium, status, client_id, agent_id, branch_id) VALUES
 (1, 'ДС-2025-000101', '2025-01-15', '2025-01-16', '2026-01-15',  62500.00, 'действует', 1, 2, 1),
 (2, 'ДС-2025-000102', '2025-03-02', '2025-03-03', '2026-03-02',  18000.00, 'действует', 2, 3, 2),
 (3, 'ДС-2025-000103', '2025-05-20', '2025-06-01', '2026-05-31', 135000.00, 'действует', 3, 2, 1);

-- Покрытия — связующее отношение для связи М:М «договор ↔ вид страхования»
INSERT INTO contract_coverage (contract_id, type_id, insured_sum, rate, franchise) VALUES
 (1, 1,   400000.00, 0.0500, NULL),
 (1, 2,  1200000.00, 0.0350, 15000.00),
 (1, 3,   300000.00, 0.0150, NULL),
 (2, 4,  4500000.00, 0.0040, 10000.00),
 (3, 5, 15000000.00, 0.0090, 50000.00);

-- Объекты страхования
INSERT INTO insured_object (object_id, contract_id, object_kind, description, appraised_value, object_ref) VALUES
 (1, 1, 'ТС',           'Kia Rio, 2021 г. в.',              1200000.00, 'XWEHN412BM0012345'),
 (2, 1, 'жизнь',        'Иванов С. П., водитель',            300000.00, NULL),
 (3, 2, 'недвижимость', 'Квартира 62 м², пр. Науки, 3-40',  4500000.00, '78:36:0005001:1234'),
 (4, 3, 'имущество',    'Партия бытовой техники',          15000000.00, 'НАКЛ-4471');

-- Платежи (график взносов)
INSERT INTO payment (payment_id, contract_id, instalment_no, due_date, paid_date, amount, method, status) VALUES
 (1, 1, 1, '2025-01-16', '2025-01-16', 31250.00, 'карта',               'оплачен'),
 (2, 1, 2, '2025-07-16', '2025-07-14', 31250.00, 'карта',               'оплачен'),
 (3, 2, 1, '2025-03-03', '2025-03-03', 18000.00, 'наличные',            'оплачен'),
 (4, 3, 1, '2025-06-01', '2025-06-01', 67500.00, 'безналичный расчёт',  'оплачен'),
 (5, 3, 2, '2025-12-01', NULL,         67500.00, 'безналичный расчёт',  'ожидается');

-- Страховые случаи
INSERT INTO insurance_case (case_id, contract_id, type_id, event_date, report_date, description,
                            claimed_amount, status) VALUES
 (1, 1, 2, '2025-04-08', '2025-04-09', 'ДТП на ул. Профсоюзная, повреждены передний бампер и капот',
     145000.00, 'признан'),
 (2, 2, 4, '2025-07-22', '2025-07-23', 'Залив квартиры из вышерасположенного помещения',
     260000.00, 'на рассмотрении');

-- Урегулирование — связующее отношение для связи М:М «сотрудник ↔ страховой случай»
INSERT INTO case_handling (case_id, employee_id, role, assign_date, conclusion) VALUES
 (1, 4, 'эксперт', '2025-04-09', 'Повреждения соответствуют обстоятельствам ДТП, ущерб 130 000 руб.'),
 (1, 5, 'юрист',   '2025-04-10', 'Оснований для отказа нет'),
 (2, 4, 'эксперт', '2025-07-23', NULL);

-- Выплаты
INSERT INTO payout (payout_id, case_id, payout_date, amount, doc_number) VALUES
 (1, 1, '2025-04-25', 130000.00, 'ПП-00871');

-- Синхронизация счётчиков последовательностей после вставки явных идентификаторов
SELECT setval('filial_branch_id_seq',        (SELECT MAX(branch_id)   FROM filial));
SELECT setval('job_position_position_id_seq',(SELECT MAX(position_id) FROM job_position));
SELECT setval('employee_employee_id_seq',    (SELECT MAX(employee_id) FROM employee));
SELECT setval('client_client_id_seq',        (SELECT MAX(client_id)   FROM client));
SELECT setval('insurance_type_type_id_seq',  (SELECT MAX(type_id)     FROM insurance_type));
SELECT setval('contract_contract_id_seq',    (SELECT MAX(contract_id) FROM contract));
SELECT setval('insured_object_object_id_seq',(SELECT MAX(object_id)   FROM insured_object));
SELECT setval('payment_payment_id_seq',      (SELECT MAX(payment_id)  FROM payment));
SELECT setval('insurance_case_case_id_seq',  (SELECT MAX(case_id)     FROM insurance_case));
SELECT setval('payout_payout_id_seq',        (SELECT MAX(payout_id)   FROM payout));
