"""
Oshxona boti — ma'lumotlar bazasi
SQLite ishlatiladi, hamma ma'lumot oshxona.db faylida saqlanadi
"""

import sqlite3
from datetime import datetime

DB = "oshxona.db"

def ulan():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def jadvallar_yarat():
    conn = ulan()
    c = conn.cursor()

    # Foydalanuvchilar va til sozlamasi
    c.execute("""
        CREATE TABLE IF NOT EXISTS foydalanuvchilar (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            ism TEXT,
            til TEXT DEFAULT 'uz',
            rol TEXT DEFAULT 'oshpaz'
        )
    """)

    # Mahsulot guruhlari (go'sht, sabzavot, don, sut, ziravorlar)
    c.execute("""
        CREATE TABLE IF NOT EXISTS guruhlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_uz TEXT,
            nom_ru TEXT,
            tur TEXT DEFAULT 'oddiy'
        )
    """)

    # Mahsulotlar (har bir guruh ichida)
    c.execute("""
        CREATE TABLE IF NOT EXISTS mahsulotlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guruh_id INTEGER,
            nom_uz TEXT,
            nom_ru TEXT,
            olchov TEXT DEFAULT 'kg',
            qismlar TEXT DEFAULT '',
            FOREIGN KEY (guruh_id) REFERENCES guruhlar(id)
        )
    """)

    # Taomlar ro'yxati
    c.execute("""
        CREATE TABLE IF NOT EXISTS taomlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_uz TEXT,
            nom_ru TEXT,
            mahsulot_id INTEGER,
            FOREIGN KEY (mahsulot_id) REFERENCES mahsulotlar(id)
        )
    """)

    # Kirim (mahsulot keldi)
    c.execute("""
        CREATE TABLE IF NOT EXISTS kirimlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mahsulot_id INTEGER,
            kg REAL,
            dona INTEGER DEFAULT 0,
            sana TEXT,
            vaqt TEXT,
            kim_id INTEGER,
            izoh TEXT DEFAULT '',
            FOREIGN KEY (mahsulot_id) REFERENCES mahsulotlar(id)
        )
    """)

    # Kesish natijalari (mahsulotdan qism chiqdi)
    c.execute("""
        CREATE TABLE IF NOT EXISTS kesish (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kirim_id INTEGER,
            mahsulot_id INTEGER,
            qism TEXT,
            kg REAL,
            sana TEXT,
            vaqt TEXT,
            kim_id INTEGER,
            FOREIGN KEY (kirim_id) REFERENCES kirimlar(id)
        )
    """)

    # Taom yozuvlari (qaysi qismdan qaysi taom, necha kg, necha porsiya, narx)
    c.execute("""
        CREATE TABLE IF NOT EXISTS taom_yozuv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            taom_id INTEGER,
            mahsulot_id INTEGER,
            qism TEXT,
            kg REAL,
            porsiya INTEGER DEFAULT 0,
            narx REAL DEFAULT 0,
            sana TEXT,
            vaqt TEXT,
            kim_id INTEGER,
            izoh TEXT DEFAULT '',
            FOREIGN KEY (taom_id) REFERENCES taomlar(id)
        )
    """)

    conn.commit()

    # Boshlangich guruhlar va mahsulotlar
    _boshlangich_data(c, conn)
    conn.close()

