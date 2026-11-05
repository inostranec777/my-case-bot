import asyncio
import logging
import aiosqlite
import random
import os
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_PATH = "cases.db"

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()

# Хранилище выбранных предметов для крафта
craft_baskets = {}
case_results_cache = {} # Память для хранения выпавших предметов (для листания)

if "RAILWAY_ENVIRONMENT" in os.environ:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
else:
    session = AiohttpSession(proxy="http://127.0.0.1:10809")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML), session=session)

# ==========================================
# НАСТРОЙКИ КЕЙСОВ И ПРЕДМЕТОВ (102 ШТУКИ)
# ==========================================
ITEMS = {
    # --- ОБЫЧНЫЕ (1-20) ---
    "common_1": {"name": "Ржавый ключ", "rarity": "Обычный", "chance": 40, "price": 50, "emoji": "🔑"},
    "common_2": {"name": "Мятая карта", "rarity": "Обычный", "chance": 35, "price": 60, "emoji": "🗺"},
    "common_3": {"name": "Пустая банка", "rarity": "Обычный", "chance": 30, "price": 70, "emoji": "🥫"},
    "common_4": {"name": "Сломанный чип", "rarity": "Обычный", "chance": 25, "price": 80, "emoji": "💾"},
    "common_5": {"name": "Рваный носок", "rarity": "Обычный", "chance": 20, "price": 90, "emoji": "🧦"},
    "common_6": {"name": "Камень", "rarity": "Обычный", "chance": 20, "price": 100, "emoji": "🪨"},
    "common_7": {"name": "Ветка", "rarity": "Обычный", "chance": 18, "price": 110, "emoji": "🌿"},
    "common_8": {"name": "Гвоздь", "rarity": "Обычный", "chance": 15, "price": 120, "emoji": "📌"},
    "common_9": {"name": "Осколок стекла", "rarity": "Обычный", "chance": 15, "price": 130, "emoji": "🔪"},
    "common_10": {"name": "Старая газета", "rarity": "Обычный", "chance": 12, "price": 140, "emoji": "📰"},
    "common_11": {"name": "Пластиковая бутылка", "rarity": "Обычный", "chance": 10, "price": 150, "emoji": "🧴"},
    "common_12": {"name": "Кубик льда", "rarity": "Обычный", "chance": 10, "price": 160, "emoji": "🧊"},
    "common_13": {"name": "Спичка", "rarity": "Обычный", "chance": 8, "price": 170, "emoji": "🔥"},
    "common_14": {"name": "Крышка", "rarity": "Обычный", "chance": 8, "price": 180, "emoji": "🍾"},
    "common_15": {"name": "Пробка", "rarity": "Обычный", "chance": 5, "price": 190, "emoji": "🍾"},
    "common_16": {"name": "Леденец", "rarity": "Обычный", "chance": 5, "price": 200, "emoji": "🍭"},
    "common_17": {"name": "Кусок мела", "rarity": "Обычный", "chance": 5, "price": 210, "emoji": "🖍"},
    "common_18": {"name": "Шнурок", "rarity": "Обычный", "chance": 4, "price": 220, "emoji": "👟"},
    "common_19": {"name": "Монетка", "rarity": "Обычный", "chance": 4, "price": 230, "emoji": "🪙"},
    "common_20": {"name": "Игрушка", "rarity": "Обычный", "chance": 3, "price": 250, "emoji": "🧸"},

    # --- НЕОБЫЧНЫЕ (21-40) ---
    "uncommon_1": {"name": "Медный провод", "rarity": "Необычный", "chance": 10, "price": 300, "emoji": "🔌"},
    "uncommon_2": {"name": "Шестеренка", "rarity": "Необычный", "chance": 9, "price": 350, "emoji": "⚙️"},
    "uncommon_3": {"name": "Стеклянный шарик", "rarity": "Необычный", "chance": 8, "price": 400, "emoji": "🔮"},
    "uncommon_4": {"name": "Компас", "rarity": "Необычный", "chance": 7, "price": 450, "emoji": "🧭"},
    "uncommon_5": {"name": "Старый телефон", "rarity": "Необычный", "chance": 7, "price": 500, "emoji": "☎️"},
    "uncommon_6": {"name": "Фонарик", "rarity": "Необычный", "chance": 6, "price": 550, "emoji": "🔦"},
    "uncommon_7": {"name": "Батарейка", "rarity": "Необычный", "chance": 6, "price": 600, "emoji": "🔋"},
    "uncommon_8": {"name": "Кассета", "rarity": "Необычный", "chance": 5, "price": 650, "emoji": "📼"},
    "uncommon_9": {"name": "Дискета", "rarity": "Необычный", "chance": 5, "price": 700, "emoji": "💾"},
    "uncommon_10": {"name": "Лупа", "rarity": "Необычный", "chance": 5, "price": 750, "emoji": "🔎"},
    "uncommon_11": {"name": "Брелок", "rarity": "Необычный", "chance": 4, "price": 800, "emoji": "🔑"},
    "uncommon_12": {"name": "Кубик Рубика", "rarity": "Необычный", "chance": 4, "price": 850, "emoji": "🧩"},
    "uncommon_13": {"name": "Дудка", "rarity": "Необычный", "chance": 4, "price": 900, "emoji": "🎺"},
    "uncommon_14": {"name": "Барабан", "rarity": "Необычный", "chance": 3, "price": 950, "emoji": "🥁"},
    "uncommon_15": {"name": "Гитара", "rarity": "Необычный", "chance": 3, "price": 1000, "emoji": "🎸"},
"uncommon_16": {"name": "Микрофон", "rarity": "Необычный", "chance": 3, "price": 1050, "emoji": "🎤"},
    "uncommon_17": {"name": "Наушники", "rarity": "Необычный", "chance": 2, "price": 1100, "emoji": "🎧"},
    "uncommon_18": {"name": "Часы", "rarity": "Необычный", "chance": 2, "price": 1150, "emoji": "⌚"},
    "uncommon_19": {"name": "Очки", "rarity": "Необычный", "chance": 2, "price": 1200, "emoji": "👓"},
    "uncommon_20": {"name": "Кошелек", "rarity": "Необычный", "chance": 2, "price": 1250, "emoji": "👛"},

    # --- РЕДКИЕ (41-60) ---
    "rare_1": {"name": "Синий кристалл", "rarity": "Редкий", "chance": 5, "price": 1500, "emoji": "💎"},
    "rare_2": {"name": "Серебряная монета", "rarity": "Редкий", "chance": 4.5, "price": 1800, "emoji": "🪙"},
    "rare_3": {"name": "Золотой компас", "rarity": "Редкий", "chance": 4, "price": 2000, "emoji": "🧭"},
    "rare_4": {"name": "Сапфир", "rarity": "Редкий", "chance": 3.5, "price": 2200, "emoji": "🔹"},
    "rare_5": {"name": "Изумруд", "rarity": "Редкий", "chance": 3, "price": 2500, "emoji": "🟢"},
    "rare_6": {"name": "Аметист", "rarity": "Редкий", "chance": 3, "price": 2800, "emoji": "🟣"},
    "rare_7": {"name": "Топаз", "rarity": "Редкий", "chance": 2.5, "price": 3000, "emoji": "🟡"},
    "rare_8": {"name": "Опал", "rarity": "Редкий", "chance": 2.5, "price": 3200, "emoji": "⚪"},
    "rare_9": {"name": "Гранат", "rarity": "Редкий", "chance": 2, "price": 3500, "emoji": "🔴"},
    "rare_10": {"name": "Жемчуг", "rarity": "Редкий", "chance": 2, "price": 3800, "emoji": "🦪"},
    "rare_11": {"name": "Кольцо", "rarity": "Редкий", "chance": 1.8, "price": 4000, "emoji": "💍"},
    "rare_12": {"name": "Ожерелье", "rarity": "Редкий", "chance": 1.8, "price": 4200, "emoji": "📿"},
    "rare_13": {"name": "Браслет", "rarity": "Редкий", "chance": 1.5, "price": 4500, "emoji": "🔗"},
    "rare_14": {"name": "Серьги", "rarity": "Редкий", "chance": 1.5, "price": 4800, "emoji": "💎"},
    "rare_15": {"name": "Корона принца", "rarity": "Редкий", "chance": 1.2, "price": 5000, "emoji": "👑"},
    "rare_16": {"name": "Скипетр", "rarity": "Редкий", "chance": 1.2, "price": 5200, "emoji": "🪄"},
    "rare_17": {"name": "Держава", "rarity": "Редкий", "chance": 1, "price": 5500, "emoji": "🔮"},
    "rare_18": {"name": "Меч рыцаря", "rarity": "Редкий", "chance": 1, "price": 5800, "emoji": "⚔️"},
    "rare_19": {"name": "Щит", "rarity": "Редкий", "chance": 0.8, "price": 6000, "emoji": "🛡"},
    "rare_20": {"name": "Шлем", "rarity": "Редкий", "chance": 0.8, "price": 6200, "emoji": "🪖"},

    # --- ЭПИЧЕСКИЕ (61-80) ---
    "epic_1": {"name": "Золотой слиток", "rarity": "Эпический", "chance": 2, "price": 8000, "emoji": "🧈"},
    "epic_2": {"name": "Огненный рубин", "rarity": "Эпический", "chance": 1.8, "price": 8500, "emoji": "🔴"},
    "epic_3": {"name": "Квантовый чип", "rarity": "Эпический", "chance": 1.5, "price": 9000, "emoji": "🖥"},
    "epic_4": {"name": "Кристалл льда", "rarity": "Эпический", "chance": 1.5, "price": 9500, "emoji": "❄️"},
    "epic_5": {"name": "Кристалл тьмы", "rarity": "Эпический", "chance": 1.2, "price": 10000, "emoji": "🖤"},
    "epic_6": {"name": "Кристалл света", "rarity": "Эпический", "chance": 1.2, "price": 10500, "emoji": "🤍"},
    "epic_7": {"name": "Свиток", "rarity": "Эпический", "chance": 1, "price": 11000, "emoji": "📜"},
    "epic_8": {"name": "Гримуар", "rarity": "Эпический", "chance": 1, "price": 11500, "emoji": "📕"},
    "epic_9": {"name": "Волшебная палочка", "rarity": "Эпический", "chance": 0.8, "price": 12000, "emoji": "🪄"},
    "epic_10": {"name": "Зелье", "rarity": "Эпический", "chance": 0.8, "price": 12500, "emoji": "🧪"},
    "epic_11": {"name": "Котел", "rarity": "Эпический", "chance": 0.7, "price": 13000, "emoji": "🍲"},
    "epic_12": {"name": "Метла", "rarity": "Эпический", "chance": 0.7, "price": 13500, "emoji": "🧹"},
"epic_13": {"name": "Мантия", "rarity": "Эпический", "chance": 0.6, "price": 14000, "emoji": "🥋"},
    "epic_14": {"name": "Шляпа мага", "rarity": "Эпический", "chance": 0.6, "price": 14500, "emoji": "🎩"},
    "epic_15": {"name": "Амулет", "rarity": "Эпический", "chance": 0.5, "price": 15000, "emoji": "🔱"},
    "epic_16": {"name": "Тотем", "rarity": "Эпический", "chance": 0.5, "price": 15500, "emoji": "🗿"},
    "epic_17": {"name": "Идол", "rarity": "Эпический", "chance": 0.4, "price": 16000, "emoji": "🗿"},
    "epic_18": {"name": "Реликвия", "rarity": "Эпический", "chance": 0.4, "price": 16500, "emoji": "🏺"},
    "epic_19": {"name": "Артефакт", "rarity": "Эпический", "chance": 0.3, "price": 17000, "emoji": "🔮"},
    "epic_20": {"name": "Око всевидящее", "rarity": "Эпический", "chance": 0.3, "price": 17500, "emoji": "👁"},

    # --- ЛЕГЕНДАРНЫЕ (81-90) ---
    "legend_1": {"name": "Крыло Дракона", "rarity": "Легендарный", "chance": 0.5, "price": 25000, "emoji": "🐉"},
    "legend_2": {"name": "Космический осколок", "rarity": "Легендарный", "chance": 0.4, "price": 28000, "emoji": "🌌"},
    "legend_3": {"name": "Меч Короля", "rarity": "Легендарный", "chance": 0.3, "price": 30000, "emoji": "⚔️"},
    "legend_4": {"name": "Яйцо Феникса", "rarity": "Легендарный", "chance": 0.2, "price": 35000, "emoji": "🥚"},
    "legend_5": {"name": "Перо Ангела", "rarity": "Легендарный", "chance": 0.2, "price": 40000, "emoji": "🪶"},
    "legend_6": {"name": "Рог Единорога", "rarity": "Легендарный", "chance": 0.15, "price": 45000, "emoji": "🦄"},
    "legend_7": {"name": "Клык Дракона", "rarity": "Легендарный", "chance": 0.15, "price": 50000, "emoji": "🦷"},
    "legend_8": {"name": "Чешуя Дракона", "rarity": "Легендарный", "chance": 0.1, "price": 55000, "emoji": "🛡"},
    "legend_9": {"name": "Сердце Голема", "rarity": "Легендарный", "chance": 0.1, "price": 60000, "emoji": "🪨"},
    "legend_10": {"name": "Глаз Титана", "rarity": "Легендарный", "chance": 0.05, "price": 65000, "emoji": "👁"},

    # --- МИФИЧЕСКИЕ (91-95) ---
    "mythic_1": {"name": "Корона Императора", "rarity": "Мифический", "chance": 0.1, "price": 100000, "emoji": "👑"},
    "mythic_2": {"name": "Слеза Бога", "rarity": "Мифический", "chance": 0.08, "price": 120000, "emoji": "💧"},
    "mythic_3": {"name": "Молот Тора", "rarity": "Мифический", "chance": 0.05, "price": 150000, "emoji": "🔨"},
    "mythic_4": {"name": "Трезубец Посейдона", "rarity": "Мифический", "chance": 0.03, "price": 180000, "emoji": "🔱"},
    "mythic_5": {"name": "Маска Анубиса", "rarity": "Мифический", "chance": 0.01, "price": 200000, "emoji": "🐺"},

    # --- ТАЙНЫЕ (96-100) ---
    "secret_1": {"name": "Черная Дыра", "rarity": "Тайный", "chance": 0.01, "price": 300000, "emoji": "🌑"},
    "secret_2": {"name": "Ключ от Вселенной", "rarity": "Тайный", "chance": 0.01, "price": 350000, "emoji": "🗝"},
    "secret_3": {"name": "Часы Вечности", "rarity": "Тайный", "chance": 0.005, "price": 400000, "emoji": "⏳"},
    "secret_4": {"name": "Книга Судеб", "rarity": "Тайный", "chance": 0.005, "price": 500000, "emoji": "📖"},
    "secret_5": {"name": "Око Создателя", "rarity": "Тайный", "chance": 0.001, "price": 1000000, "emoji": "👁‍🗨"},

    # --- БОЖЕСТВЕННЫЕ (101-102) ---
    "divine_1": {"name": "Свет Мироздания", "rarity": "Божественный", "chance": 0.0005, "price": 5000000, "emoji": "✨"},
    "divine_2": {"name": "Абсолют", "rarity": "Божественный", "chance": 0.0001, "price": 10000000, "emoji": "🌌"},
}

