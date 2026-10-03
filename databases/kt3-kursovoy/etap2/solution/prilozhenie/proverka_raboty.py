"""Проверка работы приложения: продажа билета, контроль занятых мест,
поиск и отчёты. Диалоговые окна перехватываются, чтобы не блокировать проверку."""
import os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kinoteatr

soobshcheniya = []
kinoteatr.messagebox.showinfo = lambda t, m, **k: soobshcheniya.append(('инфо', t, m))
kinoteatr.messagebox.showerror = lambda t, m, **k: soobshcheniya.append(('ОШИБКА', t, m))
kinoteatr.messagebox.showwarning = lambda t, m, **k: soobshcheniya.append(('предупр', t, m))
kinoteatr.messagebox.askyesno = lambda t, m, **k: True

okno = kinoteatr.GlavnoeOkno()
okno.update()
nb = [w for w in okno.winfo_children() if w.winfo_class() == 'TNotebook'][0]
vkladki = {nb.tab(t, 'text'): nb.nametowidget(t) for t in nb.tabs()}

def snimok(imya):
    okno.update(); okno.update_idletasks(); time.sleep(0.5); okno.update()
    subprocess.run(['import', '-window', 'root', '-crop', '1150x720+0+0', '+repage', imya], check=True)

# --- 1. Продажа билета ---
b = vkladki['Продажа билетов']
nb.select(nb.tabs()[1])
b.spisok_seansov.current(0)
b.vybran_seans()
b.spisok_klientov.current(12)      # клиент со скидкой 25 %
b.poschitat_cenu()
b.spisok_sotrudnikov.current(0)
b.vvod_ryad.delete(0, 'end'); b.vvod_ryad.insert(0, '9')
b.vvod_mesto.delete(0, 'end'); b.vvod_mesto.insert(0, '9')
snimok('forma_prodazha.png')
kolvo_do = len(b.bd.vybrat('SELECT id_bileta FROM bilet'))
b.prodat()
kolvo_posle = len(b.bd.vybrat('SELECT id_bileta FROM bilet'))
print(f'1) Продажа билета: было {kolvo_do}, стало {kolvo_posle}')
print('   сообщение:', soobshcheniya[-1][2].replace('\n', ' | '))

# --- 2. Повторная продажа того же места ---
soobshcheniya.clear()
b.prodat()
print('2) Повторная продажа того же места ->', soobshcheniya[-1][0], ':', soobshcheniya[-1][2])

# --- 3. Проверка выхода за размеры зала ---
soobshcheniya.clear()
b.vvod_ryad.delete(0, 'end'); b.vvod_ryad.insert(0, '99')
b.prodat()
print('3) Несуществующий ряд ->', soobshcheniya[-1][0], ':', soobshcheniya[-1][2].replace('\n',' '))

# --- 4. Свободные места ---
soobshcheniya.clear()
b.pokazat_svobodnye()
print('4) Свободные места:', soobshcheniya[-1][2].split('\n\n')[0].replace('\n', ' | '))

# --- 5. Возврат билета ---
b.obnovit()
b.vybrannyy_id = kolvo_posle
b.vernut()
status = b.bd.vybrat('SELECT status FROM bilet WHERE id_bileta = ?', (kolvo_posle,))[0][0]
print(f'5) Возврат билета №{kolvo_posle}: статус стал «{status}»')

# --- 6. Поиск по справочнику ---
f = vkladki['Фильмы']
nb.select(nb.tabs()[2])
f.pole_poiska.insert(0, 'Нолан')
f.obnovit()
najdeno = len(f.tablica_vid.get_children())
print(f'6) Поиск «Нолан» в справочнике фильмов: найдено {najdeno} записей')
snimok('forma_poisk.png')

# --- 7. Отчёты ---
o = vkladki['Отчёты']
nb.select(nb.tabs()[7])
for nomer, nazvanie in enumerate(o.OTCHETY):
    o.spisok_otchetov.current(nomer)
    o.podstavit_parametry()      # параметры подставляются автоматически
    o.postroit()
    strok = len(o.tablica_vid.get_children())
    print(f'7.{nomer+1}) Отчёт «{nazvanie}»: строк {strok}; {o.itog.cget("text")}')
    if nomer == 1:
        snimok('forma_otchet_zapolnennost.png')
    if nomer == 2:
        snimok('forma_otchet_vyruchka.png')

# --- 8. Добавление и удаление записи в справочнике ---
z = vkladki['Жанры']
nb.select(nb.tabs()[6])
z.vvod['nazvanie'].insert(0, 'военный')
z.dobavit()
vsego = len(z.tablica_vid.get_children())
z.vybrannyy_id = z.bd.vybrat("SELECT id_zhanra FROM zhanr WHERE nazvanie='военный'")[0][0]
z.udalit()
posle = len(z.tablica_vid.get_children())
print(f'8) Справочник жанров: после добавления {vsego}, после удаления {posle}')

# --- 9. Запрет удаления связанной записи ---
soobshcheniya.clear()
zal = vkladki['Залы']
zal.vybrannyy_id = 1
zal.udalit()
print('9) Удаление зала с сеансами ->', soobshcheniya[-1][0], ':', soobshcheniya[-1][2])

okno.bd.zakryt(); okno.destroy()
