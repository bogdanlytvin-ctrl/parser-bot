"""
Parser Bot — multi-language, multi-country, multi-niche parsing bot.

Conversation flow (9 steps):
  /start → language select → main menu
  New task → country → niche (or custom) → source → url → keywords
           → interval → channel → AI filter → name → created
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
from lang import t
from niches import COUNTRY_NICHES, get_template

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ConversationHandler states
(
    S_LANG,
    S_COUNTRY, S_NICHE, S_SOURCE, S_URL, S_KEYWORDS,
    S_INTERVAL, S_CHANNEL, S_AI, S_NAME,
) = range(10)

COUNTRIES = ["ua", "us", "eu", "ca", "world"]

UA_SOURCES  = ["rss", "google", "olx", "rozetka", "dou", "telegram", "web"]
# International (no OLX/Rozetka/DOU)
INT_SOURCES = ["rss", "google", "telegram", "web"]

INTERVALS = [15, 30, 45, 60, 120, 240, 720, 1440]

# Rate limiting
_rate: dict[int, list[float]] = defaultdict(list)
_app: Application | None = None


def _rate_ok(tg_id: int, limit: int = 10, window: int = 60) -> bool:
    now = time.time()
    _rate[tg_id] = [ts for ts in _rate[tg_id] if now - ts < window]
    if len(_rate[tg_id]) >= limit:
        return False
    _rate[tg_id].append(now)
    return True


def _lang(context: ContextTypes.DEFAULT_TYPE, tg_id: int | None = None) -> str:
    return context.user_data.get("lang") or (
        db.get_user_lang(tg_id) if tg_id else "ua"
    )


# -- Keyboards --------------------------------------------------------------

def _lang_kb() -> InlineKeyboardMarkup:
    """Використовується під час /start (перший візит). Prefix: lang:"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇺🇦 Українська", callback_data="lang:ua"),
        InlineKeyboardButton("🇬🇧 English",    callback_data="lang:en"),
    ]])


def _settings_lang_kb() -> InlineKeyboardMarkup:
    """Використовується в /settings. Prefix: setlang:"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇺🇦 Українська", callback_data="setlang:ua"),
        InlineKeyboardButton("🇬🇧 English",    callback_data="setlang:en"),
    ]])


def _country_kb(lang: str) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for c in COUNTRIES:
        row.append(InlineKeyboardButton(t(lang, f"country_{c}"), callback_data=f"country:{c}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _niche_kb(lang: str, country: str) -> InlineKeyboardMarkup:
    niches = COUNTRY_NICHES.get(country, [])
    rows = []
    row = []
    for n in niches:
        row.append(InlineKeyboardButton(t(lang, f"niche_{n}"), callback_data=f"niche:{n}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(t(lang, "niche_custom"), callback_data="niche:custom")])
    return InlineKeyboardMarkup(rows)


def _source_kb(lang: str, country: str) -> InlineKeyboardMarkup:
    sources = UA_SOURCES if country == "ua" else INT_SOURCES
    rows = [[InlineKeyboardButton(t(lang, f"src_{s}"), callback_data=f"src:{s}")]
            for s in sources]
    return InlineKeyboardMarkup(rows)


def _interval_kb(lang: str) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for mins in INTERVALS:
        key = f"interval_{mins}"
        row.append(InlineKeyboardButton(t(lang, key), callback_data=f"int:{mins}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _ai_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t(lang, "btn_ai_yes"), callback_data="ai:yes"),
        InlineKeyboardButton(t(lang, "btn_ai_no"),  callback_data="ai:no"),
    ]])


def _skip_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[t(lang, "btn_skip")]], resize_keyboard=True)


def _main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[t(lang, "btn_new_task"), t(lang, "btn_my_tasks")],
         [t(lang, "btn_settings"), t(lang, "btn_help")]],
        resize_keyboard=True,
    )


def _tasks_kb(tasks: list) -> InlineKeyboardMarkup:
    rows = []
    for task in tasks:
        status = "✅" if task["is_active"] else "⏸"
        rows.append([InlineKeyboardButton(
            f"{status} {task['name'][:28]}", callback_data=f"info:{task['id']}"
        )])
    return InlineKeyboardMarkup(rows)


def _task_action_kb(lang: str, task_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle = "⏸ Pause" if is_active else "▶️ Resume"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(toggle,              callback_data=f"toggle:{task_id}"),
            InlineKeyboardButton(t(lang, "btn_delete"), callback_data=f"delete:{task_id}"),
        ],
        [InlineKeyboardButton(t(lang, "btn_back"), callback_data="back:tasks")],
    ])


# -- Send to channel --------------------------------------------------------

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


# -- /start -----------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    db.upsert_user(user.id, user.first_name, user.username)
    row = db.get_user(user.id)

    # First visit — ask language
    if not row or not row["lang"]:
        await update.message.reply_text(
            t("ua", "welcome", name=user.first_name),
            parse_mode=ParseMode.HTML,
            reply_markup=_lang_kb(),
        )
        return S_LANG

    lang = row["lang"]
    context.user_data["lang"] = lang
    tasks = db.get_user_tasks(row["id"])
    active = sum(1 for t_ in tasks if t_["is_active"])
    await update.message.reply_text(
        t(lang, "main_menu", count=active),
        reply_markup=_main_menu_kb(lang),
    )
    return ConversationHandler.END


async def on_lang_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = q.data.split(":")[1]
    db.set_user_lang(q.from_user.id, lang)
    context.user_data["lang"] = lang

    row = db.get_user(q.from_user.id)
    tasks = db.get_user_tasks(row["id"]) if row else []
    active = sum(1 for t_ in tasks if t_["is_active"])
    await q.edit_message_text(
        t(lang, "main_menu", count=active),
    )
    await q.message.reply_text(
        t(lang, "main_menu", count=active),
        reply_markup=_main_menu_kb(lang),
    )
    return ConversationHandler.END


# -- /settings --------------------------------------------------------------

async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(context, update.effective_user.id)
    await update.message.reply_text(
        t(lang, "settings_menu"),
        reply_markup=_settings_lang_kb(),
    )


async def on_settings_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє зміну мови з /settings (prefix setlang:)."""
    q = update.callback_query
    await q.answer()
    new_lang = q.data.split(":")[1]
    db.set_user_lang(q.from_user.id, new_lang)
    context.user_data["lang"] = new_lang
    await q.edit_message_text(
        t(new_lang, "lang_changed"),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Menu", callback_data="back:tasks"),
        ]]),
    )