# Словарь с кейсами
CASES = {
    "case_1": {"name": "Стартовый кейс", "price": 500, "emoji": "📦", "items": ["common_1", "common_2", "common_3", "common_4", "common_5", "uncommon_1", "rare_1"]},
    "case_2": {"name": "Кейс Бродяги", "price": 1500, "emoji": "🎒", "items": ["common_10", "uncommon_1", "uncommon_5", "uncommon_10", "rare_5", "epic_1"]},
"case_3": {"name": "Серебряный кейс", "price": 3500, "emoji": "🥈", "items": ["uncommon_15", "rare_1", "rare_5", "rare_10", "rare_15", "epic_5", "legend_1"]},
    "case_4": {"name": "Золотой кейс", "price": 8000, "emoji": "👑", "items": ["rare_10", "rare_15", "rare_20", "epic_1", "epic_10", "legend_1", "legend_5", "legend_10"]},
    "case_5": {"name": "Кейс Дракона", "price": 15000, "emoji": "🐉", "items": ["rare_20", "epic_10", "epic_15", "legend_1", "legend_5", "legend_8", "mythic_1"]},
    "case_6": {"name": "Кейс Титана", "price": 30000, "emoji": "🗿", "items": ["epic_15", "epic_20", "legend_5", "legend_10", "mythic_1", "mythic_3", "secret_1"]},
    "case_7": {"name": "Кейс Бездны", "price": 60000, "emoji": "🌑", "items": ["legend_5", "legend_10", "mythic_1", "mythic_3", "mythic_5", "secret_1", "secret_5"]},
    "case_8": {"name": "Кейс Создателя", "price": 150000, "emoji": "✨", "items": ["mythic_1", "mythic_5", "secret_1", "secret_3", "secret_5", "divine_1", "divine_2"]},
}

