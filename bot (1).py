"""
Oshxona mahsulot hisobi — Telegram Bot
=======================================
Xususiyatlar:
  - O'zbek va Rus tili (oshpaz tanlaydi)
  - Mahsulot / taom / qism qo'shish
  - Kirim, kesish, taom yozish
  - Tahrirlash (oshpaz o'z yozuvini)
  - O'chirish (faqat menejer)
  - Kunlik / haftalik / oylik hisobot
  - Sklad holati
  - Balans tekshiruvi

O'rnatish:
  pip install pyTelegramBotAPI

Ishga tushirish:
  python bot.py
"""

import telebot
from telebot import types
from datetime import datetime, timedelta
import database as db

# ═══════════════════════════════════════════════════════════
#  SOZLAMALAR — Railway.app da Variables bo'limiga kiriting
#  BOT_TOKEN  = BotFather dan olgan token
#  MENEJER_ID = @userinfobot dan olgan ID raqam
# ═══════════════════════════════════════════════════════════
import os
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
MENEJER_ID = int(os.environ.get("MENEJER_ID", "0"))
# ═══════════════════════════════════════════════════════════

bot = telebot.TeleBot(BOT_TOKEN)
db.jadvallar_yarat()

# Foydalanuvchi holatlari (xotirada)
holat = {}   # {chat_id: {"qadam": ..., ...}}

# ── TIL YORDAMCHISI ────────────────────────────────────────

def t(chat_id, uz, ru):
    """Foydalanuvchi tiliga qarab matn qaytaradi."""
    u = db.foydalanuvchi_ol(chat_id)
    til = u["til"] if u else "uz"
    return uz if til == "uz" else ru

def nom(item, chat_id):
    """Mahsulot yoki taom nomini tilga qarab oladi."""
    u = db.foydalanuvchi_ol(chat_id)
    til = u["til"] if u else "uz"
    return item.get("nom_uz") if til == "uz" else item.get("nom_ru", item.get("nom_uz"))

# ── ASOSIY MENYU TUGMALARI ─────────────────────────────────

def asosiy_menyu(chat_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton(t(chat_id, "📦 Kirim", "📦 Приход")),
        types.KeyboardButton(t(chat_id, "🔪 Kesish", "🔪 Разделка")),
        types.KeyboardButton(t(chat_id, "🍳 Taom", "🍳 Блюдо")),
        types.KeyboardButton(t(chat_id, "📊 Hisobot", "📊 Отчёт")),
        types.KeyboardButton(t(chat_id, "📋 Sklad", "📋 Склад")),
        types.KeyboardButton(t(chat_id, "⚙️ Sozlama", "⚙️ Настройки")),
    )
    return kb

def bekor_kb(chat_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(t(chat_id, "🔙 Ortga", "🔙 Назад")))
    return kb

def ortga_kb(chat_id):
    return bekor_kb(chat_id)

