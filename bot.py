"""
Parser Bot — Telegram bot for managing parsing tasks.

Flow:
  /start → main menu
  Нова задача → вибрати джерело → ввести URL/запит → ввести ключові слова
               → вибрати інтервал → ввести канал → підтвердити → збережено
  /tasks  → список задач з кнопками вкл/викл/видалити
  /help   → довідка
"""
import asyncio
import logging
import os
import time
from collections import defaultdict

from dotenv import load_dotenv
from telegram import (
    Update, BotCommand,
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes,
)

import database as db
from scheduler import run_scheduler

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ConversationHandler states
(
    S_SOURCE, S_URL, S_KEYWORDS,
    S_INTERVAL, S_CHANNEL, S_CONFIRM
) = range(6)

# Sources
SOURCES = {
    "rss":     ("📡 RSS Feed",     "Будь-який RSS/Atom URL"),
    "google":  ("🔍 Google News",  "Пошуковий запит"),
    "olx":     ("🛒 OLX",          "Пошуковий запит або URL"),
    "rozetka": ("🛍 Rozetka",      "Назва товару"),
    "dou":     ("💼 DOU Jobs",     "Категорія: Python, JS, QA..."),
    "web":     ("🌐 Будь-який сайт", "URL сторінки"),
}

INTERVALS = [15, 30, 45, 60, 180, 360, 720, 1440]
INTERVAL_LABELS = {
    15: "15 хв", 30: "30 хв", 45: "45 хв", 60: "1 год",
    180: "3 год", 360: "6 год", 720: "12 год", 1440: "24 год",
}

# Rate limiting
_rate: dict[int, list[float]] = defaultdict(list)

_app: Application | None = None


def _rate_ok(tg_id: int, limit: int = 10, window: int = 60) -> bool:
    now = time.time()
    _rate[tg_id] = [t for t in _rate[tg_id] if now - t < window]
    if len(_rate[tg_id]) >= limit:
        return False
    _rate[tg_id].append(now)
    return True


# ── Keyboards ──────────────────────────────────────────────────────────────

def _source_kb() -> InlineKeyboardMarkup:
    rows = []
    for key, (label, _) in SOURCES.items():
        rows.append([InlineKeyboardButton(label, callback_data=f"src:{key}")])
    return InlineKeyboardMarkup(rows)


def _interval_kb() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i, mins in enumerate(INTERVALS):
        row.append(InlineKeyboardButton(
            INTERVAL_LABELS[mins], callback_data=f"int:{mins}"
        ))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _tasks_kb(tasks: list) -> InlineKeyboardMarkup:
    rows = []
    for t in tasks:
        status = "✅" if t["is_active"] else "⏸"
        rows.append([
            InlineKeyboardButton(
                f"{status} {t['name'][:25]}", callback_data=f"info:{t['id']}"
            )
        ])
    return InlineKeyboardMarkup(rows)


def _task_action_kb(task_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle_label = "⏸ Вимкнути" if is_active else "▶️ Увімкнути"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(toggle_label, callback_data=f"toggle:{task_id}"),
            InlineKeyboardButton("🗑 Видалити",  callback_data=f"delete:{task_id}"),
        ],
        [InlineKeyboardButton("← Назад", callback_data="back:tasks")],
    ])


# ── Helpers ────────────────────────────────────────────────────────────────

def _main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["➕ Нова задача", "📋 Мої задачі"],
         ["ℹ️ Довідка"]],
        resize_keyboard=True,
    )


async def _send_to_channel(channel_id: str, text: str, photo_url: str = "") -> None:
    if _app is None:
        return
    try:
        if photo_url and photo_url.startswith("http"):
            await _app.bot.send_photo(
                chat_id=channel_id,
                photo=photo_url,
                caption=text[:1024],
                parse_mode=ParseMode.HTML,
            )
        else:
            await _app.bot.send_message(
                chat_id=channel_id,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
            )
    except Exception as e:
        logger.warning("Send to channel %s failed: %s", channel_id, e)


# ── /start ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.upsert_user(user.id, user.first_name, user.username)
    await update.message.reply_text(
        f"Привіт, {user.first_name}! 👋\n\n"
        "🤖 <b>Parser Bot</b> — автоматичний збір даних з сайтів.\n\n"
        "Обери дію:",
        parse_mode=ParseMode.HTML,
        reply_markup=_main_menu_kb(),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "<b>Як користуватись Parser Bot:</b>\n\n"
        "1️⃣ Натисни <b>➕ Нова задача</b>\n"
        "2️⃣ Вибери джерело (OLX, RSS, Rozetka...)\n"
        "3️⃣ Введи пошуковий запит або URL\n"
        "4️⃣ Введи ключові слова для фільтрації\n"
        "5️⃣ Вибери інтервал перевірки\n"
        "6️⃣ Введи ID або @username каналу\n"
        "   (бот має бути адміном каналу!)\n\n"
        "<b>Управління задачами:</b>\n"
        "📋 <b>Мої задачі</b> — список, вмикати/вимикати/видаляти\n\n"
        "<b>Підтримувані джерела:</b>\n"
        "• RSS/Atom feeds\n"
        "• Google News (пошук по темі)\n"
        "• OLX Ukraine\n"
        "• Rozetka\n"
        "• DOU Jobs\n"
        "• Будь-який сайт (універсальний парсер)",
        parse_mode=ParseMode.HTML,
        reply_markup=_main_menu_kb(),
    )