# -- /help ------------------------------------------------------------------

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(context, update.effective_user.id)
    await update.message.reply_text(
        t(lang, "help_text"),
        parse_mode=ParseMode.HTML,
        reply_markup=_main_menu_kb(lang),
    )


# -- /tasks -----------------------------------------------------------------

async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    lang = _lang(context, user.id)
    row  = db.get_user(user.id)
    if not row:
        db.upsert_user(user.id, user.first_name, user.username)
        row = db.get_user(user.id)

    tasks = db.get_user_tasks(row["id"])
    if not tasks:
        await update.message.reply_text(
            t(lang, "no_tasks"),
            reply_markup=_main_menu_kb(lang),
        )
        return

    await update.message.reply_text(
        f"📋 <b>{len(tasks)}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=_tasks_kb(tasks),
    )


async def on_task_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    lang    = _lang(context, q.from_user.id)
    task_id = int(q.data.split(":")[1])
    task    = db.get_task(task_id)
    if not task:
        await q.edit_message_text("Not found.")
        return

    count  = db.count_task_results(task_id)
    status = t(lang, "status_active") if task["is_active"] else t(lang, "status_paused")
    ai_txt = t(lang, "ai_on") if task["ai_filter"] else t(lang, "ai_off")
    last   = task["last_run_at"][:16] if task["last_run_at"] else t(lang, "never")

    text = t(lang, "task_info",
             name=task["name"],
             source_type=task["source_type"].upper(),
             country=(task["country"] or "ua").upper(),
             interval=task["interval_min"],
             channel=task["channel_id"],
             ai=ai_txt,
             status=status,
             results=count,
             last_run=last)

    await q.edit_message_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=_task_action_kb(lang, task_id, bool(task["is_active"]))
    )


async def on_toggle_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    lang    = _lang(context, q.from_user.id)
    task_id = int(q.data.split(":")[1])
    new_state = db.toggle_task(task_id)
    task = db.get_task(task_id)
    name = task["name"] if task else str(task_id)
    msg  = t(lang, "task_resumed", name=name) if new_state else t(lang, "task_paused", name=name)
    await q.edit_message_text(msg, parse_mode=ParseMode.HTML)


async def on_delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    lang    = _lang(context, q.from_user.id)
    task_id = int(q.data.split(":")[1])
    db.delete_task(task_id)
    await q.edit_message_text(t(lang, "task_deleted"), parse_mode=ParseMode.HTML)


async def on_back_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    lang = _lang(context, q.from_user.id)
    row  = db.get_user(q.from_user.id)
    tasks = db.get_user_tasks(row["id"]) if row else []
    if not tasks:
        await q.edit_message_text(t(lang, "no_tasks"))
        return
    await q.edit_message_text(
        f"📋 <b>{len(tasks)}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=_tasks_kb(tasks),
    )