# ── START ──────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def start(msg):
    cid = msg.chat.id
    ism = msg.from_user.first_name or "Mehmon"

    # Foydalanuvchi mavjud bo'lmasa til tanlash
    if not db.foydalanuvchi_ol(cid):
        holat[cid] = {"qadam": "til_tanla"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🇺🇿 O'zbek", "🇷🇺 Русский")
        bot.send_message(cid, f"Salom {ism}! / Привет {ism}!\n\nTilni tanlang / Выберите язык:", reply_markup=kb)
        return

    holat[cid] = {"qadam": "asosiy"}
    bot.send_message(
        cid,
        t(cid, f"Xush kelibsiz, {ism}! 🍽", f"Добро пожаловать, {ism}! 🍽"),
        reply_markup=asosiy_menyu(cid)
    )

# ── BARCHA XABARLAR ────────────────────────────────────────

@bot.message_handler(func=lambda m: True)
def xabar(msg):
    cid  = msg.chat.id
    matn = msg.text.strip() if msg.text else ""
    u    = db.foydalanuvchi_ol(cid)
    qadam = holat.get(cid, {}).get("qadam", "asosiy")

    # ── TIL TANLASH ──
    if qadam == "til_tanla":
        if "O'zbek" in matn:
            db.foydalanuvchi_qosh(cid, msg.from_user.first_name or "", "uz")
            holat[cid] = {"qadam": "asosiy"}
            bot.send_message(cid, "✅ O'zbek tili tanlandi!", reply_markup=asosiy_menyu(cid))
        elif "Русский" in matn:
            db.foydalanuvchi_qosh(cid, msg.from_user.first_name or "", "ru")
            holat[cid] = {"qadam": "asosiy"}
            bot.send_message(cid, "✅ Русский язык выбран!", reply_markup=asosiy_menyu(cid))
        return

    # Foydalanuvchi ro'yxatda bo'lmasa
    if not u:
        bot.send_message(cid, "Iltimos /start bosing. / Пожалуйста нажмите /start.")
        return

    # ── ORTGA ──
    if matn in ["🔙 Ortga", "🔙 Назад"]:
        holat[cid] = {"qadam": "asosiy"}
        bot.send_message(cid, t(cid, "Asosiy menyu", "Главное меню"), reply_markup=asosiy_menyu(cid))
        return

    # ── SOZLAMALAR ──
    if matn in ["⚙️ Sozlama", "⚙️ Настройки"]:
        holat[cid] = {"qadam": "sozlama"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add("🇺🇿 O'zbek", "🇷🇺 Русский",
               types.KeyboardButton(t(cid, "🔙 Ortga", "🔙 Назад")))
        bot.send_message(cid, t(cid, "Tilni tanlang:", "Выберите язык:"), reply_markup=kb)
        return

    if qadam == "sozlama":
        if "O'zbek" in matn:
            db.til_ozgartir(cid, "uz")
        elif "Русский" in matn:
            db.til_ozgartir(cid, "ru")
        holat[cid] = {"qadam": "asosiy"}
        bot.send_message(cid, t(cid, "✅ Til o'zgardi", "✅ Язык изменён"), reply_markup=asosiy_menyu(cid))
        return

    # ═══════════════════════════════════════════════════════
    #  KIRIM
    # ═══════════════════════════════════════════════════════
    if matn in ["📦 Kirim", "📦 Приход"]:
        holat[cid] = {"qadam": "kirim_guruh"}
        _guruh_kb(cid, t(cid, "Qaysi guruh?", "Какая группа?"))
        return

    if qadam == "kirim_guruh":
        g = _guruh_top(cid, matn)
        if g:
            holat[cid] = {"qadam": "kirim_mahsulot", "guruh_id": g["id"]}
            _mahsulot_kb(cid, g["id"], t(cid, "Qaysi mahsulot?", "Какой продукт?"))
        elif matn == t(cid, "➕ Yangi mahsulot", "➕ Новый продукт"):
            holat[cid]["qadam"] = "kirim_yangi_mah_uz"
            bot.send_message(cid, t(cid, "Mahsulot nomi (o'zbekcha):", "Название продукта (по-узбекски):"), reply_markup=ortga_kb(cid))
        return

    if qadam == "kirim_yangi_mah_uz":
        holat[cid]["nom_uz"] = matn
        holat[cid]["qadam"] = "kirim_yangi_mah_ru"
        bot.send_message(cid, t(cid, "Nomi (ruscha):", "Название (по-русски):"), reply_markup=ortga_kb(cid))
        return

    if qadam == "kirim_yangi_mah_ru":
        h = holat[cid]
        mid = db.mahsulot_qosh(h["guruh_id"], h["nom_uz"], matn)
        holat[cid] = {"qadam": "kirim_mahsulot_id", "mahsulot_id": mid}
        bot.send_message(cid, t(cid, f"✅ Qo'shildi! Necha kg?", f"✅ Добавлен! Сколько кг?"), reply_markup=ortga_kb(cid))
        holat[cid]["qadam"] = "kirim_kg"
        return

    if qadam == "kirim_mahsulot":
        m = _mahsulot_top(cid, holat[cid].get("guruh_id"), matn)
        if m:
            holat[cid]["mahsulot_id"] = m["id"]
            holat[cid]["olchov"] = m["olchov"]
            holat[cid]["qadam"] = "kirim_kg"
            bot.send_message(cid, t(cid, f"Necha {m['olchov']}?", f"Сколько {m['olchov']}?"), reply_markup=ortga_kb(cid))
        elif matn == t(cid, "➕ Yangi mahsulot", "➕ Новый продукт"):
            holat[cid]["qadam"] = "kirim_yangi_mah_uz"
            bot.send_message(cid, t(cid, "Mahsulot nomi (o'zbekcha):", "Название (по-узбекски):"), reply_markup=ortga_kb(cid))
        return

    if qadam == "kirim_kg":
        try:
            kg = float(matn.replace(",", "."))
            if kg <= 0: raise ValueError
        except:
            bot.send_message(cid, t(cid, "Son kiriting! Masalan: 5 yoki 2.5", "Введите число! Например: 5 или 2.5"))
            return
        holat[cid]["kg"] = kg
        holat[cid]["qadam"] = "kirim_dona"
        bot.send_message(cid, t(cid, "Necha dona? (0 yozing agar kerak bo'lmasa)", "Сколько штук? (0 если не нужно)"), reply_markup=ortga_kb(cid))
        return

    if qadam == "kirim_dona":
        try:
            dona = int(matn)
        except:
            dona = 0
        h = holat[cid]
        kid = db.kirim_qosh(h["mahsulot_id"], h["kg"], dona, cid)
        m = db.mahsulot_ol(h["mahsulot_id"])
        holat[cid] = {"qadam": "asosiy"}
        javob = t(cid,
            f"✅ Kirim saqlandi!\n{nom(m,cid)}: {h['kg']} kg, {dona} dona",
            f"✅ Приход сохранён!\n{nom(m,cid)}: {h['kg']} кг, {dona} шт"
        )
        bot.send_message(cid, javob, reply_markup=asosiy_menyu(cid))
        _menejerga(cid, javob)
        return

    # ═══════════════════════════════════════════════════════
    #  KESISH
    # ═══════════════════════════════════════════════════════
    if matn in ["🔪 Kesish", "🔪 Разделка"]:
        holat[cid] = {"qadam": "kesish_guruh"}
        _guruh_kb(cid, t(cid, "Qaysi guruh?", "Какая группа?"), faqat_gosht=True)
        return

    if qadam == "kesish_guruh":
        g = _guruh_top(cid, matn)
        if g:
            holat[cid] = {"qadam": "kesish_mahsulot", "guruh_id": g["id"]}
            _mahsulot_kb(cid, g["id"], t(cid, "Qaysi mahsulot?", "Какой продукт?"), qism_kerak=True)
        return

    if qadam == "kesish_mahsulot":
        m = _mahsulot_top(cid, holat[cid].get("guruh_id"), matn)
        if m:
            holat[cid]["mahsulot_id"] = m["id"]
            holat[cid]["qismlar"] = m.get("qismlar", "").split(",") if m.get("qismlar") else []
            holat[cid]["kesish_natijalari"] = []
            holat[cid]["qadam"] = "kesish_kirim_top"
            kirimlar = db.oxirgi_kirimlar(m["id"])
            if not kirimlar:
                bot.send_message(cid, t(cid, "Bu mahsulot uchun kirim topilmadi!", "Приход для этого продукта не найден!"))
                holat[cid] = {"qadam": "asosiy"}
                return
            holat[cid]["kirim_id"] = kirimlar[0]["id"]
            holat[cid]["kirim_kg"] = kirimlar[0]["kg"]
            _qism_kb(cid, holat[cid]["qismlar"])
        return

    if qadam == "kesish_qism":
        h = holat[cid]
        qism = matn
        if qism == t(cid, "➕ Yangi qism", "➕ Новая часть"):
            holat[cid]["qadam"] = "kesish_yangi_qism"
            bot.send_message(cid, t(cid, "Yangi qism nomi:", "Название новой части:"), reply_markup=ortga_kb(cid))
            return
        if qism == t(cid, "✅ Tayyor", "✅ Готово"):
            _kesish_saqlash(cid)
            return
        holat[cid]["joriy_qism"] = qism
        holat[cid]["qadam"] = "kesish_kg"
        bot.send_message(cid, t(cid, f"{qism} — necha kg?", f"{qism} — сколько кг?"), reply_markup=ortga_kb(cid))
        return

    if qadam == "kesish_yangi_qism":
        yangi = matn
        db.qism_qosh(holat[cid]["mahsulot_id"], yangi)
        holat[cid]["qismlar"].append(yangi)
        holat[cid]["joriy_qism"] = yangi
        holat[cid]["qadam"] = "kesish_kg"
        bot.send_message(cid, t(cid, f"✅ Qo'shildi! {yangi} — necha kg?", f"✅ Добавлено! {yangi} — сколько кг?"), reply_markup=ortga_kb(cid))
        return

    if qadam == "kesish_kirim_top":
        holat[cid]["qadam"] = "kesish_qism"
        _qism_kb(cid, holat[cid]["qismlar"])
        return

    if qadam == "kesish_kg":
        try:
            kg = float(matn.replace(",", "."))
            if kg <= 0: raise ValueError
        except:
            bot.send_message(cid, t(cid, "Son kiriting!", "Введите число!"))
            return
        h = holat[cid]
        h["kesish_natijalari"].append({"qism": h["joriy_qism"], "kg": kg})
        holat[cid]["qadam"] = "kesish_qism"
        _qism_kb(cid, h["qismlar"], h["kesish_natijalari"])
        return

    # ═══════════════════════════════════════════════════════
    #  TAOM
    # ═══════════════════════════════════════════════════════
    if matn in ["🍳 Taom", "🍳 Блюдо"]:
        holat[cid] = {"qadam": "taom_guruh"}
        _guruh_kb(cid, t(cid, "Qaysi guruhdan?", "Из какой группы?"))
        return

    if qadam == "taom_guruh":
        g = _guruh_top(cid, matn)
        if g:
            holat[cid] = {"qadam": "taom_mahsulot", "guruh_id": g["id"]}
            _mahsulot_kb(cid, g["id"], t(cid, "Qaysi mahsulot?", "Какой продукт?"))
        return

    if qadam == "taom_mahsulot":
        m = _mahsulot_top(cid, holat[cid].get("guruh_id"), matn)
        if m:
            holat[cid]["mahsulot_id"] = m["id"]
            holat[cid]["qadam"] = "taom_tanla"
            _taom_kb(cid, m["id"])
        return

    if qadam == "taom_tanla":
        if matn == t(cid, "➕ Yangi taom", "➕ Новое блюдо"):
            holat[cid]["qadam"] = "taom_yangi_uz"
            bot.send_message(cid, t(cid, "Taom nomi (o'zbekcha):", "Название блюда (по-узбекски):"), reply_markup=ortga_kb(cid))
            return
        taomlar = db.taomlar_ol(holat[cid]["mahsulot_id"])
        t_obj = next((x for x in taomlar if nom(x, cid) == matn), None)
        if t_obj:
            holat[cid]["taom_id"] = t_obj["id"]
            holat[cid]["qadam"] = "taom_qism"
            m = db.mahsulot_ol(holat[cid]["mahsulot_id"])
            qismlar = m.get("qismlar", "").split(",") if m.get("qismlar") else []
            if qismlar and qismlar[0]:
                _qism_tanla_kb(cid, qismlar)
            else:
                holat[cid]["qism"] = "Umumiy"
                holat[cid]["qadam"] = "taom_kg"
                bot.send_message(cid, t(cid, "Necha kg ishlatildi?", "Сколько кг использовано?"), reply_markup=ortga_kb(cid))
        return

    if qadam == "taom_yangi_uz":
        holat[cid]["taom_nom_uz"] = matn
        holat[cid]["qadam"] = "taom_yangi_ru"
        bot.send_message(cid, t(cid, "Nomi (ruscha):", "Название (по-русски):"), reply_markup=ortga_kb(cid))
        return

    if qadam == "taom_yangi_ru":
        h = holat[cid]
        tid = db.taom_qosh(h["taom_nom_uz"], matn, h["mahsulot_id"])
        holat[cid]["taom_id"] = tid
        holat[cid]["qadam"] = "taom_kg"
        holat[cid]["qism"] = "Umumiy"
        bot.send_message(cid, t(cid, "✅ Taom qo'shildi! Necha kg?", "✅ Блюдо добавлено! Сколько кг?"), reply_markup=ortga_kb(cid))
        return

    if qadam == "taom_qism":
        holat[cid]["qism"] = matn
        holat[cid]["qadam"] = "taom_kg"
        bot.send_message(cid, t(cid, f"{matn} dan necha kg?", f"Сколько кг из {matn}?"), reply_markup=ortga_kb(cid))
        return

    if qadam == "taom_kg":
        try:
            kg = float(matn.replace(",", "."))
            if kg <= 0: raise ValueError
        except:
            bot.send_message(cid, t(cid, "Son kiriting!", "Введите число!"))
            return
        holat[cid]["kg"] = kg
        holat[cid]["qadam"] = "taom_porsiya"
        bot.send_message(cid, t(cid, "Necha porsiya?", "Сколько порций?"), reply_markup=ortga_kb(cid))
        return

    if qadam == "taom_porsiya":
        try:
            porsiya = int(matn)
        except:
            porsiya = 0
        holat[cid]["porsiya"] = porsiya
        holat[cid]["qadam"] = "taom_narx"
        bot.send_message(cid, t(cid, "Narx (so'm/kg)? 0 yozing agar kerak emas:", "Цена (сум/кг)? 0 если не нужно:"), reply_markup=ortga_kb(cid))
        return

    if qadam == "taom_narx":
        try:
            narx = float(matn.replace(",", "."))
        except:
            narx = 0
        h = holat[cid]
        db.taom_yoz(h["taom_id"], h["mahsulot_id"], h.get("qism","Umumiy"), h["kg"], h["porsiya"], narx, cid)
        taomlar_list = db.taomlar_ol(h["mahsulot_id"])
        t_obj = next((x for x in taomlar_list if x["id"] == h["taom_id"]), None)
        t_nomi = nom(t_obj, cid) if t_obj else ""
        holat[cid] = {"qadam": "asosiy"}
        javob = t(cid,
            f"✅ Taom saqlandi!\n{t_nomi}: {h['kg']} kg, {h['porsiya']} porsiya",
            f"✅ Блюдо сохранено!\n{t_nomi}: {h['kg']} кг, {h['porsiya']} порций"
        )
        bot.send_message(cid, javob, reply_markup=asosiy_menyu(cid))
        _menejerga(cid, javob)
        return

    # ═══════════════════════════════════════════════════════
    #  HISOBOT
    # ═══════════════════════════════════════════════════════
    if matn in ["📊 Hisobot", "📊 Отчёт"]:
        holat[cid] = {"qadam": "hisobot_tur"}
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add(
            t(cid, "📅 Bugun", "📅 Сегодня"),
            t(cid, "📆 Kecha", "📆 Вчера"),
            t(cid, "🗓 Hafta", "🗓 Неделя"),
            t(cid, "🗓 Oy", "🗓 Месяц"),
            t(cid, "🔙 Ortga", "🔙 Назад"),
        )
        bot.send_message(cid, t(cid, "Qaysi davr?", "Какой период?"), reply_markup=kb)
        return

    if qadam == "hisobot_tur":
        bugun = datetime.now().strftime("%Y-%m-%d")
        kecha = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if matn in [t(cid,"📅 Bugun","📅 Сегодня")]:
            _hisobot_yuborish(cid, bugun)
        elif matn in [t(cid,"📆 Kecha","📆 Вчера")]:
            _hisobot_yuborish(cid, kecha)
        elif matn in [t(cid,"🗓 Hafta","🗓 Неделя")]:
            for i in range(7):
                s = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                _hisobot_yuborish(cid, s)
        elif matn in [t(cid,"🗓 Oy","🗓 Месяц")]:
            bot.send_message(cid, t(cid, "Oylik hisobot tayyorlanmoqda...", "Формируется месячный отчёт..."))
            for i in range(30):
                s = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                _hisobot_yuborish(cid, s)
        holat[cid] = {"qadam": "asosiy"}
        bot.send_message(cid, t(cid, "Asosiy menyu", "Главное меню"), reply_markup=asosiy_menyu(cid))
        return

    # ═══════════════════════════════════════════════════════
    #  SKLAD
    # ═══════════════════════════════════════════════════════
    if matn in ["📋 Sklad", "📋 Склад"]:
        sklad = db.sklad_holati()
        if not sklad:
            bot.send_message(cid, t(cid, "Sklad bo'sh.", "Склад пуст."), reply_markup=asosiy_menyu(cid))
            return
        lines = [t(cid, "📋 *Sklad holati*", "📋 *Состояние склада*")]
        for s in sklad:
            n = s.get("nom_uz") if u["til"] == "uz" else s.get("nom_ru", s.get("nom_uz"))
            q = s.get("qoldiq_kg", 0)
            icon = "✅" if q > 2 else ("⚠️" if q > 0 else "❌")
            lines.append(f"{icon} {n}: *{round(q,1)} kg*")
        bot.send_message(cid, "\n".join(lines), parse_mode="Markdown", reply_markup=asosiy_menyu(cid))
        return

# ── YORDAMCHI FUNKSIYALAR ──────────────────────────────────

def _guruh_kb(cid, savol, faqat_gosht=False):
    guruhlar = db.guruhlar_ol()
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for g in guruhlar:
        if faqat_gosht and g.get("tur") != "gosht":
            continue
        n = g["nom_uz"] if db.foydalanuvchi_ol(cid)["til"] == "uz" else g["nom_ru"]
        kb.add(types.KeyboardButton(n))
    kb.add(types.KeyboardButton(t(cid, "🔙 Ortga", "🔙 Назад")))
    bot.send_message(cid, savol, reply_markup=kb)

def _guruh_top(cid, matn):
    guruhlar = db.guruhlar_ol()
    u = db.foydalanuvchi_ol(cid)
    for g in guruhlar:
        n = g["nom_uz"] if u["til"] == "uz" else g["nom_ru"]
        if n == matn:
            return g
    return None

def _mahsulot_kb(cid, guruh_id, savol, qism_kerak=False):
    mahsulotlar = db.mahsulotlar_ol(guruh_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for m in mahsulotlar:
        kb.add(types.KeyboardButton(nom(m, cid)))
    kb.add(types.KeyboardButton(t(cid, "➕ Yangi mahsulot", "➕ Новый продукт")))
    kb.add(types.KeyboardButton(t(cid, "🔙 Ortga", "🔙 Назад")))
    bot.send_message(cid, savol, reply_markup=kb)

def _mahsulot_top(cid, guruh_id, matn):
    mahsulotlar = db.mahsulotlar_ol(guruh_id)
    for m in mahsulotlar:
        if nom(m, cid) == matn:
            return m
    return None

def _qism_kb(cid, qismlar, natijalari=None):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kirilgan = {n["qism"] for n in (natijalari or [])}
    for q in qismlar:
        if q and q not in kirilgan:
            kb.add(types.KeyboardButton(q))
    kb.add(types.KeyboardButton(t(cid, "➕ Yangi qism", "➕ Новая часть")))
    if natijalari:
        kb.add(types.KeyboardButton(t(cid, "✅ Tayyor", "✅ Готово")))
    kb.add(types.KeyboardButton(t(cid, "🔙 Ortga", "🔙 Назад")))
    holat[cid]["qadam"] = "kesish_qism"
    matn_sar = t(cid, "Qaysi qism?", "Какая часть?")
    if natijalari:
        yozilgan = "\n".join([f"  {n['qism']}: {n['kg']} kg" for n in natijalari])
        matn_sar += f"\n\n{t(cid, 'Kiritildi:', 'Введено:')}\n{yozilgan}"
    bot.send_message(cid, matn_sar, reply_markup=kb)

def _qism_tanla_kb(cid, qismlar):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for q in qismlar:
        if q:
            kb.add(types.KeyboardButton(q))
    kb.add(types.KeyboardButton(t(cid, "🔙 Ortga", "🔙 Назад")))
    holat[cid]["qadam"] = "taom_qism"
    bot.send_message(cid, t(cid, "Qaysi qismdan?", "Из какой части?"), reply_markup=kb)

def _taom_kb(cid, mahsulot_id):
    taomlar = db.taomlar_ol(mahsulot_id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for t_obj in taomlar:
        kb.add(types.KeyboardButton(nom(t_obj, cid)))
    kb.add(types.KeyboardButton(t(cid, "➕ Yangi taom", "➕ Новое блюдо")))
    kb.add(types.KeyboardButton(t(cid, "🔙 Ortga", "🔙 Назад")))
    bot.send_message(cid, t(cid, "Qaysi taom?", "Какое блюдо?"), reply_markup=kb)

def _kesish_saqlash(cid):
    h = holat[cid]
    for n in h["kesish_natijalari"]:
        db.kesish_qosh(h["kirim_id"], h["mahsulot_id"], n["qism"], n["kg"], cid)
    m = db.mahsulot_ol(h["mahsulot_id"])
    lines = [t(cid, f"✅ Kesish saqlandi — {nom(m,cid)}:", f"✅ Разделка сохранена — {nom(m,cid)}:")]
    for n in h["kesish_natijalari"]:
        lines.append(f"  {n['qism']}: {n['kg']} kg")
    javob = "\n".join(lines)
    holat[cid] = {"qadam": "asosiy"}
    bot.send_message(cid, javob, reply_markup=asosiy_menyu(cid))
    _menejerga(cid, javob)

def _hisobot_yuborish(cid, sana):
    data = db.kunlik_hisobot(sana)
    lines = [f"📊 *{sana}*"]
    if data["kirimlar"]:
        lines.append(t(cid, "\n📦 Kirimlar:", "\n📦 Приходы:"))
        for k in data["kirimlar"]:
            n = k["nom_uz"] if db.foydalanuvchi_ol(cid)["til"]=="uz" else k.get("nom_ru",k["nom_uz"])
            lines.append(f"  {n}: {round(k['jami_kg'],1)} kg")
    if data["kesishlar"]:
        lines.append(t(cid, "\n🔪 Kesish:", "\n🔪 Разделка:"))
        for k in data["kesishlar"]:
            lines.append(f"  {k['qism']}: {round(k['jami_kg'],1)} kg")
    if data["taomlar"]:
        lines.append(t(cid, "\n🍳 Taomlar:", "\n🍳 Блюда:"))
        for t_obj in data["taomlar"]:
            n = t_obj["nom_uz"] if db.foydalanuvchi_ol(cid)["til"]=="uz" else t_obj.get("nom_ru",t_obj["nom_uz"])
            lines.append(f"  {n}: {round(t_obj['jami_kg'],1)} kg, {t_obj['jami_porsiya']} porsiya")
    if len(lines) == 1:
        lines.append(t(cid, "  Ma'lumot yo'q", "  Нет данных"))
    bot.send_message(cid, "\n".join(lines), parse_mode="Markdown")

def _menejerga(cid, xabar_matni):
    if cid != MENEJER_ID:
        try:
            u = db.foydalanuvchi_ol(cid)
            ism = u["ism"] if u else "Noma'lum"
            vaqt = datetime.now().strftime("%H:%M")
            bot.send_message(
                MENEJER_ID,
                f"🔔 *{ism}* ({vaqt}):\n{xabar_matni}",
                parse_mode="Markdown"
            )
        except:
            pass

# ── ISHGA TUSHIRISH ────────────────────────────────────────
if __name__ == "__main__":
    print("✅ Oshxona boti ishga tushdi...")
    bot.infinity_polling()