# ── /tasks ─────────────────────────────────────────────────────────────────

async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_row = db.get_user(user.id)
    if not user_row:
        db.upsert_user(user.id, user.first_name, user.username)
        user_row = db.get_user(user.id)

    tasks = db.get_user_tasks(user_row["id"])
    if not tasks:
        await update.message.reply_text(
            "У тебе поки немає задач.\nНатисни <b>➕ Нова задача</b> щоб створити.",
            parse_mode=ParseMode.HTML,
            reply_markup=_main_menu_kb(),
        )
        return

    await update.message.reply_text(
        f"📋 <b>Твої задачі ({len(tasks)}):</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=_tasks_kb(tasks),
    )


async def on_task_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    task_id = int(q.data.split(":")[1])
    task = db.get_task(task_id)
    if not task:
        await q.edit_message_text("Задача не знайдена.")
        return

    count  = db.count_task_results(task_id)
    status = "✅ Активна" if task["is_active"] else "⏸ Призупинена"
    source = task["source_type"].upper()
    last   = task["last_run_at"][:16] if task["last_run_at"] else "ще не запускалась"
    next_  = task["next_run_at"][:16] if task["next_run_at"] else "—"

    text = (
        f"<b>{task['name']}</b>\n\n"
        f"Статус: {status}\n"
        f"Джерело: {source}\n"
        f"Запит: <code>{task['source_url'] or '—'}</code>\n"
        f"Ключові слова: {task['keywords'] or 'всі'}\n"
        f"Інтервал: {INTERVAL_LABELS.get(task['interval_min'], str(task['interval_min'])+'хв')}\n"
        f"Канал: {task['channel_id']}\n"
        f"Знайдено записів: {count}\n"
        f"Останній запуск: {last}\n"
        f"Наступний: {next_}"
    )
    await q.edit_message_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=_task_action_kb(task_id, bool(task["is_active"]))
    )


async def on_toggle_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    task_id  = int(q.data.split(":")[1])
    new_state = db.toggle_task(task_id)
    state_text = "увімкнена ✅" if new_state else "призупинена ⏸"
    task = db.get_task(task_id)
    await q.edit_message_text(
        f"Задача <b>{task['name'] if task else task_id}</b> {state_text}.",
        parse_mode=ParseMode.HTML,
    )


async def on_delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    task_id = int(q.data.split(":")[1])
    task = db.get_task(task_id)
    name = task["name"] if task else str(task_id)
    db.delete_task(task_id)
    await q.edit_message_text(f"Задача <b>{name}</b> видалена 🗑", parse_mode=ParseMode.HTML)


async def on_back_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    user = update.effective_user
    user_row = db.get_user(user.id)
    tasks = db.get_user_tasks(user_row["id"]) if user_row else []
    if not tasks:
        await q.edit_message_text("Задач немає.")
        return
    await q.edit_message_text(
        f"📋 <b>Твої задачі ({len(tasks)}):</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=_tasks_kb(tasks),
    )


# ── Conversation: Create Task ──────────────────────────────────────────────

async def conv_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "🆕 <b>Нова задача</b>\n\nКрок 1/5 — Вибери джерело:",
        parse_mode=ParseMode.HTML,
        reply_markup=_source_kb(),
    )
    return S_SOURCE


async def conv_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    key = q.data.split(":")[1]
    label, hint = SOURCES[key]
    context.user_data["source_type"] = key

    await q.edit_message_text(
        f"✅ Джерело: <b>{label}</b>\n\n"
        f"Крок 2/5 — Введи запит або URL\n"
        f"<i>Підказка: {hint}</i>",
        parse_mode=ParseMode.HTML,
    )
    return S_URL


async def conv_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["source_url"] = update.message.text.strip()
    await update.message.reply_text(
        "Крок 3/5 — Введи ключові слова через кому\n"
        "<i>Наприклад: iPhone, 128gb, нова</i>\n"
        "Або натисни <b>-</b> щоб отримувати всі результати:",
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardMarkup([["-"]], resize_keyboard=True),
    )
    return S_KEYWORDS