# -- Conversation: Create Task ---------------------------------------------

async def conv_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    user = update.effective_user
    lang = db.get_user_lang(user.id)
    context.user_data["lang"] = lang

    await update.message.reply_text(
        t(lang, "step_country"),
        reply_markup=_country_kb(lang),
    )
    return S_COUNTRY


async def conv_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang    = context.user_data.get("lang", "ua")
    country = q.data.split(":")[1]
    context.user_data["country"] = country

    await q.edit_message_text(
        t(lang, "step_niche"),
        reply_markup=_niche_kb(lang, country),
    )
    return S_NICHE


async def conv_niche(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang    = context.user_data.get("lang", "ua")
    country = context.user_data.get("country", "ua")
    niche   = q.data.split(":")[1]
    context.user_data["niche"] = niche

    if niche == "custom":
        await q.edit_message_text(
            t(lang, "step_source"),
            reply_markup=_source_kb(lang, country),
        )
        return S_SOURCE

    # Apply template
    tpl = get_template(country, niche)
    if tpl:
        context.user_data["source_type"] = tpl.source_type
        context.user_data["source_url"]  = tpl.source_url
        context.user_data["keywords"]    = tpl.keywords
        context.user_data["task_name_suggestion"] = (
            tpl.name_ua if lang == "ua" else tpl.name_en
        )

        msg = t(lang, "tpl_applied",
                name=(tpl.name_ua if lang == "ua" else tpl.name_en),
                source_type=tpl.source_type.upper(),
                url=tpl.source_url[:60],
                keywords=tpl.keywords or "—")

        await q.edit_message_text(
            msg,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t(lang, "btn_accept_tpl"), callback_data="tpl:accept"),
                InlineKeyboardButton("✏️ Edit URL",            callback_data="tpl:edit"),
            ]]),
        )
        return S_URL
    else:
        await q.edit_message_text(
            t(lang, "step_source"),
            reply_markup=_source_kb(lang, country),
        )
        return S_SOURCE