def _boshlangich_data(c, conn):
    # Guruhlar mavjud bo'lmasa qo'sh
    c.execute("SELECT COUNT(*) FROM guruhlar")
    if c.fetchone()[0] > 0:
        return

    guruhlar = [
        ("Go'sht", "Мясо", "gosht"),
        ("Sabzavotlar", "Овощи", "oddiy"),
        ("Don mahsulotlari", "Зерновые", "oddiy"),
        ("Sut mahsulotlari", "Молочные", "oddiy"),
        ("Ziravorlar", "Специи", "oddiy"),
    ]
    c.executemany("INSERT INTO guruhlar (nom_uz, nom_ru, tur) VALUES (?,?,?)", guruhlar)
    conn.commit()

    # Guruh ID larini ol
    c.execute("SELECT id, nom_uz FROM guruhlar")
    gids = {row["nom_uz"]: row["id"] for row in c.fetchall()}

    mahsulotlar = [
        (gids["Go'sht"], "Baliq", "Рыба", "kg", "Fille,Suyak,Chiqindi"),
        (gids["Go'sht"], "Qo'y", "Баранина", "kg", "Fille,Suyak,Qiyma,Chiqindi"),
        (gids["Go'sht"], "Mol", "Говядина", "kg", "Fille,Suyak,Qiyma,Chiqindi"),
        (gids["Go'sht"], "Quyon", "Кролик", "kg", "Fille,Suyak,Qiyma,Chiqindi"),
        (gids["Go'sht"], "Tovuq", "Курица", "kg", "Fille,Suyak,Chiqindi"),
        (gids["Go'sht"], "Kurka", "Индейка", "kg", "Fille,Suyak,Chiqindi"),
        (gids["Sabzavotlar"], "Piyoz", "Лук", "kg", ""),
        (gids["Sabzavotlar"], "Sabzi", "Морковь", "kg", ""),
        (gids["Sabzavotlar"], "Kartoshka", "Картофель", "kg", ""),
        (gids["Don mahsulotlari"], "Guruch", "Рис", "kg", ""),
        (gids["Don mahsulotlari"], "Un", "Мука", "kg", ""),
        (gids["Don mahsulotlari"], "Makaron", "Макароны", "kg", ""),
        (gids["Sut mahsulotlari"], "Yog'", "Масло", "kg", ""),
        (gids["Sut mahsulotlari"], "Tuxum", "Яйца", "dona", ""),
        (gids["Sut mahsulotlari"], "Qaymoq", "Сметана", "kg", ""),
        (gids["Ziravorlar"], "Tuz", "Соль", "kg", ""),
        (gids["Ziravorlar"], "Qalampir", "Перец", "kg", ""),
    ]
    c.executemany(
        "INSERT INTO mahsulotlar (guruh_id,nom_uz,nom_ru,olchov,qismlar) VALUES (?,?,?,?,?)",
        mahsulotlar
    )
    conn.commit()

    # Boshlangich taomlar
    c.execute("SELECT id, nom_uz FROM mahsulotlar")
    mids = {row["nom_uz"]: row["id"] for row in c.fetchall()}

    taomlar = [
        ("Kotlet", "Котлеты", mids.get("Quyon")),
        ("Kabob", "Кебаб", mids.get("Mol")),
        ("Sho'rva", "Суп", mids.get("Qo'y")),
        ("Fried fish", "Жареная рыба", mids.get("Baliq")),
        ("Tovuq qovurma", "Жареная курица", mids.get("Tovuq")),
        ("Pilaf", "Плов", mids.get("Mol")),
    ]
    c.executemany(
        "INSERT INTO taomlar (nom_uz, nom_ru, mahsulot_id) VALUES (?,?,?)",
        taomlar
    )
    conn.commit()

# ── FOYDALANUVCHI ──────────────────────────────────────────