async def conv_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip()
    context.user_data["keywords"] = "" if raw == "-" else raw
    await update.message.reply_text(
        "Крок 4/5 — Вибери інтервал перевірки:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await update.message.reply_text(
        "⏱ Як часто перевіряти?",
        reply_markup=_interval_kb(),
    )
    return S_INTERVAL


async def conv_interval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    mins = int(q.data.split(":")[1])
    context.user_data["interval_min"] = mins

    await q.edit_message_text(
        f"✅ Інтервал: <b>{INTERVAL_LABELS[mins]}</b>\n\n"
        "Крок 5/5 — Введи <b>@username</b> або <b>ID</b> каналу\n"
        "<i>Бот повинен бути адміністратором каналу!</i>",
        parse_mode=ParseMode.HTML,
    )
    return S_CHANNEL


async def conv_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    channel = update.message.text.strip()
    if not channel.startswith("@") and not channel.lstrip("-").isdigit():
        await update.message.reply_text(
            "Введи @username каналу або числовий ID (наприклад -1001234567890):"
        )
        return S_CHANNEL

    context.user_data["channel_id"] = channel

    # Ask for task name
    source_key = context.user_data["source_type"]
    source_label = SOURCES[source_key][0]
    kw = context.user_data["keywords"] or "всі"
    interval = INTERVAL_LABELS[context.user_data["interval_min"]]

    await update.message.reply_text(
        "Останній крок — введи <b>назву задачі</b>\n"
        "<i>Наприклад: iPhone OLX, Вакансії Python</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove(),
    )
    return S_CONFIRM


async def conv_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()[:50]
    d    = context.user_data

    user = update.effective_user
    user_id = db.upsert_user(user.id, user.first_name, user.username)

    task_id = db.create_task(
        user_id      = user_id,
        name         = name,
        source_type  = d["source_type"],
        source_url   = d["source_url"],
        keywords     = d["keywords"],
        interval_min = d["interval_min"],
        channel_id   = d["channel_id"],
    )

    source_label = SOURCES[d["source_type"]][0]
    kw_text = d["keywords"] if d["keywords"] else "без фільтру"
    interval_text = INTERVAL_LABELS[d["interval_min"]]

    await update.message.reply_text(
        f"✅ <b>Задача створена!</b>\n\n"
        f"📌 Назва: <b>{name}</b>\n"
        f"📂 Джерело: {source_label}\n"
        f"🔍 Запит: <code>{d['source_url']}</code>\n"
        f"🏷 Ключові слова: {kw_text}\n"
        f"⏱ Інтервал: {interval_text}\n"
        f"📢 Канал: {d['channel_id']}\n\n"
        "Перший запуск відбудеться через ~1 хвилину.",
        parse_mode=ParseMode.HTML,
        reply_markup=_main_menu_kb(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def conv_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Скасовано.",
        reply_markup=_main_menu_kb(),
    )
    return ConversationHandler.END


# ── Text router (main menu buttons) ───────────────────────────────────────

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text == "📋 Мої задачі":
        await cmd_tasks(update, context)
    elif text == "ℹ️ Довідка":
        await cmd_help(update, context)
    else:
        await cmd_start(update, context)


# ── Setup ──────────────────────────────────────────────────────────────────

async def post_init(app: Application) -> None:
    global _app
    _app = app

    await app.bot.set_my_commands([
        BotCommand("start",  "Головне меню"),
        BotCommand("tasks",  "Мої задачі"),
        BotCommand("help",   "Довідка"),
    ])

    asyncio.get_event_loop().create_task(run_scheduler(_send_to_channel))
    logger.info("Scheduler task started.")


def main() -> None:
    global _app
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN is not set in .env")

    db.init_db()
    logger.info("Database initialized.")

    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    _app = app

    # Conversation handler for creating a task
    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^➕ Нова задача$"), conv_start),
            CommandHandler("new", conv_start),
        ],
        states={
            S_SOURCE:   [CallbackQueryHandler(conv_source,   pattern=r"^src:")],
            S_URL:      [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_url)],
            S_KEYWORDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_keywords)],
            S_INTERVAL: [CallbackQueryHandler(conv_interval, pattern=r"^int:")],
            S_CHANNEL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_channel)],
            S_CONFIRM:  [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_confirm)],
        },
        fallbacks=[CommandHandler("cancel", conv_cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("tasks", cmd_tasks))
    app.add_handler(conv)

    # Inline button handlers
    app.add_handler(CallbackQueryHandler(on_task_info,   pattern=r"^info:"))
    app.add_handler(CallbackQueryHandler(on_toggle_task, pattern=r"^toggle:"))
    app.add_handler(CallbackQueryHandler(on_delete_task, pattern=r"^delete:"))
    app.add_handler(CallbackQueryHandler(on_back_tasks,  pattern=r"^back:tasks$"))

    # Main menu text buttons
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, on_text
    ))

    logger.info("Parser Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
