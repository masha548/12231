import asyncio
import logging
import aiosqlite
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    BotCommand
)

# ================= НАСТРОЙКИ И КОНФИГУРАЦИЯ =================
BOT_TOKEN = "8970135216:AAHpetDJk9u-AiY96voZPi89bTwf-hCM5DY"
ADMIN_ID = 1302301841  # Твой Telegram ID
MANAGER_USERNAME = "N9tnns"  # Замени на username твоего менеджера без @

DB_PATH = "shop_database.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Каталог товаров/услуг для демонстрации
PRODUCTS = {
    "dev_landing": {
        "title": "⚡ Landing Page под ключ",
        "price": 12000,
        "description": "Современный одностраничный сайт с адаптивной версткой, анимациями и интеграцией заявок в Telegram.",
        "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80"
    },
    "tg_bot": {
        "title": "🤖 Telegram-бот для бизнеса",
        "price": 15000,
        "description": "Автоматизация продаж, сбор лидов, рассылки и кастомная панель администратора на aiogram 3.",
        "image": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80"
    },
    "mini_app": {
        "title": "📱 Telegram Web App",
        "price": 25000,
        "description": "Полноценное веб-приложение прямо внутри Telegram интерфейса: каталог, оплата, удобный UI/UX.",
        "image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80"
    }
}


# ================= РАБОТА С БАЗОЙ ДАННЫХ =================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                registered_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_key TEXT,
                customer_name TEXT,
                customer_phone TEXT,
                status TEXT,
                created_at TEXT
            )
        """)
        await db.commit()


async def register_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name, registered_at) VALUES (?, ?, ?, ?)",
            (user_id, username or "", full_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        await db.commit()


async def save_order(user_id: int, product_key: str, name: str, phone: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO orders (user_id, product_key, customer_name, customer_phone, status, created_at) 
               VALUES (?, ?, ?, ?, 'NEW', ?)""",
            (user_id, product_key, name, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        await db.commit()
        return cursor.lastrowid


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            users_count = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders") as cur:
            orders_count = (await cur.fetchone())[0]
    return users_count, orders_count


async def get_last_orders(limit=5):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
                "SELECT order_id, product_key, customer_name, customer_phone, created_at FROM orders ORDER BY order_id DESC LIMIT ?",
                (limit,)) as cursor:
            return await cursor.fetchall()


# ================= СОСТОЯНИЯ FSM =================
class OrderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


# ================= КЛАВИАТУРЫ (UI) =================
def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton(text=" Каталог услуг", callback_data="catalog"),
            InlineKeyboardButton(text="ℹ️ О нас / Стек", callback_data="about")
        ],
        [
            InlineKeyboardButton(text=" Оставить бриф", callback_data="quick_order"),
            InlineKeyboardButton(text=" Связь со мной", url=f"https://t.me/{MANAGER_USERNAME}")  # Изменили ссылку
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_catalog_keyboard(current_index: int = 0):
    keys = list(PRODUCTS.keys())
    current_key = keys[current_index]

    # Кнопки навигации пагинатора
    prev_index = (current_index - 1) % len(keys)
    next_index = (current_index + 1) % len(keys)

    nav_row = [
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{prev_index}"),
        InlineKeyboardButton(text=f"{current_index + 1} / {len(keys)}", callback_data="noop"),
        InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{next_index}")
    ]

    action_row = [
        InlineKeyboardButton(text=" Заказать расчет", callback_data=f"buy_{current_key}")
    ]

    back_row = [
        InlineKeyboardButton(text=" Главное меню", callback_data="to_main")
    ]

    return InlineKeyboardMarkup(inline_keyboard=[nav_row, action_row, back_row])


def get_cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_fsm")]]
    )


def get_admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=" Последние 5 заявок", callback_data="admin_last_orders")],  # Добавили кнопку
            [InlineKeyboardButton(text=" Обновить аналитику", callback_data="admin_stats")],
            [InlineKeyboardButton(text=" В меню", callback_data="to_main")]
        ]
    )