def foydalanuvchi_ol(telegram_id):
    conn = ulan()
    c = conn.cursor()
    c.execute("SELECT * FROM foydalanuvchilar WHERE telegram_id=?", (telegram_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def foydalanuvchi_qosh(telegram_id, ism, til="uz", rol="oshpaz"):
    conn = ulan()
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO foydalanuvchilar (telegram_id,ism,til,rol) VALUES (?,?,?,?)",
        (telegram_id, ism, til, rol)
    )
    conn.commit()
    conn.close()

def til_ozgartir(telegram_id, til):
    conn = ulan()
    c = conn.cursor()
    c.execute("UPDATE foydalanuvchilar SET til=? WHERE telegram_id=?", (til, telegram_id))
    conn.commit()
    conn.close()

def menejermi(telegram_id, menejer_id):
    return telegram_id == menejer_id

# ── MAHSULOTLAR ────────────────────────────────────────────

def guruhlar_ol():
    conn = ulan()
    c = conn.cursor()
    c.execute("SELECT * FROM guruhlar ORDER BY id")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def mahsulotlar_ol(guruh_id=None):
    conn = ulan()
    c = conn.cursor()
    if guruh_id:
        c.execute("SELECT * FROM mahsulotlar WHERE guruh_id=? ORDER BY nom_uz", (guruh_id,))
    else:
        c.execute("SELECT * FROM mahsulotlar ORDER BY nom_uz")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def mahsulot_ol(mahsulot_id):
    conn = ulan()
    c = conn.cursor()
    c.execute("SELECT * FROM mahsulotlar WHERE id=?", (mahsulot_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def mahsulot_qosh(guruh_id, nom_uz, nom_ru, olchov="kg", qismlar=""):
    conn = ulan()
    c = conn.cursor()
    c.execute(
        "INSERT INTO mahsulotlar (guruh_id,nom_uz,nom_ru,olchov,qismlar) VALUES (?,?,?,?,?)",
        (guruh_id, nom_uz, nom_ru, olchov, qismlar)
    )
    mid = c.lastrowid
    conn.commit()
    conn.close()
    return mid

def qism_qosh(mahsulot_id, yangi_qism):
    conn = ulan()
    c = conn.cursor()
    c.execute("SELECT qismlar FROM mahsulotlar WHERE id=?", (mahsulot_id,))
    row = c.fetchone()
    if row:
        qismlar = row["qismlar"].split(",") if row["qismlar"] else []
        if yangi_qism not in qismlar:
            qismlar.append(yangi_qism)
        c.execute("UPDATE mahsulotlar SET qismlar=? WHERE id=?",
                  (",".join(qismlar), mahsulot_id))
        conn.commit()
    conn.close()

# ── TAOMLAR ────────────────────────────────────────────────

def taomlar_ol(mahsulot_id=None):
    conn = ulan()
    c = conn.cursor()
    if mahsulot_id:
        c.execute("SELECT * FROM taomlar WHERE mahsulot_id=? ORDER BY nom_uz", (mahsulot_id,))
    else:
        c.execute("SELECT * FROM taomlar ORDER BY nom_uz")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def taom_qosh(nom_uz, nom_ru, mahsulot_id):
    conn = ulan()
    c = conn.cursor()
    c.execute("INSERT INTO taomlar (nom_uz,nom_ru,mahsulot_id) VALUES (?,?,?)",
              (nom_uz, nom_ru, mahsulot_id))
    tid = c.lastrowid
    conn.commit()
    conn.close()
    return tid

# ── KIRIM ──────────────────────────────────────────────────

def kirim_qosh(mahsulot_id, kg, dona, kim_id, izoh=""):
    conn = ulan()
    c = conn.cursor()
    sana = datetime.now().strftime("%Y-%m-%d")
    vaqt = datetime.now().strftime("%H:%M")
    c.execute(
        "INSERT INTO kirimlar (mahsulot_id,kg,dona,sana,vaqt,kim_id,izoh) VALUES (?,?,?,?,?,?,?)",
        (mahsulot_id, kg, dona, sana, vaqt, kim_id, izoh)
    )
    kid = c.lastrowid
    conn.commit()
    conn.close()
    return kid

def kirim_tahrir(kirim_id, kg, dona):
    conn = ulan()
    c = conn.cursor()
    c.execute("UPDATE kirimlar SET kg=?, dona=? WHERE id=?", (kg, dona, kirim_id))
    conn.commit()
    conn.close()

def kirim_ochir(kirim_id):
    conn = ulan()
    c = conn.cursor()
    c.execute("DELETE FROM kesish WHERE kirim_id=?", (kirim_id,))
    c.execute("DELETE FROM kirimlar WHERE id=?", (kirim_id,))
    conn.commit()
    conn.close()

def oxirgi_kirimlar(mahsulot_id, sana=None):
    conn = ulan()
    c = conn.cursor()
    if not sana:
        sana = datetime.now().strftime("%Y-%m-%d")
    c.execute(
        "SELECT * FROM kirimlar WHERE mahsulot_id=? AND sana=? ORDER BY id DESC LIMIT 10",
        (mahsulot_id, sana)
    )
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# ── KESISH ─────────────────────────────────────────────────

def kesish_qosh(kirim_id, mahsulot_id, qism, kg, kim_id):
    conn = ulan()
    c = conn.cursor()
    sana = datetime.now().strftime("%Y-%m-%d")
    vaqt = datetime.now().strftime("%H:%M")
    c.execute(
        "INSERT INTO kesish (kirim_id,mahsulot_id,qism,kg,sana,vaqt,kim_id) VALUES (?,?,?,?,?,?,?)",
        (kirim_id, mahsulot_id, qism, kg, sana, vaqt, kim_id)
    )
    conn.commit()
    conn.close()

def kesish_ochir(kesish_id):
    conn = ulan()
    c = conn.cursor()
    c.execute("DELETE FROM kesish WHERE id=?", (kesish_id,))
    conn.commit()
    conn.close()

def kesish_natija(kirim_id):
    conn = ulan()
    c = conn.cursor()
    c.execute("SELECT * FROM kesish WHERE kirim_id=?", (kirim_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# ── TAOM YOZUV ─────────────────────────────────────────────

def taom_yoz(taom_id, mahsulot_id, qism, kg, porsiya, narx, kim_id, izoh=""):
    conn = ulan()
    c = conn.cursor()
    sana = datetime.now().strftime("%Y-%m-%d")
    vaqt = datetime.now().strftime("%H:%M")
    c.execute(
        "INSERT INTO taom_yozuv (taom_id,mahsulot_id,qism,kg,porsiya,narx,sana,vaqt,kim_id,izoh) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (taom_id, mahsulot_id, qism, kg, porsiya, narx, sana, vaqt, kim_id, izoh)
    )
    tid = c.lastrowid
    conn.commit()
    conn.close()
    return tid

def taom_tahrir(yozuv_id, kg, porsiya, narx):
    conn = ulan()
    c = conn.cursor()
    c.execute("UPDATE taom_yozuv SET kg=?,porsiya=?,narx=? WHERE id=?",
              (kg, porsiya, narx, yozuv_id))
    conn.commit()
    conn.close()

def taom_ochir(yozuv_id):
    conn = ulan()
    c = conn.cursor()
    c.execute("DELETE FROM taom_yozuv WHERE id=?", (yozuv_id,))
    conn.commit()
    conn.close()

# ── HISOBOTLAR ─────────────────────────────────────────────

def kunlik_hisobot(sana=None):
    if not sana:
        sana = datetime.now().strftime("%Y-%m-%d")
    conn = ulan()
    c = conn.cursor()

    c.execute("""
        SELECT m.nom_uz, m.nom_ru, SUM(k.kg) as jami_kg, SUM(k.dona) as jami_dona
        FROM kirimlar k JOIN mahsulotlar m ON k.mahsulot_id=m.id
        WHERE k.sana=? GROUP BY k.mahsulot_id
    """, (sana,))
    kirimlar = [dict(r) for r in c.fetchall()]

    c.execute("""
        SELECT t.nom_uz, t.nom_ru, SUM(ty.kg) as jami_kg,
               SUM(ty.porsiya) as jami_porsiya, SUM(ty.narx*ty.kg) as jami_narx
        FROM taom_yozuv ty JOIN taomlar t ON ty.taom_id=t.id
        WHERE ty.sana=? GROUP BY ty.taom_id
    """, (sana,))
    taomlar = [dict(r) for r in c.fetchall()]

    c.execute("""
        SELECT qism, SUM(kg) as jami_kg
        FROM kesish WHERE sana=? GROUP BY qism
    """, (sana,))
    kesishlar = [dict(r) for r in c.fetchall()]

    conn.close()
    return {"sana": sana, "kirimlar": kirimlar, "taomlar": taomlar, "kesishlar": kesishlar}

def sklad_holati():
    conn = ulan()
    c = conn.cursor()
    c.execute("""
        SELECT m.id, m.nom_uz, m.nom_ru, m.olchov,
               COALESCE(SUM(k.kg),0) as kirim_kg,
               COALESCE(SUM(k.dona),0) as kirim_dona
        FROM mahsulotlar m
        LEFT JOIN kirimlar k ON m.id=k.mahsulot_id
        GROUP BY m.id
    """)
    kirimlar = {r["id"]: dict(r) for r in c.fetchall()}

    c.execute("""
        SELECT mahsulot_id, SUM(kg) as chiqim_kg
        FROM taom_yozuv GROUP BY mahsulot_id
    """)
    for r in c.fetchall():
        mid = r["mahsulot_id"]
        if mid in kirimlar:
            kirimlar[mid]["qoldiq_kg"] = round(
                kirimlar[mid]["kirim_kg"] - r["chiqim_kg"], 2)

    for v in kirimlar.values():
        if "qoldiq_kg" not in v:
            v["qoldiq_kg"] = v["kirim_kg"]

    conn.close()
    return list(kirimlar.values())