async def conv_tpl_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User accepted or wants to edit the niche template."""
    q = update.callback_query
    await q.answer()
    lang   = context.user_data.get("lang", "ua")
    choice = q.data.split(":")[1]

    if choice == "accept":
        # Skip URL/keywords — go straight to interval
        await q.edit_message_text(t(lang, "step_interval"),
                                   reply_markup=_interval_kb(lang))
        return S_INTERVAL
    else:
        # Edit: show URL prompt with pre-filled value
        await q.edit_message_text(
            t(lang, "step_url") + f"\n\n<code>{context.user_data.get('source_url', '')}</code>",
            parse_mode=ParseMode.HTML,
        )
        return S_URL


async def conv_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ua")
    context.user_data["source_type"] = q.data.split(":")[1]

    await q.edit_message_text(t(lang, "step_url"), parse_mode=ParseMode.HTML)
    return S_URL


async def conv_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "ua")
    context.user_data["source_url"] = update.message.text.strip()

    await update.message.reply_text(
        t(lang, "step_keywords"),
        reply_markup=_skip_kb(lang),
    )
    return S_KEYWORDS


async def conv_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "ua")
    raw  = update.message.text.strip()
    context.user_data["keywords"] = "" if raw == t(lang, "btn_skip") else raw

    await update.message.reply_text("✅", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_text(
        t(lang, "step_interval"),
        reply_markup=_interval_kb(lang),
    )
    return S_INTERVAL


async def conv_interval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ua")
    context.user_data["interval_min"] = int(q.data.split(":")[1])

    await q.edit_message_text(t(lang, "step_channel"), parse_mode=ParseMode.HTML)
    return S_CHANNEL


async def conv_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang    = context.user_data.get("lang", "ua")
    channel = update.message.text.strip()

    if not channel.startswith("@") and not channel.lstrip("-").isdigit():
        await update.message.reply_text(t(lang, "step_channel"), parse_mode=ParseMode.HTML)
        return S_CHANNEL

    context.user_data["channel_id"] = channel
    await update.message.reply_text(t(lang, "step_ai"), reply_markup=_ai_kb(lang))
    return S_AI


async def conv_ai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ua")
    context.user_data["ai_filter"] = (q.data == "ai:yes")

    suggestion = context.user_data.get("task_name_suggestion", "")
    hint = f"\n<i>{suggestion}</i>" if suggestion else ""
    await q.edit_message_text(
        t(lang, "step_name") + hint,
        parse_mode=ParseMode.HTML,
    )
    return S_NAME


async def conv_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "ua")
    name = update.message.text.strip()[:50]
    d    = context.user_data

    user    = update.effective_user
    user_id = db.upsert_user(user.id, user.first_name, user.username)

    db.create_task(
        user_id      = user_id,
        name         = name,
        source_type  = d.get("source_type", "rss"),
        source_url   = d.get("source_url", ""),
        keywords     = d.get("keywords", ""),
        interval_min = d.get("interval_min", 60),
        channel_id   = d.get("channel_id", ""),
        country      = d.get("country", "ua"),
        niche        = d.get("niche", "custom"),
        ai_filter    = d.get("ai_filter", False),
    )

    ai_txt = t(lang, "ai_on") if d.get("ai_filter") else t(lang, "ai_off")
    await update.message.reply_text(
        t(lang, "task_created",
          name=name,
          source_type=d.get("source_type", "").upper(),
          country=d.get("country", "ua").upper(),
          interval=d.get("interval_min", 60),
          channel=d.get("channel_id", ""),
          ai=ai_txt),
        parse_mode=ParseMode.HTML,
        reply_markup=_main_menu_kb(lang),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def conv_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "ua")
    context.user_data.clear()
    await update.message.reply_text(
        t(lang, "task_cancelled"),
        reply_markup=_main_menu_kb(lang),
    )
    return ConversationHandler.END


# -- Text router -----------------------------------------------------------

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    lang = _lang(context, user.id)
    text = update.message.text

    if text == t(lang, "btn_my_tasks") or text == t("ua", "btn_my_tasks") or text == t("en", "btn_my_tasks"):
        await cmd_tasks(update, context)
    elif text == t(lang, "btn_settings") or text == t("ua", "btn_settings") or text == t("en", "btn_settings"):
        await cmd_settings(update, context)
    elif text == t(lang, "btn_help") or text == t("ua", "btn_help") or text == t("en", "btn_help"):
        await cmd_help(update, context)
    else:
        row = db.get_user(user.id)
        lang = row["lang"] if row else "ua"
        tasks = db.get_user_tasks(row["id"]) if row else []
        active = sum(1 for t_ in tasks if t_["is_active"])
        await update.message.reply_text(
            t(lang, "main_menu", count=active),
            reply_markup=_main_menu_kb(lang),
        )


# -- Setup -----------------------------------------------------------------

async def post_init(app: Application) -> None:
    global _app
    _app = app

    await app.bot.set_my_commands([
        BotCommand("start",    "Main menu"),
        BotCommand("tasks",    "My tasks"),
        BotCommand("settings", "Language settings"),
        BotCommand("help",     "Help"),
        BotCommand("cancel",   "Cancel current action"),
    ])

    asyncio.create_task(run_scheduler(_send_to_channel))
    logger.info("Scheduler task started.")


def main() -> None:
    global _app
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN is not set in .env")

    db.init_db()
    logger.info("Database initialized.")

    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    _app = app

    # Зміна мови з /settings (окремий prefix, щоб не конфліктувати з start_conv)
    app.add_handler(CallbackQueryHandler(on_settings_lang, pattern=r"^setlang:"))

    # Conversation handler for creating a task
    conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^(➕ Нова задача|➕ New task)$"), conv_start
            ),
            CommandHandler("newtask", conv_start),
        ],
        states={
            S_COUNTRY:  [CallbackQueryHandler(conv_country,    pattern=r"^country:")],
            S_NICHE:    [CallbackQueryHandler(conv_niche,      pattern=r"^niche:")],
            S_SOURCE:   [CallbackQueryHandler(conv_source,     pattern=r"^src:")],
            S_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, conv_url),
                CallbackQueryHandler(conv_tpl_choice, pattern=r"^tpl:"),
            ],
            S_KEYWORDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_keywords)],
            S_INTERVAL: [CallbackQueryHandler(conv_interval,   pattern=r"^int:")],
            S_CHANNEL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_channel)],
            S_AI:       [CallbackQueryHandler(conv_ai,         pattern=r"^ai:")],
            S_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_name)],
        },
        fallbacks=[CommandHandler("cancel", conv_cancel)],
        allow_reentry=True,
    )

    # Start / settings (also handles first-visit language selection)
    start_conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            S_LANG: [CallbackQueryHandler(on_lang_select, pattern=r"^lang:")],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    app.add_handler(start_conv)
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("tasks",    cmd_tasks))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(conv)

    # Inline button handlers for task management
    app.add_handler(CallbackQueryHandler(on_task_info,   pattern=r"^info:"))
    app.add_handler(CallbackQueryHandler(on_toggle_task, pattern=r"^toggle:"))
    app.add_handler(CallbackQueryHandler(on_delete_task, pattern=r"^delete:"))
    app.add_handler(CallbackQueryHandler(on_back_tasks,  pattern=r"^back:tasks$"))

    # Main menu text buttons
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.info("Parser Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