# --- БАЗА ДАННЫХ ---
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS users
                         (
                             user_id
                             INTEGER
                             PRIMARY
                             KEY,
                             balance
                             INTEGER
                             DEFAULT
                             5000,
                             last_daily
                             INTEGER
                             DEFAULT
                             0
                         )
                         """)
        await db.execute(
            "CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, item_id TEXT NOT NULL)")
        try:
            await db.execute("ALTER TABLE users ADD COLUMN last_daily INTEGER DEFAULT 0")
        except Exception:
            pass
        await db.commit()


async def get_balance(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            else:
                await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
                await db.commit()
                return 5000


async def update_balance(user_id: int, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()


# --- КЛАВИАТУРЫ ---
def main_menu():
    kb = [
        [InlineKeyboardButton(text="🎁 Бесплатный кейс", callback_data="daily_case")],
        [InlineKeyboardButton(text="📦 Платные кейсы", callback_data="show_cases")],
        [InlineKeyboardButton(text="🎒 Инвентарь", callback_data="show_inventory"),
         InlineKeyboardButton(text="💰 Профиль", callback_data="show_profile")],
        [InlineKeyboardButton(text="🛠 Крафт (Апгрейд)", callback_data="show_craft")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


# --- ОБРАБОТЧИКИ ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await get_balance(message.from_user.id)
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"Добро пожаловать в симулятор кейсов.\n"
        f"Тебе начислено <b>5000</b> стартовых монет!\n\n"
        "Забирай бесплатный кейс раз в 24 часа и открывай платные кейсы!",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    # Возвращаем предметы из корзины, если игрок вышел
    if callback.from_user.id in craft_baskets and craft_baskets[callback.from_user.id]:
        async with aiosqlite.connect(DB_PATH) as db:
            for item_id in craft_baskets[callback.from_user.id]:
                await db.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)",
                                 (callback.from_user.id, item_id))
            await db.commit()
        craft_baskets[callback.from_user.id] = []

    await callback.message.edit_text("Главное меню:", reply_markup=main_menu())
    await callback.answer()


# --- ЕЖЕДНЕВНЫЙ БЕСПЛАТНЫЙ КЕЙС ---
@dp.callback_query(F.data == "daily_case")
async def daily_case(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    now = int(time.time())
    cooldown = 24 * 60 * 60

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            last_daily = row[0] if row else 0

    if now - last_daily < cooldown:
        time_left = cooldown - (now - last_daily)
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        await callback.answer(f"⏳ Следующий бесплатный кейс через {hours} ч. {minutes} мин.", show_alert=True)
        return

    await callback.message.edit_text("🎁 Открываем бесплатный кейс...")
    await asyncio.sleep(1.5)

    rand_num = random.randint(1, 100)
    current_chance = 0
    dropped_item_id = None
    for item_id, item_data in ITEMS.items():
        current_chance += item_data["chance"]
        if rand_num <= current_chance:
            dropped_item_id = item_id
            break
    if not dropped_item_id: dropped_item_id = list(ITEMS.keys())[0]

    item = ITEMS[dropped_item_id]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (user_id, dropped_item_id))
        await db.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (now, user_id))
        await db.commit()

    text = (
        f"🎉 <b>Бесплатный кейс открыт!</b>\n\n"
        f"Тебе выпало:\n"
        f"{item['emoji']} <b>{item['name']}</b> ({item['rarity']})\n"
        f"💰 Цена продажи: {item['price']} монет.\n\n"
        f"<i>Возвращайся через 24 часа за новым!</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎒 В инвентарь", callback_data="show_inventory")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# --- ПЛАТНЫЕ КЕЙСЫ ---
@dp.callback_query(F.data == "show_cases")
async def show_cases(callback: types.CallbackQuery):
    kb = []
    for case_id, case_data in CASES.items():
        kb.append([InlineKeyboardButton(text=f"{case_data['emoji']} {case_data['name']} ({case_data['price']} монет)",
                                        callback_data=f"select_case_{case_id}")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    await callback.message.edit_text("📦 <b>Выбери кейс для открытия:</b>",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await callback.answer()


@dp.callback_query(F.data.startswith("select_case_"))
async def select_case_amount(callback: types.CallbackQuery):
    case_id = callback.data.replace("select_case_", "")
    case_data = CASES[case_id]

    kb = [
        [InlineKeyboardButton(text="1 шт", callback_data=f"open_{case_id}_1"),
         InlineKeyboardButton(text="5 шт", callback_data=f"open_{case_id}_5"),
         InlineKeyboardButton(text="10 шт", callback_data=f"open_{case_id}_10")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_cases")]
    ]
    await callback.message.edit_text(
        f"📦 <b>{case_data['name']}</b>\n"
        f"Цена за 1 шт: {case_data['price']} монет.\n\n"
        f"Сколько кейсов открыть?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("open_"))
async def open_case(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    case_id = f"{parts[1]}_{parts[2]}"
    amount = int(parts[3])

    case_data = CASES[case_id]
    user_id = callback.from_user.id
    balance = await get_balance(user_id)
    total_price = case_data["price"] * amount

    if balance < total_price:
        await callback.answer(f"❌ Нужно {total_price} монет!", show_alert=True)
        return

    await update_balance(user_id, -total_price)
    await callback.message.edit_text(f"🎰 Открываем {amount} шт. {case_data['name']}...")
    await asyncio.sleep(1)

    possible_items = case_data["items"]
    total_chance = sum(ITEMS[item]["chance"] for item in possible_items)

    dropped_list = []
    async with aiosqlite.connect(DB_PATH) as db:
        for _ in range(amount):
            rand_num = random.uniform(1, total_chance)
            current_chance = 0
            dropped_item_id = possible_items[0]

            for item_id in possible_items:
                current_chance += ITEMS[item_id]["chance"]
                if rand_num <= current_chance:
                    dropped_item_id = item_id
                    break

            dropped_list.append(dropped_item_id)
            await db.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (user_id, dropped_item_id))
        await db.commit()

        async def show_case_result_page(callback: types.CallbackQuery, user_id: int, page: int):
            data = case_results_cache.get(user_id)
            if not data:
                await callback.answer("Результаты устарели, откройте кейс заново.", show_alert=True)
                return

            items = data["items"]
            items_per_page = 6  # Сколько предметов на одной странице
            total_pages = (len(items) + items_per_page - 1) // items_per_page

            start_idx = page * items_per_page
            end_idx = start_idx + items_per_page
            page_items = items[start_idx:end_idx]

            # Формируем текст
            text = f"🎉 <b>Открыто {data['amount']} шт. {data['case_name']}:</b>\n\n"
            text += f"👤 На странице: {len(page_items)} · стр. {page + 1}/{total_pages}\n\n"

            for idx, item_id in enumerate(page_items, start=start_idx + 1):
                item = ITEMS[item_id]
                # Пишем номер, эмодзи, название и цену
                text += f"{idx}. {item['emoji']} {item['name']} — {item['price']} монет\n"

            new_balance = await get_balance(user_id)
            text += f"\n💳 Твой баланс: {new_balance}."

            # Кнопки листания
            kb = []
            nav_row = []

            if page > 0:
                nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"respage_{page - 1}"))
            else:
                nav_row.append(InlineKeyboardButton(text="⬅️", callback_data="noop"))  # Пустая кнопка

            nav_row.append(InlineKeyboardButton(text=f"· {page + 1}/{total_pages} ·", callback_data="noop"))

            if page < total_pages - 1:
                nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"respage_{page + 1}"))
            else:
                nav_row.append(InlineKeyboardButton(text="➡️", callback_data="noop"))  # Пустая кнопка

            kb.append(nav_row)

            # Кнопки внизу
            kb.append([InlineKeyboardButton(text=f"🔄 Открыть еще {data['amount']} шт.",
                                            callback_data=f"open_{data['case_id']}_{data['amount']}")])
            kb.append([InlineKeyboardButton(text="🎒 В инвентарь", callback_data="show_inventory")])
            kb.append([InlineKeyboardButton(text="🔙 К выбору кейсов", callback_data="show_cases")])

            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
            await callback.answer()

        @dp.callback_query(F.data.startswith("respage_"))
        async def change_result_page(callback: types.CallbackQuery):
            page = int(callback.data.replace("respage_", ""))
            await show_case_result_page(callback, callback.from_user.id, page)

    # СОХРАНЯЕМ РЕЗУЛЬТАТЫ В ПАМЯТЬ ДЛЯ ЛИСТАНИЯ
    case_results_cache[user_id] = {
        "items": dropped_list,
        "case_name": case_data["name"],
        "amount": amount,
        "case_id": case_id
    }

    # Показываем первую страницу
    await show_case_result_page(callback, user_id, page=0)

# --- ИНВЕНТАРЬ, ПРОФИЛЬ, ПРОДАЖА ---
@dp.callback_query(F.data == "show_inventory")
async def show_inventory(callback: types.CallbackQuery):
    # Возвращаем предметы из корзины, если они там были
    if callback.from_user.id in craft_baskets and craft_baskets[callback.from_user.id]:
        async with aiosqlite.connect(DB_PATH) as db:
            for item_id in craft_baskets[callback.from_user.id]:
                await db.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)",
                                 (callback.from_user.id, item_id))
            await db.commit()
        craft_baskets[callback.from_user.id] = []

    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, item_id FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
            inv_items = await cursor.fetchall()

    if not inv_items:
        await callback.message.edit_text("🎒 Твой инвентарь пуст. Открывай кейсы!", reply_markup=main_menu())
        await callback.answer()
        return


    kb = []
    text = "🎒 <b>Твой инвентарь:</b>\n\n"
    for db_id, item_id in inv_items[:10]:
        item = ITEMS[item_id]
        text += f"{item['emoji']} {item['name']} — {item['price']} монет\n"
        kb.append([InlineKeyboardButton(text=f"Продать {item['emoji']} (+{item['price']})", callback_data=f"sell_{db_id}")])

    kb.append([InlineKeyboardButton(text="💰 Продать всё", callback_data="SellAllItems")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await callback.answer()


@dp.callback_query(F.data.startswith("sell_"))
async def sell_item(callback: types.CallbackQuery):
    db_id = int(callback.data.replace("sell_", ""))
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT item_id FROM inventory WHERE id = ? AND user_id = ?", (db_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await callback.answer("❌ Предмет не найден!", show_alert=True)
                return
            item_id = row[0]

        await db.execute("DELETE FROM inventory WHERE id = ?", (db_id,))
        await db.commit()

    item_price = ITEMS[item_id]["price"]
    await update_balance(user_id, item_price)
    await callback.answer(f"✅ Ты продал предмет за {item_price} монет!", show_alert=True)
    await show_inventory(callback)


@dp.callback_query(F.data == "SellAllItems")
async def sell_everything(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    total_earned = 0
    items_sold = 0

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, item_id FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
            inv_items = await cursor.fetchall()

        if not inv_items:
            await callback.answer("❌ У тебя нет предметов для продажи!", show_alert=True)
            return

        for db_id, item_id in inv_items:
            total_earned += ITEMS[item_id]["price"]
            items_sold += 1
            await db.execute("DELETE FROM inventory WHERE id = ?", (db_id,))

        await db.commit()

    await update_balance(user_id, total_earned)
    await callback.answer(f"✅ Продано {items_sold} шт. Получено {total_earned} монет!", show_alert=True)
    await show_inventory(callback)


@dp.callback_query(F.data == "show_profile")
async def show_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bal = await get_balance(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
            items_count = (await cursor.fetchone())[0]

    text = (
        f"👤 <b>Твой профиль:</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"💰 Баланс: <b>{bal}</b> монет\n"
        f"🎒 Предметов: <b>{items_count}</b>"
    )
    await callback.message.edit_text(text, reply_markup=main_menu())
    await callback.answer()


# --- АПГРЕЙД / КРАФТ ---
@dp.callback_query(F.data == "show_craft")
async def start_craft(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in craft_baskets and craft_baskets[user_id]:
        async with aiosqlite.connect(DB_PATH) as db:
            for item_id in craft_baskets[user_id]:
                await db.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (user_id, item_id))
            await db.commit()
    craft_baskets[user_id] = []
    await show_craft_inventory(callback, user_id)


async def show_craft_inventory(callback: types.CallbackQuery, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, item_id FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
            inv_items = await cursor.fetchall()


    kb = []
    text = "🛠 <b>Мастерская Апгрейда</b>\n\n"
    text += "Выбери от 3 до 10 предметов, чтобы попытать удачу!\n"
    text += "Если повезет — получишь предмет дороже. Если нет — предметы сгорят!\n\n"

    basket = craft_baskets.get(user_id, [])

    if basket:
        text += f"<b>В корзине: {len(basket)} шт.</b>\n\n"
        total_value = sum(ITEMS[item]["price"] for item in basket)
        text += f"💰 Стоимость корзины: {total_value} монет.\n\n"

    for db_id, item_id in inv_items[:10]:
        item = ITEMS[item_id]
        kb.append(
            [InlineKeyboardButton(text=f"Добавить {item['emoji']} {item['name']}", callback_data=f"craft_add_{db_id}")])

    if len(basket) >= 3:
        kb.append([InlineKeyboardButton(text="🔥 СКРЕСТИТЬ ПРЕДМЕТЫ", callback_data="craft_spin")])

    kb.append([InlineKeyboardButton(text="🗑 Очистить корзину (вернуть)", callback_data="clear_craft")])
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await callback.answer()


@dp.callback_query(F.data == "clear_craft")
async def clear_craft(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in craft_baskets:
        async with aiosqlite.connect(DB_PATH) as db:
            for item_id in craft_baskets[user_id]:
                await db.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (user_id, item_id))
            await db.commit()
        craft_baskets[user_id] = []
    await start_craft(callback)


@dp.callback_query(F.data.startswith("craft_add_"))
async def add_to_craft(callback: types.CallbackQuery):
    db_id = int(callback.data.replace("craft_add_", ""))
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT item_id FROM inventory WHERE id = ? AND user_id = ?", (db_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await callback.answer("❌ Предмет не найден!", show_alert=True)
                return
            item_id = row[0]

        await db.execute("DELETE FROM inventory WHERE id = ?", (db_id,))
        await db.commit()

    if user_id not in craft_baskets:
        craft_baskets[user_id] = []

    if len(craft_baskets[user_id]) >= 10:
        await callback.answer("❌ Максимум 10 предметов!", show_alert=True)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (user_id, item_id))
            await db.commit()
        return

    craft_baskets[user_id].append(item_id)
    await show_craft_inventory(callback, user_id)


@dp.callback_query(F.data == "craft_spin")
async def do_craft_spin(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    basket = craft_baskets.get(user_id, [])

    if len(basket) < 3:
        await callback.answer("❌ Нужно минимум 3 предмета!", show_alert=True)
        return

    total_value = sum(ITEMS[item]["price"] for item in basket)

    await callback.message.edit_text(
        f"🔥 Скрещиваем {len(basket)} предметов на общую сумму {total_value}...\n🎰 Крутим...")
    await asyncio.sleep(2)

    if random.randint(1, 100) <= 67:
        top_items = ["epic_5", "epic_10", "legend_1", "legend_5", "legend_10", "mythic_1", "secret_1"]
        dropped_item_id = random.choice(top_items)
        item = ITEMS[dropped_item_id]

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (user_id, dropped_item_id))
            await db.commit()

        text = (
            f"🎉 <b>УСПЕХ!</b>\n\n"
            f"Предметы успешно скрестились!\n"
            f"Ты получил: {item['emoji']} <b>{item['name']}</b> ({item['rarity']})\n"
            f"💰 Стоимость: {item['price']} монет."
        )
    else:
        text = (
            f"💀 <b>НЕУДАЧА.</b>\n\n"
            f"Предметы на сумму {total_value} монет просто сгорели в печи...\n"
            f"Повезет в следующий раз!"
        )

    craft_baskets[user_id] = []

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 В мастерскую", callback_data="show_craft")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="main_menu")]
    ])

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@dp.message(Command("cheat"))
async def cheat_money(message: Message):
    # Эта команда работает только для твоего ID (можно вписать свой)
    user_id = message.from_user.id
    await update_balance(user_id, 1000000)
    await message.answer("💰 <b>Чит-код активирован!</b>\nТебе начислено 1 000 000 монет для тестов.")

# --- ЗАПУСК ---
async def main():
    await init_db()
    print("Бот полностью обновлен и запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")