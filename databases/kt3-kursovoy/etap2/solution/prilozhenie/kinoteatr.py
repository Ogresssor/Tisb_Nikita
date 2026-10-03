# -*- coding: utf-8 -*-
"""
Информационная система «Кинотеатр»
Курсовой проект по дисциплине «Базы данных»

Приложение для работы с базой данных кинотеатра.
СУБД: SQLite, файл базы данных kinoteatr.db лежит рядом с программой.
Интерфейс: библиотека tkinter (входит в стандартную поставку Python).

Запуск:  python kinoteatr.py
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

PAPKA = os.path.dirname(os.path.abspath(__file__))
FAYL_BD = os.path.join(PAPKA, 'kinoteatr.db')
SKRIPT_STRUKTURY = os.path.join(PAPKA, 'kino_schema.sql')
SKRIPT_DANNYH = os.path.join(PAPKA, 'kino_dannye.sql')


# ======================================================================
#  Работа с базой данных
# ======================================================================

class BazaDannyh:
    """Класс отвечает за подключение к базе данных и выполнение запросов."""

    def __init__(self, fayl):
        self.novaya = not os.path.exists(fayl)
        self.con = sqlite3.connect(fayl)
        self.con.row_factory = sqlite3.Row
        self.con.execute('PRAGMA foreign_keys = ON')
        if self.novaya:
            self.sozdat_bazu()

    def sozdat_bazu(self):
        """Если файла базы нет, создаём таблицы и заполняем их данными."""
        for skript in (SKRIPT_STRUKTURY, SKRIPT_DANNYH):
            if os.path.exists(skript):
                with open(skript, encoding='utf-8') as f:
                    self.con.executescript(f.read())
        self.con.commit()

    def vybrat(self, sql, parametry=()):
        """Выполнить запрос на выборку и вернуть список строк."""
        return self.con.execute(sql, parametry).fetchall()

    def vypolnit(self, sql, parametry=()):
        """Выполнить запрос на изменение данных (INSERT, UPDATE, DELETE)."""
        kursor = self.con.execute(sql, parametry)
        self.con.commit()
        return kursor.lastrowid

    def zakryt(self):
        self.con.close()


# ======================================================================
#  Универсальная вкладка-справочник
# ======================================================================

class VkladkaSpravochnik(ttk.Frame):
    """Вкладка для работы с одной таблицей: просмотр, поиск, добавление,
    изменение и удаление записей."""

    def __init__(self, roditel, bd, tablica, klyuch, polya, zagolovki,
                 polya_poiska, shiriny=None):
        super().__init__(roditel, padding=8)
        self.bd = bd
        self.tablica = tablica
        self.klyuch = klyuch              # имя поля первичного ключа
        self.polya = polya                # поля, которые вводит пользователь
        self.zagolovki = zagolovki        # подписи полей на русском
        self.polya_poiska = polya_poiska  # по каким полям работает поиск
        self.shiriny = shiriny or {}
        self.vybrannyy_id = None

        self.sozdat_panel_poiska()
        self.sozdat_tablicu()
        self.sozdat_formu()
        self.obnovit()

    # ---------- создание элементов окна ----------

    def sozdat_panel_poiska(self):
        panel = ttk.Frame(self)
        panel.pack(fill='x', pady=(0, 6))
        ttk.Label(panel, text='Поиск:').pack(side='left')
        self.pole_poiska = ttk.Entry(panel, width=30)
        self.pole_poiska.pack(side='left', padx=5)
        self.pole_poiska.bind('<Return>', lambda e: self.obnovit())
        ttk.Button(panel, text='Найти', command=self.obnovit).pack(side='left')
        ttk.Button(panel, text='Показать все',
                   command=self.sbrosit_poisk).pack(side='left', padx=5)

    def sozdat_tablicu(self):
        ramka = ttk.Frame(self)
        ramka.pack(fill='both', expand=True)
        stolbcy = [self.klyuch] + self.polya
        self.tablica_vid = ttk.Treeview(ramka, columns=stolbcy,
                                        show='headings', height=12)
        for stolbec in stolbcy:
            podpis = 'Код' if stolbec == self.klyuch else self.zagolovki[stolbec]
            self.tablica_vid.heading(stolbec, text=podpis)
            self.tablica_vid.column(stolbec, width=self.shiriny.get(stolbec, 120),
                                    anchor='w')
        polosa = ttk.Scrollbar(ramka, orient='vertical',
                               command=self.tablica_vid.yview)
        self.tablica_vid.configure(yscrollcommand=polosa.set)
        self.tablica_vid.pack(side='left', fill='both', expand=True)
        polosa.pack(side='right', fill='y')
        self.tablica_vid.bind('<<TreeviewSelect>>', self.vybrat_zapis)

    def sozdat_formu(self):
        forma = ttk.LabelFrame(self, text='Запись', padding=8)
        forma.pack(fill='x', pady=8)
        self.vvod = {}
        for nomer, pole in enumerate(self.polya):
            stroka, stolbec = divmod(nomer, 3)
            ttk.Label(forma, text=self.zagolovki[pole] + ':').grid(
                row=stroka, column=stolbec * 2, sticky='e', padx=4, pady=3)
            entry = ttk.Entry(forma, width=24)
            entry.grid(row=stroka, column=stolbec * 2 + 1, padx=4, pady=3)
            self.vvod[pole] = entry

        knopki = ttk.Frame(self)
        knopki.pack(fill='x')
        ttk.Button(knopki, text='Добавить', command=self.dobavit).pack(side='left')
        ttk.Button(knopki, text='Изменить', command=self.izmenit).pack(side='left', padx=5)
        ttk.Button(knopki, text='Удалить', command=self.udalit).pack(side='left')
        ttk.Button(knopki, text='Очистить поля', command=self.ochistit).pack(side='left', padx=5)

    # ---------- работа с данными ----------

    def obnovit(self):
        """Заполнить таблицу записями с учётом строки поиска."""
        tekst = self.pole_poiska.get().strip()
        sql = f'SELECT {self.klyuch}, {", ".join(self.polya)} FROM {self.tablica}'
        parametry = ()
        if tekst:
            usloviya = ' OR '.join(f'{p} LIKE ?' for p in self.polya_poiska)
            sql += ' WHERE ' + usloviya
            parametry = tuple(f'%{tekst}%' for _ in self.polya_poiska)
        sql += f' ORDER BY {self.klyuch}'
        self.tablica_vid.delete(*self.tablica_vid.get_children())
        for stroka in self.bd.vybrat(sql, parametry):
            self.tablica_vid.insert('', 'end', values=tuple(stroka))

    def sbrosit_poisk(self):
        self.pole_poiska.delete(0, 'end')
        self.obnovit()

    def vybrat_zapis(self, sobytie=None):
        """При выборе строки в таблице её значения попадают в поля ввода."""
        vydelenie = self.tablica_vid.selection()
        if not vydelenie:
            return
        znacheniya = self.tablica_vid.item(vydelenie[0])['values']
        self.vybrannyy_id = znacheniya[0]
        for nomer, pole in enumerate(self.polya, start=1):
            self.vvod[pole].delete(0, 'end')
            self.vvod[pole].insert(0, znacheniya[nomer])

    def ochistit(self):
        self.vybrannyy_id = None
        for entry in self.vvod.values():
            entry.delete(0, 'end')
        self.tablica_vid.selection_remove(self.tablica_vid.selection())

    def sobrat_znacheniya(self):
        return [self.vvod[p].get().strip() or None for p in self.polya]

    def dobavit(self):
        znacheniya = self.sobrat_znacheniya()
        if not znacheniya[0]:
            messagebox.showwarning('Внимание', 'Заполните хотя бы первое поле.')
            return
        voprosy = ', '.join('?' for _ in self.polya)
        sql = f'INSERT INTO {self.tablica} ({", ".join(self.polya)}) VALUES ({voprosy})'
        try:
            self.bd.vypolnit(sql, tuple(znacheniya))
        except sqlite3.IntegrityError as oshibka:
            messagebox.showerror('Ошибка', f'Запись не добавлена:\n{oshibka}')
            return
        self.ochistit()
        self.obnovit()

    def izmenit(self):
        if self.vybrannyy_id is None:
            messagebox.showwarning('Внимание', 'Сначала выберите запись в таблице.')
            return
        prisvoeniya = ', '.join(f'{p} = ?' for p in self.polya)
        sql = f'UPDATE {self.tablica} SET {prisvoeniya} WHERE {self.klyuch} = ?'
        try:
            self.bd.vypolnit(sql, tuple(self.sobrat_znacheniya()) + (self.vybrannyy_id,))
        except sqlite3.IntegrityError as oshibka:
            messagebox.showerror('Ошибка', f'Запись не изменена:\n{oshibka}')
            return
        self.obnovit()

    def udalit(self):
        if self.vybrannyy_id is None:
            messagebox.showwarning('Внимание', 'Сначала выберите запись в таблице.')
            return
        if not messagebox.askyesno('Удаление', 'Удалить выбранную запись?'):
            return
        try:
            self.bd.vypolnit(f'DELETE FROM {self.tablica} WHERE {self.klyuch} = ?',
                             (self.vybrannyy_id,))
        except sqlite3.IntegrityError:
            messagebox.showerror(
                'Ошибка',
                'Запись удалить нельзя: на неё ссылаются записи других таблиц.')
            return
        self.ochistit()
        self.obnovit()


# ======================================================================
#  Вкладка «Сеансы»
# ======================================================================

class VkladkaSeansy(ttk.Frame):
    """Расписание сеансов. Фильм и зал выбираются из выпадающих списков,
    поэтому ошибиться с кодом нельзя."""

    def __init__(self, roditel, bd):
        super().__init__(roditel, padding=8)
        self.bd = bd
        self.vybrannyy_id = None

        panel = ttk.Frame(self)
        panel.pack(fill='x', pady=(0, 6))
        ttk.Label(panel, text='Дата (ГГГГ-ММ-ДД):').pack(side='left')
        self.pole_daty = ttk.Entry(panel, width=14)
        self.pole_daty.pack(side='left', padx=5)
        ttk.Button(panel, text='Показать расписание',
                   command=self.obnovit).pack(side='left')
        ttk.Button(panel, text='Все сеансы',
                   command=self.pokazat_vse).pack(side='left', padx=5)

        stolbcy = ('id', 'data', 'vremya', 'film', 'zal', 'format', 'cena', 'mest')
        podpisi = ('Код', 'Дата', 'Время', 'Фильм', 'Зал', 'Формат',
                   'Цена, руб.', 'Мест в зале')
        shiriny = (50, 90, 70, 230, 110, 80, 90, 95)
        self.tablica_vid = ttk.Treeview(self, columns=stolbcy, show='headings', height=12)
        for stolbec, podpis, shirina in zip(stolbcy, podpisi, shiriny):
            self.tablica_vid.heading(stolbec, text=podpis)
            self.tablica_vid.column(stolbec, width=shirina, anchor='w')
        self.tablica_vid.pack(fill='both', expand=True)
        self.tablica_vid.bind('<<TreeviewSelect>>', self.vybrat_zapis)

        forma = ttk.LabelFrame(self, text='Сеанс', padding=8)
        forma.pack(fill='x', pady=8)

        ttk.Label(forma, text='Фильм:').grid(row=0, column=0, sticky='e', padx=4, pady=3)
        self.spisok_filmov = ttk.Combobox(forma, width=38, state='readonly')
        self.spisok_filmov.grid(row=0, column=1, padx=4, pady=3)

        ttk.Label(forma, text='Зал:').grid(row=0, column=2, sticky='e', padx=4, pady=3)
        self.spisok_zalov = ttk.Combobox(forma, width=24, state='readonly')
        self.spisok_zalov.grid(row=0, column=3, padx=4, pady=3)

        ttk.Label(forma, text='Дата:').grid(row=1, column=0, sticky='e', padx=4, pady=3)
        self.vvod_data = ttk.Entry(forma, width=38)
        self.vvod_data.grid(row=1, column=1, padx=4, pady=3)

        ttk.Label(forma, text='Время:').grid(row=1, column=2, sticky='e', padx=4, pady=3)
        self.vvod_vremya = ttk.Entry(forma, width=24)
        self.vvod_vremya.grid(row=1, column=3, padx=4, pady=3)

        ttk.Label(forma, text='Цена, руб.:').grid(row=2, column=0, sticky='e', padx=4, pady=3)
        self.vvod_cena = ttk.Entry(forma, width=38)
        self.vvod_cena.grid(row=2, column=1, padx=4, pady=3)

        ttk.Label(forma, text='Формат:').grid(row=2, column=2, sticky='e', padx=4, pady=3)
        self.spisok_formatov = ttk.Combobox(forma, width=24, state='readonly',
                                            values=('2D', '3D', 'IMAX'))
        self.spisok_formatov.grid(row=2, column=3, padx=4, pady=3)

        knopki = ttk.Frame(self)
        knopki.pack(fill='x')
        ttk.Button(knopki, text='Добавить сеанс', command=self.dobavit).pack(side='left')
        ttk.Button(knopki, text='Изменить', command=self.izmenit).pack(side='left', padx=5)
        ttk.Button(knopki, text='Удалить', command=self.udalit).pack(side='left')
        ttk.Button(knopki, text='Очистить поля', command=self.ochistit).pack(side='left', padx=5)

        self.zagruzit_spiski()
        self.obnovit()

    def zagruzit_spiski(self):
        self.filmy = self.bd.vybrat('SELECT id_filma, nazvanie FROM film ORDER BY nazvanie')
        self.zaly = self.bd.vybrat('SELECT id_zala, nazvanie FROM zal ORDER BY nazvanie')
        self.spisok_filmov['values'] = [f'{r["id_filma"]} — {r["nazvanie"]}' for r in self.filmy]
        self.spisok_zalov['values'] = [f'{r["id_zala"]} — {r["nazvanie"]}' for r in self.zaly]

    def obnovit(self):
        data = self.pole_daty.get().strip()
        sql = ('SELECT s.id_seansa, s.data_seansa, s.vremya_nachala, f.nazvanie, '
               '       z.nazvanie, s.format_pokaza, s.bazovaya_cena, z.vsego_mest '
               'FROM seans s '
               'JOIN film f ON f.id_filma = s.id_filma '
               'JOIN zal  z ON z.id_zala  = s.id_zala ')
        parametry = ()
        if data:
            sql += 'WHERE s.data_seansa = ? '
            parametry = (data,)
        sql += 'ORDER BY s.data_seansa, s.vremya_nachala'
        self.tablica_vid.delete(*self.tablica_vid.get_children())
        for stroka in self.bd.vybrat(sql, parametry):
            self.tablica_vid.insert('', 'end', values=tuple(stroka))

    def pokazat_vse(self):
        self.pole_daty.delete(0, 'end')
        self.obnovit()

    def vybrat_zapis(self, sobytie=None):
        vydelenie = self.tablica_vid.selection()
        if not vydelenie:
            return
        znacheniya = self.tablica_vid.item(vydelenie[0])['values']
        self.vybrannyy_id = znacheniya[0]
        stroka = self.bd.vybrat('SELECT * FROM seans WHERE id_seansa = ?',
                                (self.vybrannyy_id,))[0]
        self.ustanovit_spisok(self.spisok_filmov, self.filmy, 'id_filma', stroka['id_filma'])
        self.ustanovit_spisok(self.spisok_zalov, self.zaly, 'id_zala', stroka['id_zala'])
        self.vvod_data.delete(0, 'end'); self.vvod_data.insert(0, stroka['data_seansa'])
        self.vvod_vremya.delete(0, 'end'); self.vvod_vremya.insert(0, stroka['vremya_nachala'])
        self.vvod_cena.delete(0, 'end'); self.vvod_cena.insert(0, stroka['bazovaya_cena'])
        self.spisok_formatov.set(stroka['format_pokaza'])

    @staticmethod
    def ustanovit_spisok(spisok, dannye, pole_koda, kod):
        for nomer, stroka in enumerate(dannye):
            if stroka[pole_koda] == kod:
                spisok.current(nomer)
                return

    def ochistit(self):
        self.vybrannyy_id = None
        self.spisok_filmov.set(''); self.spisok_zalov.set(''); self.spisok_formatov.set('')
        for pole in (self.vvod_data, self.vvod_vremya, self.vvod_cena):
            pole.delete(0, 'end')

    def sobrat_dannye(self):
        if not self.spisok_filmov.get() or not self.spisok_zalov.get():
            messagebox.showwarning('Внимание', 'Выберите фильм и зал.')
            return None
        try:
            cena = float(self.vvod_cena.get().replace(',', '.'))
        except ValueError:
            messagebox.showwarning('Внимание', 'Цена должна быть числом.')
            return None
        return (int(self.spisok_filmov.get().split(' — ')[0]),
                int(self.spisok_zalov.get().split(' — ')[0]),
                self.vvod_data.get().strip(),
                self.vvod_vremya.get().strip(),
                cena,
                self.spisok_formatov.get() or '2D')

    def dobavit(self):
        dannye = self.sobrat_dannye()
        if not dannye:
            return
        try:
            self.bd.vypolnit(
                'INSERT INTO seans (id_filma, id_zala, data_seansa, vremya_nachala, '
                'bazovaya_cena, format_pokaza) VALUES (?, ?, ?, ?, ?, ?)', dannye)
        except sqlite3.IntegrityError as oshibka:
            messagebox.showerror(
                'Ошибка',
                'Сеанс не добавлен. Возможно, в этом зале на это время уже назначен '
                f'другой сеанс.\n\n{oshibka}')
            return
        self.ochistit()
        self.obnovit()

    def izmenit(self):
        if self.vybrannyy_id is None:
            messagebox.showwarning('Внимание', 'Сначала выберите сеанс в таблице.')
            return
        dannye = self.sobrat_dannye()
        if not dannye:
            return
        try:
            self.bd.vypolnit(
                'UPDATE seans SET id_filma = ?, id_zala = ?, data_seansa = ?, '
                'vremya_nachala = ?, bazovaya_cena = ?, format_pokaza = ? '
                'WHERE id_seansa = ?', dannye + (self.vybrannyy_id,))
        except sqlite3.IntegrityError as oshibka:
            messagebox.showerror('Ошибка', f'Сеанс не изменён:\n{oshibka}')
            return
        self.obnovit()

    def udalit(self):
        if self.vybrannyy_id is None:
            messagebox.showwarning('Внимание', 'Сначала выберите сеанс в таблице.')
            return
        if not messagebox.askyesno('Удаление', 'Удалить выбранный сеанс?'):
            return
        try:
            self.bd.vypolnit('DELETE FROM seans WHERE id_seansa = ?', (self.vybrannyy_id,))
        except sqlite3.IntegrityError:
            messagebox.showerror('Ошибка',
                                 'Сеанс удалить нельзя: на него уже проданы билеты.')
            return
        self.ochistit()
        self.obnovit()


# ======================================================================
#  Вкладка «Продажа билетов»
# ======================================================================

class VkladkaBilety(ttk.Frame):
    """Продажа и возврат билетов. Итоговая цена считается автоматически
    (вычисляемый столбец в базе данных), занятые места проверяются."""

    def __init__(self, roditel, bd):
        super().__init__(roditel, padding=8)
        self.bd = bd
        self.vybrannyy_id = None

        forma = ttk.LabelFrame(self, text='Продажа билета', padding=8)
        forma.pack(fill='x')

        ttk.Label(forma, text='Сеанс:').grid(row=0, column=0, sticky='e', padx=4, pady=3)
        self.spisok_seansov = ttk.Combobox(forma, width=60, state='readonly')
        self.spisok_seansov.grid(row=0, column=1, columnspan=3, padx=4, pady=3, sticky='w')
        self.spisok_seansov.bind('<<ComboboxSelected>>', self.vybran_seans)

        ttk.Label(forma, text='Клиент:').grid(row=1, column=0, sticky='e', padx=4, pady=3)
        self.spisok_klientov = ttk.Combobox(forma, width=34, state='readonly')
        self.spisok_klientov.grid(row=1, column=1, padx=4, pady=3, sticky='w')
        self.spisok_klientov.bind('<<ComboboxSelected>>', self.poschitat_cenu)

        ttk.Label(forma, text='Кассир:').grid(row=1, column=2, sticky='e', padx=4, pady=3)
        self.spisok_sotrudnikov = ttk.Combobox(forma, width=26, state='readonly')
        self.spisok_sotrudnikov.grid(row=1, column=3, padx=4, pady=3, sticky='w')

        ttk.Label(forma, text='Ряд:').grid(row=2, column=0, sticky='e', padx=4, pady=3)
        self.vvod_ryad = ttk.Spinbox(forma, from_=1, to=30, width=6)
        self.vvod_ryad.grid(row=2, column=1, padx=4, pady=3, sticky='w')

        ttk.Label(forma, text='Место:').grid(row=2, column=2, sticky='e', padx=4, pady=3)
        self.vvod_mesto = ttk.Spinbox(forma, from_=1, to=30, width=6)
        self.vvod_mesto.grid(row=2, column=3, padx=4, pady=3, sticky='w')

        self.nadpis_ceny = ttk.Label(forma, text='Цена билета: —', font=('Segoe UI', 10, 'bold'))
        self.nadpis_ceny.grid(row=3, column=0, columnspan=4, sticky='w', padx=4, pady=6)

        knopki = ttk.Frame(self)
        knopki.pack(fill='x', pady=(0, 8))
        ttk.Button(knopki, text='Продать билет', command=self.prodat).pack(side='left')
        ttk.Button(knopki, text='Свободные места',
                   command=self.pokazat_svobodnye).pack(side='left', padx=5)
        ttk.Button(knopki, text='Вернуть билет', command=self.vernut).pack(side='left')
        ttk.Button(knopki, text='Удалить билет', command=self.udalit).pack(side='left', padx=5)

        stolbcy = ('id', 'seans', 'film', 'klient', 'ryad', 'mesto', 'cena', 'status')
        podpisi = ('Код', 'Дата и время', 'Фильм', 'Клиент', 'Ряд', 'Место',
                   'Итоговая цена', 'Статус')
        shiriny = (50, 120, 200, 160, 50, 60, 110, 110)
        self.tablica_vid = ttk.Treeview(self, columns=stolbcy, show='headings', height=12)
        for stolbec, podpis, shirina in zip(stolbcy, podpisi, shiriny):
            self.tablica_vid.heading(stolbec, text=podpis)
            self.tablica_vid.column(stolbec, width=shirina, anchor='w')
        self.tablica_vid.pack(fill='both', expand=True)
        self.tablica_vid.bind('<<TreeviewSelect>>', self.vybrat_zapis)

        self.zagruzit_spiski()
        self.obnovit()

    def zagruzit_spiski(self):
        self.seansy = self.bd.vybrat(
            'SELECT s.id_seansa, s.data_seansa, s.vremya_nachala, f.nazvanie AS film, '
            '       z.nazvanie AS zal, s.bazovaya_cena, z.kolichestvo_ryadov, z.mest_v_ryadu '
            'FROM seans s JOIN film f ON f.id_filma = s.id_filma '
            'JOIN zal z ON z.id_zala = s.id_zala '
            'ORDER BY s.data_seansa, s.vremya_nachala')
        self.klienty = self.bd.vybrat(
            'SELECT id_klienta, familiya, imya, skidka_procent FROM klient ORDER BY familiya')
        self.sotrudniki = self.bd.vybrat(
            "SELECT id_sotrudnika, familiya, imya FROM sotrudnik "
            "WHERE dolzhnost IN ('кассир','администратор') ORDER BY familiya")

        self.spisok_seansov['values'] = [
            f'{r["id_seansa"]} — {r["data_seansa"]} {r["vremya_nachala"]} — '
            f'{r["film"]} ({r["zal"]}, {r["bazovaya_cena"]:.0f} руб.)' for r in self.seansy]
        self.spisok_klientov['values'] = ['без карты'] + [
            f'{r["id_klienta"]} — {r["familiya"]} {r["imya"]} (скидка {r["skidka_procent"]:.0f}%)'
            for r in self.klienty]
        self.spisok_sotrudnikov['values'] = [
            f'{r["id_sotrudnika"]} — {r["familiya"]} {r["imya"]}' for r in self.sotrudniki]

    # ---------- вспомогательные действия ----------

    def tekushchiy_seans(self):
        if not self.spisok_seansov.get():
            return None
        kod = int(self.spisok_seansov.get().split(' — ')[0])
        for stroka in self.seansy:
            if stroka['id_seansa'] == kod:
                return stroka
        return None

    def tekushchaya_skidka(self):
        vybor = self.spisok_klientov.get()
        if not vybor or vybor == 'без карты':
            return 0.0
        kod = int(vybor.split(' — ')[0])
        for stroka in self.klienty:
            if stroka['id_klienta'] == kod:
                return float(stroka['skidka_procent'])
        return 0.0

    def vybran_seans(self, sobytie=None):
        """При выборе сеанса ограничиваем номера рядов и мест размерами зала."""
        seans = self.tekushchiy_seans()
        if seans:
            self.vvod_ryad.configure(to=seans['kolichestvo_ryadov'])
            self.vvod_mesto.configure(to=seans['mest_v_ryadu'])
        self.poschitat_cenu()

    def poschitat_cenu(self, sobytie=None):
        seans = self.tekushchiy_seans()
        if not seans:
            self.nadpis_ceny.configure(text='Цена билета: —')
            return
        skidka = self.tekushchaya_skidka()
        itog = round(seans['bazovaya_cena'] * (1 - skidka / 100), 2)
        self.nadpis_ceny.configure(
            text=f'Цена билета: {seans["bazovaya_cena"]:.2f} руб. − скидка {skidka:.0f}% '
                 f'= {itog:.2f} руб.')

    def obnovit(self):
        sql = ('SELECT b.id_bileta, s.data_seansa || " " || s.vremya_nachala, f.nazvanie, '
               '       IFNULL(k.familiya || " " || k.imya, "без карты"), '
               '       b.ryad, b.mesto, b.itogovaya_cena, b.status '
               'FROM bilet b '
               'JOIN seans s ON s.id_seansa = b.id_seansa '
               'JOIN film f ON f.id_filma = s.id_filma '
               'LEFT JOIN klient k ON k.id_klienta = b.id_klienta '
               'ORDER BY b.id_bileta DESC')
        self.tablica_vid.delete(*self.tablica_vid.get_children())
        for stroka in self.bd.vybrat(sql):
            self.tablica_vid.insert('', 'end', values=tuple(stroka))

    def vybrat_zapis(self, sobytie=None):
        vydelenie = self.tablica_vid.selection()
        if vydelenie:
            self.vybrannyy_id = self.tablica_vid.item(vydelenie[0])['values'][0]

    # ---------- основные операции ----------

    def prodat(self):
        seans = self.tekushchiy_seans()
        if not seans:
            messagebox.showwarning('Внимание', 'Выберите сеанс.')
            return
        if not self.spisok_sotrudnikov.get():
            messagebox.showwarning('Внимание', 'Выберите кассира.')
            return
        try:
            ryad = int(self.vvod_ryad.get())
            mesto = int(self.vvod_mesto.get())
        except ValueError:
            messagebox.showwarning('Внимание', 'Номер ряда и места — целые числа.')
            return
        if ryad > seans['kolichestvo_ryadov'] or mesto > seans['mest_v_ryadu']:
            messagebox.showwarning(
                'Внимание',
                f'В зале «{seans["zal"]}» {seans["kolichestvo_ryadov"]} рядов '
                f'по {seans["mest_v_ryadu"]} мест.')
            return

        vybor_klienta = self.spisok_klientov.get()
        kod_klienta = (None if not vybor_klienta or vybor_klienta == 'без карты'
                       else int(vybor_klienta.split(' — ')[0]))
        kod_sotrudnika = int(self.spisok_sotrudnikov.get().split(' — ')[0])
        skidka = self.tekushchaya_skidka()

        try:
            self.bd.vypolnit(
                'INSERT INTO bilet (id_seansa, id_klienta, id_sotrudnika, ryad, mesto, '
                'data_prodazhi, cena_bez_skidki, skidka_procent, status) '
                "VALUES (?, ?, ?, ?, ?, date('now'), ?, ?, 'продан')",
                (seans['id_seansa'], kod_klienta, kod_sotrudnika, ryad, mesto,
                 seans['bazovaya_cena'], skidka))
        except sqlite3.IntegrityError:
            messagebox.showerror('Ошибка',
                                 f'Место {mesto} в ряду {ryad} на этот сеанс уже продано.')
            return
        itog = round(seans['bazovaya_cena'] * (1 - skidka / 100), 2)
        messagebox.showinfo('Билет продан',
                            f'Фильм: {seans["film"]}\nЗал: {seans["zal"]}\n'
                            f'Ряд {ryad}, место {mesto}\nК оплате: {itog:.2f} руб.')
        self.obnovit()

    def pokazat_svobodnye(self):
        seans = self.tekushchiy_seans()
        if not seans:
            messagebox.showwarning('Внимание', 'Выберите сеанс.')
            return
        zanyato = {(r['ryad'], r['mesto']) for r in self.bd.vybrat(
            "SELECT ryad, mesto FROM bilet WHERE id_seansa = ? AND status <> 'возвращён'",
            (seans['id_seansa'],))}
        vsego = seans['kolichestvo_ryadov'] * seans['mest_v_ryadu']
        svobodno = vsego - len(zanyato)
        spisok_zanyatyh = ', '.join(f'ряд {r}, место {m}' for r, m in sorted(zanyato)) or 'нет'
        messagebox.showinfo(
            'Свободные места',
            f'Фильм: {seans["film"]}\nЗал: {seans["zal"]}\n'
            f'Всего мест: {vsego}\nСвободно: {svobodno}\n\nЗанятые места:\n{spisok_zanyatyh}')

    def vernut(self):
        if self.vybrannyy_id is None:
            messagebox.showwarning('Внимание', 'Выберите билет в таблице.')
            return
        if not messagebox.askyesno('Возврат', 'Оформить возврат выбранного билета?'):
            return
        self.bd.vypolnit("UPDATE bilet SET status = 'возвращён' WHERE id_bileta = ?",
                         (self.vybrannyy_id,))
        self.obnovit()

    def udalit(self):
        if self.vybrannyy_id is None:
            messagebox.showwarning('Внимание', 'Выберите билет в таблице.')
            return
        if not messagebox.askyesno('Удаление', 'Удалить запись о билете?'):
            return
        self.bd.vypolnit('DELETE FROM bilet WHERE id_bileta = ?', (self.vybrannyy_id,))
        self.vybrannyy_id = None
        self.obnovit()


# ======================================================================
#  Вкладка «Отчёты»
# ======================================================================

class VkladkaOtchety(ttk.Frame):
    """Отчёты по работе кинотеатра. Каждый отчёт — это запрос к базе данных."""

    OTCHETY = (
        'Расписание сеансов на дату',
        'Заполненность залов и выручка по сеансам',
        'Выручка за период',
        'Рейтинг фильмов по числу проданных билетов',
        'Продажи по кассирам',
        'Фильмы по жанру',
    )

    def __init__(self, roditel, bd):
        super().__init__(roditel, padding=8)
        self.bd = bd

        panel = ttk.Frame(self)
        panel.pack(fill='x', pady=(0, 6))
        ttk.Label(panel, text='Отчёт:').pack(side='left')
        self.spisok_otchetov = ttk.Combobox(panel, width=46, state='readonly',
                                            values=self.OTCHETY)
        self.spisok_otchetov.current(0)
        self.spisok_otchetov.pack(side='left', padx=5)
        self.spisok_otchetov.bind('<<ComboboxSelected>>', self.podstavit_parametry)

        ttk.Label(panel, text='Параметр 1:').pack(side='left', padx=(10, 2))
        self.parametr1 = ttk.Entry(panel, width=14)
        self.parametr1.pack(side='left')

        ttk.Label(panel, text='Параметр 2:').pack(side='left', padx=(10, 2))
        self.parametr2 = ttk.Entry(panel, width=14)
        self.parametr2.pack(side='left')

        ttk.Button(panel, text='Построить отчёт',
                   command=self.postroit).pack(side='left', padx=8)

        self.podskazka = ttk.Label(self, foreground='#444444', text='')
        self.podskazka.pack(fill='x', pady=(0, 6))

        self.tablica_vid = ttk.Treeview(self, show='headings', height=16)
        self.tablica_vid.pack(fill='both', expand=True)
        self.itog = ttk.Label(self, text='', font=('Segoe UI', 10, 'bold'))
        self.itog.pack(fill='x', pady=6)

        self.podstavit_parametry()
        self.postroit()

    def podstavit_parametry(self, sobytie=None):
        """Подставляет в поля параметров подходящие значения для выбранного отчёта,
        чтобы не вводить даты вручную."""
        nazvanie = self.spisok_otchetov.get()
        self.parametr1.delete(0, 'end')
        self.parametr2.delete(0, 'end')

        if nazvanie == self.OTCHETY[0]:          # расписание на дату
            data = self.bd.vybrat('SELECT MIN(data_seansa) FROM seans')[0][0]
            self.parametr1.insert(0, data or '')
            podskazka = 'Параметр 1 — дата сеансов в формате ГГГГ-ММ-ДД.'
        elif nazvanie == self.OTCHETY[2]:        # выручка за период
            granicy = self.bd.vybrat(
                'SELECT MIN(data_prodazhi), MAX(data_prodazhi) FROM bilet')[0]
            self.parametr1.insert(0, granicy[0] or '')
            self.parametr2.insert(0, granicy[1] or '')
            podskazka = 'Параметр 1 — начало периода, параметр 2 — конец периода (по дате продажи).'
        elif nazvanie == self.OTCHETY[5]:        # фильмы по жанру
            zhanr = self.bd.vybrat('SELECT nazvanie FROM zhanr ORDER BY id_zhanra')[0][0]
            self.parametr1.insert(0, zhanr)
            podskazka = 'Параметр 1 — название жанра или его часть.'
        else:
            podskazka = 'Этот отчёт строится по всем данным, параметры не нужны.'
        self.podskazka.configure(text=podskazka)

    def postroit(self):
        nazvanie = self.spisok_otchetov.get()
        p1 = self.parametr1.get().strip()
        p2 = self.parametr2.get().strip()

        if nazvanie == self.OTCHETY[0]:
            podpisi = ('Время', 'Фильм', 'Длительность, мин', 'Зал', 'Формат', 'Цена, руб.')
            sql = ('SELECT vremya_nachala, film, dlitelnost_min, zal, format_pokaza, '
                   'bazovaya_cena FROM v_raspisanie WHERE data_seansa = ? '
                   'ORDER BY vremya_nachala')
            dannye = self.bd.vybrat(sql, (p1,))
            itog = f'Сеансов на {p1}: {len(dannye)}'

        elif nazvanie == self.OTCHETY[1]:
            podpisi = ('Дата', 'Время', 'Фильм', 'Зал', 'Мест', 'Продано',
                       'Выручка, руб.', 'Заполненность, %')
            sql = ('SELECT data_seansa, vremya_nachala, film, zal, vsego_mest, '
                   'prodano_biletov, vyruchka, zapolnennost_procent '
                   'FROM v_seans_svodka ORDER BY data_seansa, vremya_nachala')
            dannye = self.bd.vybrat(sql)
            itog = f'Всего сеансов: {len(dannye)}'

        elif nazvanie == self.OTCHETY[2]:
            podpisi = ('Дата продажи', 'Продано билетов', 'Выручка, руб.')
            sql = ('SELECT data_prodazhi, COUNT(*), ROUND(SUM(itogovaya_cena), 2) '
                   "FROM bilet WHERE status = 'продан' AND data_prodazhi BETWEEN ? AND ? "
                   'GROUP BY data_prodazhi ORDER BY data_prodazhi')
            dannye = self.bd.vybrat(sql, (p1, p2))
            vsego = sum(stroka[2] for stroka in dannye) if dannye else 0
            itog = f'Выручка за период с {p1} по {p2}: {vsego:.2f} руб.'

        elif nazvanie == self.OTCHETY[3]:
            podpisi = ('Фильм', 'Режиссёр', 'Продано билетов', 'Выручка, руб.')
            sql = ('SELECT f.nazvanie, f.rezhisser, COUNT(b.id_bileta), '
                   'ROUND(IFNULL(SUM(b.itogovaya_cena), 0), 2) '
                   'FROM film f '
                   'LEFT JOIN seans s ON s.id_filma = f.id_filma '
                   "LEFT JOIN bilet b ON b.id_seansa = s.id_seansa AND b.status = 'продан' "
                   'GROUP BY f.id_filma, f.nazvanie, f.rezhisser '
                   'ORDER BY COUNT(b.id_bileta) DESC')
            dannye = self.bd.vybrat(sql)
            itog = f'Всего фильмов в прокате: {len(dannye)}'

        elif nazvanie == self.OTCHETY[4]:
            podpisi = ('Сотрудник', 'Должность', 'Оформлено билетов', 'Сумма продаж, руб.')
            sql = ('SELECT s.familiya || " " || s.imya, s.dolzhnost, COUNT(b.id_bileta), '
                   'ROUND(IFNULL(SUM(b.itogovaya_cena), 0), 2) '
                   'FROM sotrudnik s '
                   "LEFT JOIN bilet b ON b.id_sotrudnika = s.id_sotrudnika "
                   "AND b.status = 'продан' "
                   'GROUP BY s.id_sotrudnika, s.familiya, s.imya, s.dolzhnost '
                   'HAVING COUNT(b.id_bileta) > 0 '
                   'ORDER BY COUNT(b.id_bileta) DESC')
            dannye = self.bd.vybrat(sql)
            itog = f'Кассиров с продажами: {len(dannye)}'

        else:
            podpisi = ('Фильм', 'Режиссёр', 'Год', 'Длительность, мин', 'Рейтинг')
            sql = ('SELECT f.nazvanie, f.rezhisser, f.god_vypuska, f.dlitelnost_min, '
                   'f.vozrastnoy_reyting '
                   'FROM film f '
                   'JOIN film_zhanr fz ON fz.id_filma = f.id_filma '
                   'JOIN zhanr z ON z.id_zhanra = fz.id_zhanra '
                   'WHERE z.nazvanie LIKE ? ORDER BY f.nazvanie')
            dannye = self.bd.vybrat(sql, (f'%{p1}%',))
            itog = f'Найдено фильмов: {len(dannye)}'

        self.tablica_vid.delete(*self.tablica_vid.get_children())
        self.tablica_vid['columns'] = podpisi
        for podpis in podpisi:
            self.tablica_vid.heading(podpis, text=podpis)
            shirina = 260 if 'Фильм' in podpis else 140
            self.tablica_vid.column(podpis, width=shirina, anchor='w')
        for stroka in dannye:
            self.tablica_vid.insert('', 'end', values=tuple(stroka))
        self.itog.configure(text=itog)


# ======================================================================
#  Главное окно
# ======================================================================

class GlavnoeOkno(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('Информационная система «Кинотеатр»')
        self.geometry('1150x720')
        self.bd = BazaDannyh(FAYL_BD)

        zagolovok = ttk.Label(self, text='Информационная система «Кинотеатр»',
                              font=('Segoe UI', 14, 'bold'), padding=8)
        zagolovok.pack()

        vkladki = ttk.Notebook(self)
        vkladki.pack(fill='both', expand=True, padx=8, pady=8)

        vkladki.add(VkladkaSeansy(vkladki, self.bd), text='Сеансы')
        vkladki.add(VkladkaBilety(vkladki, self.bd), text='Продажа билетов')

        vkladki.add(VkladkaSpravochnik(
            vkladki, self.bd, 'film', 'id_filma',
            ['nazvanie', 'rezhisser', 'strana', 'god_vypuska', 'dlitelnost_min',
             'vozrastnoy_reyting'],
            {'nazvanie': 'Название', 'rezhisser': 'Режиссёр', 'strana': 'Страна',
             'god_vypuska': 'Год', 'dlitelnost_min': 'Длительность, мин',
             'vozrastnoy_reyting': 'Рейтинг'},
            ['nazvanie', 'rezhisser', 'strana'],
            {'id_filma': 50, 'nazvanie': 260, 'rezhisser': 170, 'god_vypuska': 60,
             'dlitelnost_min': 130, 'vozrastnoy_reyting': 80}), text='Фильмы')

        vkladki.add(VkladkaSpravochnik(
            vkladki, self.bd, 'zal', 'id_zala',
            ['nazvanie', 'kolichestvo_ryadov', 'mest_v_ryadu', 'tip_zala'],
            {'nazvanie': 'Название зала', 'kolichestvo_ryadov': 'Рядов',
             'mest_v_ryadu': 'Мест в ряду', 'tip_zala': 'Тип зала'},
            ['nazvanie', 'tip_zala'],
            {'id_zala': 50, 'nazvanie': 180}), text='Залы')

        vkladki.add(VkladkaSpravochnik(
            vkladki, self.bd, 'klient', 'id_klienta',
            ['familiya', 'imya', 'telefon', 'email', 'data_registracii', 'skidka_procent'],
            {'familiya': 'Фамилия', 'imya': 'Имя', 'telefon': 'Телефон',
             'email': 'E-mail', 'data_registracii': 'Дата регистрации',
             'skidka_procent': 'Скидка, %'},
            ['familiya', 'imya', 'telefon'],
            {'id_klienta': 50, 'email': 170, 'data_registracii': 130}), text='Клиенты')

        vkladki.add(VkladkaSpravochnik(
            vkladki, self.bd, 'sotrudnik', 'id_sotrudnika',
            ['familiya', 'imya', 'dolzhnost', 'telefon', 'data_priema'],
            {'familiya': 'Фамилия', 'imya': 'Имя', 'dolzhnost': 'Должность',
             'telefon': 'Телефон', 'data_priema': 'Дата приёма'},
            ['familiya', 'dolzhnost'],
            {'id_sotrudnika': 50, 'dolzhnost': 170, 'data_priema': 120}), text='Сотрудники')

        vkladki.add(VkladkaSpravochnik(
            vkladki, self.bd, 'zhanr', 'id_zhanra', ['nazvanie'],
            {'nazvanie': 'Название жанра'}, ['nazvanie'],
            {'id_zhanra': 60, 'nazvanie': 240}), text='Жанры')

        vkladki.add(VkladkaOtchety(vkladki, self.bd), text='Отчёты')

        self.protocol('WM_DELETE_WINDOW', self.zakryt)

    def zakryt(self):
        self.bd.zakryt()
        self.destroy()


if __name__ == '__main__':
    GlavnoeOkno().mainloop()