# ================= ХЕНДЛЕРЫ: СТАРТ И ОСНОВНОЕ МЕНЮ =================
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await register_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    caption = (
        f"👋 <b>Добро пожаловать, {message.from_user.first_name}!</b>\n\n"
        f"Это демонстрационный бот digital-агентства разработки.\n"
        f"Здесь вы можете изучить примеры услуг, рассчитать стоимость проекта "
        f"или оформить заявку прямо через бота.\n\n"
        f"<i>Выберите действие в меню ниже:</i>"
    )

    # Используем баннер-картинку
    banner_url = "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&q=80"
    await message.answer_photo(
        photo=banner_url,
        caption=caption,
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@dp.callback_query(F.data == "to_main")
async def cb_to_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    caption = (
        f" Главное меню студии разработки.\n\n"
        f"Изучите наши решения или оставьте заявку для консультации."
    )
    banner_url = "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800&q=80"

    media = InputMediaPhoto(media=banner_url, caption=caption, parse_mode="HTML")
    await call.message.edit_media(media=media, reply_markup=get_main_menu())
    await call.answer()


@dp.callback_query(F.data == "about")
async def cb_about(call: CallbackQuery):
    text = (
        "ℹ️ <b>О технологическом стеке</b>\n\n"
        "Данный бот разработан с использованием:\n"
        "• <b>Python 3.11+ & aiogram 3</b> (Асинхронная архитектура)\n"
        "• <b>SQLite + aiosqlite</b> (Неблокирующее хранилище данных)\n"
        "• <b>FSM Architecture</b> (Надежный пошаговый диалог)\n"
        "• <b>Dynamic Inline UI</b> (Пагинация без спама в чат)\n\n"
        "Готов к деплою на любой Linux VPS через Docker/Systemd."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=" Назад в меню", callback_data="to_main")]]
    )
    await call.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
    await call.answer()


# ================= ХЕНДЛЕРЫ: КАТАЛОГ И ПАГИНАЦИЯ =================
@dp.callback_query(F.data == "catalog")
async def cb_catalog(call: CallbackQuery):
    await show_catalog_page(call.message, page=0, is_edit=True)
    await call.answer()


@dp.callback_query(F.data.startswith("page_"))
async def cb_page(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    await show_catalog_page(call.message, page=page, is_edit=True)
    await call.answer()


async def show_catalog_page(message: Message, page: int, is_edit: bool = False):
    keys = list(PRODUCTS.keys())
    product = PRODUCTS[keys[page]]

    caption = (
        f"<b>{product['title']}</b>\n\n"
        f"{product['description']}\n\n"
        f" Ориентировочная стоимость: <b>от {product['price']:,} ₽</b>\n"
        f" Срок реализации: <b>от 3 до 7 рабочих дней</b>"
    )

    media = InputMediaPhoto(
        media=product["image"],
        caption=caption,
        parse_mode="HTML"
    )

    if is_edit:
        await message.edit_media(media=media, reply_markup=get_catalog_keyboard(page))
    else:
        await message.answer_photo(photo=product["image"], caption=caption, parse_mode="HTML",
                                   reply_markup=get_catalog_keyboard(page))


# ================= ХЕНДЛЕРЫ FSM: ОФОРМЛЕНИЕ ЗАЯВКИ =================
@dp.callback_query(F.data.startswith("buy_"))
async def cb_buy(call: CallbackQuery, state: FSMContext):
    product_key = call.data.replace("buy_", "")
    await state.update_data(product_key=product_key)
    await state.set_state(OrderStates.waiting_for_name)

    await call.message.delete()
    await call.message.answer(
        "📝 <b>Шаг 1 из 2: Ваше имя</b>\n\n"
        "Как к вам можно обращаться?",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()


@dp.callback_query(F.data == "quick_order")
async def cb_quick_order(call: CallbackQuery, state: FSMContext):
    await state.update_data(product_key="custom_request")
    await state.set_state(OrderStates.waiting_for_name)

    await call.message.delete()
    await call.message.answer(
        "📝 <b>Экспресс-заявка (Шаг 1 из 2)</b>\n\n"
        "Представьтесь, пожалуйста:",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )
    await call.answer()


@dp.callback_query(F.data == "cancel_fsm")
async def cb_cancel_fsm(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ Заполнение заявки отменено.", reply_markup=get_main_menu())
    await call.answer()


@dp.message(OrderStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer("Пожалуйста, введите корректное имя (минимум 2 символа).")
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(OrderStates.waiting_for_phone)

    await message.answer(
        "📞 <b>Шаг 2 из 2: Контактный телефон или Telegram-ник</b>\n\n"
        "Укажите номер телефона (например, +79991234567) или ваш юзернейм для подтверждения:",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@dp.message(OrderStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext, bot: Bot):
    phone = message.text.strip()
    # Простая валидация
    if len(phone) < 5:
        await message.answer("Слишком короткий контакт. Укажите реальный номер или юзернейм для связи:")
        return

    data = await state.get_data()
    product_key = data.get("product_key", "custom_request")
    product_name = PRODUCTS.get(product_key, {}).get("title", "Индивидуальный проект")
    user_name = data["name"]

    # Сохраняем в БД
    order_id = await save_order(
        user_id=message.from_user.id,
        product_key=product_key,
        name=user_name,
        phone=phone
    )

    await state.clear()

    # Сообщение клиенту
    success_text = (
        f"✅ <b>Заявка #{order_id} успешно отправлена!</b>\n\n"
        f"• <b>Услуга:</b> {product_name}\n"
        f"• <b>Имя:</b> {user_name}\n"
        f"• <b>Контакт:</b> {phone}\n\n"
        f"Наш специалист свяжется с вами в ближайшее время!"
    )
    await message.answer(success_text, parse_mode="HTML", reply_markup=get_main_menu())

    # Мгновенное оповещение администратора (ТЕБЕ)
    admin_notify = (
        f"🚨 <b>НОВАЯ ЗАЯВКА С БОТА! (#{order_id})</b>\n\n"
        f"👤 <b>Клиент:</b> {user_name} (@{message.from_user.username or 'без_юзернейма'})\n"
        f"📞 <b>Контакт:</b> {phone}\n"
        f"💼 <b>Продукт:</b> {product_name}\n"
        f"🆔 <b>ID пользователя:</b> <code>{message.from_user.id}</code>"
    )
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_notify, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")


# ================= АДМИН-ПАНЕЛЬ =================
@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа к панели администратора.")
        return

    users_count, orders_count = await get_stats()
    text = (
        "👑 <b>Панель администратора</b>\n\n"
        f"👥 Всего пользователей: <b>{users_count}</b>\n"
        f"📦 Всего заявок в базе: <b>{orders_count}</b>\n"
        f" Серверное время: <b>{datetime.now().strftime('%H:%M:%S')}</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_keyboard())


@dp.callback_query(F.data == "admin_stats")
async def cb_admin_stats(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Доступ запрещен.", show_alert=True)
        return

    users_count, orders_count = await get_stats()
    text = (
        "👑 <b>Панель администратора (Обновлено)</b>\n\n"
        f"👥 Всего пользователей: <b>{users_count}</b>\n"
        f"📦 Всего заявок в базе: <b>{orders_count}</b>\n"
        f" Серверное время: <b>{datetime.now().strftime('%H:%M:%S')}</b>"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_keyboard())
    await call.answer("Данные обновлены!")


# Хендлер для просмотра последних заявок
@dp.callback_query(F.data == "admin_last_orders")
async def cb_admin_last_orders(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Доступ запрещен.", show_alert=True)
        return

    orders = await get_last_orders()

    if not orders:
        await call.message.edit_text("Заявок пока нет.", reply_markup=get_admin_keyboard())
        return

    text = "📋 <b>Последние 5 заявок:</b>\n\n"
    for order_id, product_key, customer_name, customer_phone, created_at in orders:
        product_name = PRODUCTS.get(product_key, {}).get("title", "Индивидуальный проект")
        text += f"🔹 <b>#{order_id}</b> | {created_at}\n"
        text += f"Услуга: {product_name}\n"
        text += f"Имя: {customer_name}\n"
        text += f"Контакт: {customer_phone}\n\n"

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_keyboard())
    await call.answer()


# Заглушка для пустых кликов в пагинаторе
@dp.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()


# ================= ТОЧКА ВХОДА =================
async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)

    # Установка подсказок команд в Telegram меню
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню / Каталог"),
        BotCommand(command="admin", description="Админ-панель (только для владельца)")
    ])

    logger.info("Бот успешно запущен и готов к обработке сообщений!")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")