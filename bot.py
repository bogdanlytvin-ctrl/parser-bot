"""
Parser Bot — multi-language, multi-country, multi-niche parsing bot.

Conversation flows:
  /start → language select → main menu
  New task: country → niche → source → url → keywords → interval → channel → AI → name
  Edit task: pick field → enter new value → back to task info
"""
import asyncio
import logging
import os

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
from scheduler import run_scheduler, run_task_now
from lang import t
from niches import COUNTRY_NICHES, get_template

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ConversationHandler states
(
    S_LANG,
    S_COUNTRY, S_NICHE, S_SOURCE, S_URL, S_KEYWORDS,
    S_INTERVAL, S_CHANNEL, S_AI, S_NAME,
    S_EDIT_PICK, S_EDIT_NAME, S_EDIT_KEYWORDS, S_EDIT_INTERVAL, S_EDIT_CHANNEL,
) = range(15)

COUNTRIES    = ["ua", "us", "eu", "ca", "world"]
UA_SOURCES   = ["rss", "google", "olx", "rozetka", "dou", "telegram", "web"]
INT_SOURCES  = ["rss", "google", "telegram", "web"]
INTERVALS    = [15, 30, 45, 60, 120, 240, 720, 1440]

# Source-type URL hints
_URL_HINTS = {
    "rss":      "https://feeds.bbci.co.uk/news/world/rss.xml",
    "google":   "bitcoin crypto 2024",
    "olx":      "iPhone 14 Pro",
    "rozetka":  "MacBook Pro",
    "dou":      "Python",
    "telegram": "@channelname",
    "web":      "https://example.com/news",
}

_app: Application | None = None


def _lang(context: ContextTypes.DEFAULT_TYPE, tg_id: int | None = None) -> str:
    return context.user_data.get("lang") or (
        db.get_user_lang(tg_id) if tg_id else "ua"
    )


# ── Keyboards ──────────────────────────────────────────────────────────────

def _lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇺🇦 Українська", callback_data="lang:ua"),
        InlineKeyboardButton("🇬🇧 English",    callback_data="lang:en"),
    ]])


def _settings_lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇺🇦 Українська", callback_data="setlang:ua"),
        InlineKeyboardButton("🇬🇧 English",    callback_data="setlang:en"),
    ]])


def _country_kb(lang: str) -> InlineKeyboardMarkup:
    rows, row = [], []
    for c in COUNTRIES:
        row.append(InlineKeyboardButton(t(lang, f"country_{c}"), callback_data=f"country:{c}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _niche_kb(lang: str, country: str) -> InlineKeyboardMarkup:
    niches = COUNTRY_NICHES.get(country, [])
    rows, row = [], []
    for n in niches:
        row.append(InlineKeyboardButton(t(lang, f"niche_{n}"), callback_data=f"niche:{n}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(t(lang, "niche_custom"), callback_data="niche:custom")])
    return InlineKeyboardMarkup(rows)


def _source_kb(lang: str, country: str) -> InlineKeyboardMarkup:
    sources = UA_SOURCES if country == "ua" else INT_SOURCES
    rows = [[InlineKeyboardButton(t(lang, f"src_{s}"), callback_data=f"src:{s}")]
            for s in sources]
    return InlineKeyboardMarkup(rows)


def _interval_kb(lang: str, prefix: str = "int") -> InlineKeyboardMarkup:
    rows, row = [], []
    for mins in INTERVALS:
        row.append(InlineKeyboardButton(
            t(lang, f"interval_{mins}"), callback_data=f"{prefix}:{mins}"
        ))
        if len(row) == 4:
            rows.append(row); row = []
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
        icon = "✅" if task["is_active"] else "⏸"
        rows.append([InlineKeyboardButton(
            f"{icon} {task['name'][:30]}", callback_data=f"info:{task['id']}"
        )])
    return InlineKeyboardMarkup(rows)


def _task_action_kb(lang: str, task_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle = t(lang, "btn_pause") if is_active else t(lang, "btn_resume")
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(toggle,                callback_data=f"toggle:{task_id}"),
            InlineKeyboardButton(t(lang, "btn_run_now"), callback_data=f"run:{task_id}"),
        ],
        [
            InlineKeyboardButton(t(lang, "btn_edit"),   callback_data=f"edit:{task_id}"),
            InlineKeyboardButton(t(lang, "btn_delete"), callback_data=f"delete:{task_id}"),
        ],
        [InlineKeyboardButton(t(lang, "btn_back"), callback_data="back:tasks")],
    ])


def _edit_kb(lang: str, task_id: int, ai_state: bool) -> InlineKeyboardMarkup:
    ai_label = t(lang, "edit_ai_btn",
                 state=(t(lang, "ai_on") if ai_state else t(lang, "ai_off")))
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t(lang, "edit_name_btn"),     callback_data="ef:name"),
            InlineKeyboardButton(t(lang, "edit_kw_btn"),       callback_data="ef:keywords"),
        ],
        [
            InlineKeyboardButton(t(lang, "edit_interval_btn"), callback_data="ef:interval"),
            InlineKeyboardButton(t(lang, "edit_channel_btn"),  callback_data="ef:channel"),
        ],
        [InlineKeyboardButton(ai_label,                        callback_data="ef:ai")],
        [InlineKeyboardButton(t(lang, "btn_back"),             callback_data=f"info:{task_id}")],
    ])


# ── Helpers ────────────────────────────────────────────────────────────────

def _task_info_text(lang: str, task, count: int) -> str:
    status  = t(lang, "status_active") if task["is_active"] else t(lang, "status_paused")
    ai_txt  = t(lang, "ai_on")  if task["ai_filter"] else t(lang, "ai_off")
    last    = task["last_run_at"][:16].replace("T", " ") if task["last_run_at"] else t(lang, "never")
    next_   = task["next_run_at"][:16].replace("T", " ") if task["next_run_at"] else "—"
    url     = (task["source_url"] or t(lang, "no_url"))[:60]
    kw      = task["keywords"] or t(lang, "no_keywords")
    return t(lang, "task_info",
             name=task["name"],
             source_type=task["source_type"].upper(),
             country=(task["country"] or "ua").upper(),
             url=url, keywords=kw,
             interval=task["interval_min"],
             channel=task["channel_id"],
             ai=ai_txt, status=status,
             results=count,
             last_run=last, next_run=next_)


async def _send_to_channel(channel_id: str, text: str, photo_url: str = "") -> None:
    if _app is None:
        return
    try:
        if photo_url and photo_url.startswith("http"):
            await _app.bot.send_photo(
                chat_id=channel_id, photo=photo_url,
                caption=text[:1024], parse_mode=ParseMode.HTML,
            )
        else:
            await _app.bot.send_message(
                chat_id=channel_id, text=text,
                parse_mode=ParseMode.HTML, disable_web_page_preview=False,
            )
    except Exception as e:
        logger.warning("Send to channel %s failed: %s", channel_id, e)


# ── /start ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    db.upsert_user(user.id, user.first_name, user.username)
    row  = db.get_user(user.id)

    if not row or not row["lang"]:
        await update.message.reply_text(
            t("ua", "welcome", name=user.first_name),
            parse_mode=ParseMode.HTML,
            reply_markup=_lang_kb(),
        )
        return S_LANG

    lang = row["lang"]
    context.user_data["lang"] = lang
    tasks  = db.get_user_tasks(row["id"])
    active = sum(1 for t_ in tasks if t_["is_active"])
    await update.message.reply_text(
        t(lang, "main_menu", count=active),
        parse_mode=ParseMode.HTML,
        reply_markup=_main_menu_kb(lang),
    )
    return ConversationHandler.END


async def on_lang_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = q.data.split(":")[1]
    db.set_user_lang(q.from_user.id, lang)
    context.user_data["lang"] = lang

    row    = db.get_user(q.from_user.id)
    tasks  = db.get_user_tasks(row["id"]) if row else []
    active = sum(1 for t_ in tasks if t_["is_active"])
    await q.edit_message_text(t(lang, "main_menu", count=active), parse_mode=ParseMode.HTML)
    await q.message.reply_text(
        t(lang, "main_menu", count=active),
        parse_mode=ParseMode.HTML,
        reply_markup=_main_menu_kb(lang),
    )
    return ConversationHandler.END


# ── /settings ──────────────────────────────────────────────────────────────

async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(context, update.effective_user.id)
    lang_name = "Українська" if lang == "ua" else "English"
    await update.message.reply_text(
        t(lang, "settings_header", lang_name=lang_name),
        parse_mode=ParseMode.HTML,
        reply_markup=_settings_lang_kb(),
    )


async def on_settings_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    new_lang = q.data.split(":")[1]
    db.set_user_lang(q.from_user.id, new_lang)
    context.user_data["lang"] = new_lang
    await q.edit_message_text(
        t(new_lang, "lang_changed"),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Menu", callback_data="back:tasks"),
        ]]),
    )


# ── /help ──────────────────────────────────────────────────────────────────

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = _lang(context, update.effective_user.id)
    await update.message.reply_text(
        t(lang, "help_text"),
        parse_mode=ParseMode.HTML,
        reply_markup=_main_menu_kb(lang),
    )


# ── /tasks ─────────────────────────────────────────────────────────────────

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
            parse_mode=ParseMode.HTML,
            reply_markup=_main_menu_kb(lang),
        )
        return

    await update.message.reply_text(
        t(lang, "tasks_header", count=len(tasks)),
        parse_mode=ParseMode.HTML,
        reply_markup=_tasks_kb(tasks),
    )


# ── Task management (global callbacks) ─────────────────────────────────────

async def on_task_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    lang    = _lang(context, q.from_user.id)
    task_id = int(q.data.split(":")[1])
    task    = db.get_task(task_id)
    if not task:
        await q.edit_message_text("Not found.")
        return

    count = db.count_task_results(task_id)
    await q.edit_message_text(
        _task_info_text(lang, task, count),
        parse_mode=ParseMode.HTML,
        reply_markup=_task_action_kb(lang, task_id, bool(task["is_active"])),
    )


async def on_toggle_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    lang      = _lang(context, q.from_user.id)
    task_id   = int(q.data.split(":")[1])
    new_state = db.toggle_task(task_id)
    task      = db.get_task(task_id)
    if not task:
        await q.edit_message_text("Not found.")
        return
    msg = t(lang, "task_resumed", name=task["name"]) if new_state else t(lang, "task_paused", name=task["name"])
    count = db.count_task_results(task_id)
    await q.edit_message_text(
        f"{msg}\n\n" + _task_info_text(lang, task, count),
        parse_mode=ParseMode.HTML,
        reply_markup=_task_action_kb(lang, task_id, bool(task["is_active"])),
    )


async def on_run_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer(t(_lang(context, q.from_user.id), "run_triggered")[:200])
    lang    = _lang(context, q.from_user.id)
    task_id = int(q.data.split(":")[1])
    # Run in background so the callback returns immediately
    asyncio.create_task(run_task_now(task_id, _send_to_channel))
    task  = db.get_task(task_id)
    count = db.count_task_results(task_id) if task else 0
    if task:
        await q.edit_message_text(
            f"▶️ {t(lang, 'run_triggered')}\n\n" + _task_info_text(lang, task, count),
            parse_mode=ParseMode.HTML,
            reply_markup=_task_action_kb(lang, task_id, bool(task["is_active"])),
        )


async def on_delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показує підтвердження перед видаленням."""
    q = update.callback_query
    await q.answer()
    lang    = _lang(context, q.from_user.id)
    task_id = int(q.data.split(":")[1])
    task    = db.get_task(task_id)
    if not task:
        await q.edit_message_text("Not found.")
        return
    await q.edit_message_text(
        t(lang, "delete_confirm", name=task["name"]),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t(lang, "btn_confirm_delete"), callback_data=f"delyes:{task_id}"),
                InlineKeyboardButton(t(lang, "btn_cancel_action"),  callback_data=f"info:{task_id}"),
            ]
        ]),
    )


async def on_delete_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    lang    = _lang(context, q.from_user.id)
    task_id = int(q.data.split(":")[1])
    task    = db.get_task(task_id)
    name    = task["name"] if task else str(task_id)
    db.delete_task(task_id)
    await q.edit_message_text(
        t(lang, "task_deleted", name=name),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(t(lang, "btn_back"), callback_data="back:tasks"),
        ]]),
    )


async def on_back_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    lang = _lang(context, q.from_user.id)
    row  = db.get_user(q.from_user.id)
    tasks = db.get_user_tasks(row["id"]) if row else []
    if not tasks:
        await q.edit_message_text(t(lang, "no_tasks"), parse_mode=ParseMode.HTML)
        return
    await q.edit_message_text(
        t(lang, "tasks_header", count=len(tasks)),
        parse_mode=ParseMode.HTML,
        reply_markup=_tasks_kb(tasks),
    )


# ── Edit task conversation ──────────────────────────────────────────────────

async def on_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang    = _lang(context, q.from_user.id)
    task_id = int(q.data.split(":")[1])
    task    = db.get_task(task_id)
    if not task:
        await q.edit_message_text("Not found.")
        return ConversationHandler.END

    context.user_data["edit_task_id"] = task_id
    context.user_data["lang"]         = lang

    await q.edit_message_text(
        t(lang, "edit_what", name=task["name"]),
        parse_mode=ParseMode.HTML,
        reply_markup=_edit_kb(lang, task_id, bool(task["ai_filter"])),
    )
    return S_EDIT_PICK


async def on_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang    = context.user_data.get("lang", "ua")
    task_id = context.user_data.get("edit_task_id")
    field   = q.data.split(":")[1]

    if field == "ai":
        task = db.get_task(task_id)
        if task:
            new_ai = not bool(task["ai_filter"])
            db.update_task_fields(task_id, ai_filter=int(new_ai))
            task = db.get_task(task_id)  # refresh
        count = db.count_task_results(task_id) if task else 0
        await q.edit_message_text(
            t(lang, "edit_saved") + "\n\n" + _task_info_text(lang, task, count),
            parse_mode=ParseMode.HTML,
            reply_markup=_task_action_kb(lang, task_id, bool(task["is_active"])),
        )
        return ConversationHandler.END

    if field == "name":
        await q.edit_message_text(t(lang, "edit_name_prompt"), parse_mode=ParseMode.HTML)
        return S_EDIT_NAME

    if field == "keywords":
        await q.edit_message_text(t(lang, "edit_kw_prompt"), parse_mode=ParseMode.HTML)
        return S_EDIT_KEYWORDS

    if field == "interval":
        await q.edit_message_text(
            t(lang, "edit_interval_prompt"),
            reply_markup=_interval_kb(lang, prefix="ei"),
        )
        return S_EDIT_INTERVAL

    if field == "channel":
        await q.edit_message_text(t(lang, "edit_channel_prompt"), parse_mode=ParseMode.HTML)
        return S_EDIT_CHANNEL

    return S_EDIT_PICK


async def _edit_done(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     text_or_query: bool = False) -> int:
    """Зберігає і показує оновлений task_info. Використовується після кожного редагування."""
    lang    = context.user_data.get("lang", "ua")
    task_id = context.user_data.get("edit_task_id")
    task    = db.get_task(task_id)
    count   = db.count_task_results(task_id) if task else 0
    info    = t(lang, "edit_saved") + "\n\n" + (_task_info_text(lang, task, count) if task else "")
    kb      = _task_action_kb(lang, task_id, bool(task["is_active"])) if task else None

    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(info, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await update.message.reply_text(info, parse_mode=ParseMode.HTML, reply_markup=kb)
    return ConversationHandler.END


async def on_edit_name_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    task_id = context.user_data.get("edit_task_id")
    name    = update.message.text.strip()[:50]
    db.update_task_fields(task_id, name=name)
    return await _edit_done(update, context)


async def on_edit_kw_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    task_id = context.user_data.get("edit_task_id")
    raw     = update.message.text.strip()
    kw      = "" if raw == "-" else raw
    db.update_task_fields(task_id, keywords=kw)
    return await _edit_done(update, context)


async def on_edit_interval_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    task_id  = context.user_data.get("edit_task_id")
    interval = int(q.data.split(":")[1])
    db.update_task_fields(task_id, interval_min=interval)
    return await _edit_done(update, context)


async def on_edit_channel_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    task_id = context.user_data.get("edit_task_id")
    lang    = context.user_data.get("lang", "ua")
    channel = update.message.text.strip()
    if not channel.startswith("@") and not channel.lstrip("-").isdigit():
        await update.message.reply_text(t(lang, "channel_invalid"), parse_mode=ParseMode.HTML)
        return S_EDIT_CHANNEL
    db.update_task_fields(task_id, channel_id=channel)
    return await _edit_done(update, context)


async def edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang    = context.user_data.get("lang", "ua")
    task_id = context.user_data.get("edit_task_id")
    task    = db.get_task(task_id) if task_id else None
    count   = db.count_task_results(task_id) if task else 0
    if task:
        await update.message.reply_text(
            _task_info_text(lang, task, count),
            parse_mode=ParseMode.HTML,
            reply_markup=_task_action_kb(lang, task_id, bool(task["is_active"])),
        )
    return ConversationHandler.END


# ── Conversation: Create Task ───────────────────────────────────────────────

async def conv_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    user = update.effective_user
    lang = db.get_user_lang(user.id)
    context.user_data["lang"] = lang

    await update.message.reply_text(
        t(lang, "step_country"),
        parse_mode=ParseMode.HTML,
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
        parse_mode=ParseMode.HTML,
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
            parse_mode=ParseMode.HTML,
            reply_markup=_source_kb(lang, country),
        )
        return S_SOURCE

    tpl = get_template(country, niche)
    if tpl:
        context.user_data["source_type"]          = tpl.source_type
        context.user_data["source_url"]            = tpl.source_url
        context.user_data["keywords"]              = tpl.keywords
        context.user_data["task_name_suggestion"]  = (
            tpl.name_ua if lang == "ua" else tpl.name_en
        )
        await q.edit_message_text(
            t(lang, "tpl_applied",
              name=(tpl.name_ua if lang == "ua" else tpl.name_en),
              source_type=tpl.source_type.upper(),
              url=tpl.source_url[:60],
              keywords=tpl.keywords or "—"),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t(lang, "btn_accept_tpl"), callback_data="tpl:accept"),
                InlineKeyboardButton(t(lang, "btn_edit_url"),   callback_data="tpl:edit"),
            ]]),
        )
        return S_URL
    else:
        await q.edit_message_text(
            t(lang, "step_source"),
            parse_mode=ParseMode.HTML,
            reply_markup=_source_kb(lang, country),
        )
        return S_SOURCE


async def conv_tpl_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang   = context.user_data.get("lang", "ua")
    choice = q.data.split(":")[1]

    if choice == "accept":
        await q.edit_message_text(
            t(lang, "step_interval"),
            parse_mode=ParseMode.HTML,
            reply_markup=_interval_kb(lang),
        )
        return S_INTERVAL

    # Edit — show current URL as hint
    src  = context.user_data.get("source_type", "rss")
    hint = context.user_data.get("source_url") or _URL_HINTS.get(src, "")
    await q.edit_message_text(
        t(lang, "step_url",
          source=t(lang, f"src_{src}"),
          hint=hint[:60]),
        parse_mode=ParseMode.HTML,
    )
    return S_URL


async def conv_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ua")
    src  = q.data.split(":")[1]
    context.user_data["source_type"] = src
    hint = _URL_HINTS.get(src, "")
    await q.edit_message_text(
        t(lang, "step_url", source=t(lang, f"src_{src}"), hint=hint),
        parse_mode=ParseMode.HTML,
    )
    return S_URL


async def conv_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "ua")
    context.user_data["source_url"] = update.message.text.strip()
    await update.message.reply_text(
        t(lang, "step_keywords"),
        parse_mode=ParseMode.HTML,
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
        parse_mode=ParseMode.HTML,
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
        await update.message.reply_text(t(lang, "channel_invalid"), parse_mode=ParseMode.HTML)
        return S_CHANNEL
    context.user_data["channel_id"] = channel
    await update.message.reply_text(
        t(lang, "step_ai"),
        parse_mode=ParseMode.HTML,
        reply_markup=_ai_kb(lang),
    )
    return S_AI


async def conv_ai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ua")
    context.user_data["ai_filter"] = (q.data == "ai:yes")
    suggestion = context.user_data.get("task_name_suggestion", "")
    hint = f"\n\n<i>{suggestion}</i>" if suggestion else ""
    await q.edit_message_text(
        t(lang, "step_name", hint=hint),
        parse_mode=ParseMode.HTML,
    )
    return S_NAME


async def conv_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "ua")
    name = update.message.text.strip()[:50]
    d    = context.user_data

    user    = update.effective_user
    user_id = db.upsert_user(user.id, user.first_name, user.username)

    ai_enabled = d.get("ai_filter", False)
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
        ai_filter    = ai_enabled,
    )

    ai_txt = t(lang, "ai_on") if ai_enabled else t(lang, "ai_off")
    msg = t(lang, "task_created",
            name=name,
            source_type=d.get("source_type", "").upper(),
            country=d.get("country", "ua").upper(),
            interval=d.get("interval_min", 60),
            channel=d.get("channel_id", ""),
            ai=ai_txt)

    # Warn if AI enabled but no key
    if ai_enabled and not ANTHROPIC_API_KEY:
        msg += t(lang, "ai_no_key_warn")

    await update.message.reply_text(
        msg,
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


# ── Text router ─────────────────────────────────────────────────────────────

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    lang = _lang(context, user.id)
    text = update.message.text

    all_my_tasks = {t(l, "btn_my_tasks") for l in ("ua", "en")}
    all_settings = {t(l, "btn_settings") for l in ("ua", "en")}
    all_help     = {t(l, "btn_help")     for l in ("ua", "en")}

    if text in all_my_tasks:
        await cmd_tasks(update, context)
    elif text in all_settings:
        await cmd_settings(update, context)
    elif text in all_help:
        await cmd_help(update, context)
    else:
        row    = db.get_user(user.id)
        lang   = row["lang"] if row else "ua"
        tasks  = db.get_user_tasks(row["id"]) if row else []
        active = sum(1 for t_ in tasks if t_["is_active"])
        await update.message.reply_text(
            t(lang, "main_menu", count=active),
            parse_mode=ParseMode.HTML,
            reply_markup=_main_menu_kb(lang),
        )


# ── Setup ───────────────────────────────────────────────────────────────────

async def post_init(app: Application) -> None:
    global _app
    _app = app

    await app.bot.set_my_commands([
        BotCommand("start",    "Головне меню / Main menu"),
        BotCommand("tasks",    "Мої задачі / My tasks"),
        BotCommand("newtask",  "Нова задача / New task"),
        BotCommand("settings", "Мова / Language"),
        BotCommand("help",     "Довідка / Help"),
        BotCommand("cancel",   "Скасувати / Cancel"),
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

    # Settings language change
    app.add_handler(CallbackQueryHandler(on_settings_lang, pattern=r"^setlang:"))

    # Task action buttons (global — outside conversations)
    app.add_handler(CallbackQueryHandler(on_task_info,   pattern=r"^info:\d+$"))
    app.add_handler(CallbackQueryHandler(on_toggle_task, pattern=r"^toggle:\d+$"))
    app.add_handler(CallbackQueryHandler(on_run_now,     pattern=r"^run:\d+$"))
    app.add_handler(CallbackQueryHandler(on_delete_task, pattern=r"^delete:\d+$"))
    app.add_handler(CallbackQueryHandler(on_delete_yes,  pattern=r"^delyes:\d+$"))
    app.add_handler(CallbackQueryHandler(on_back_tasks,  pattern=r"^back:tasks$"))

    # Edit task conversation
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_edit_start, pattern=r"^edit:\d+$")],
        states={
            S_EDIT_PICK:     [CallbackQueryHandler(on_edit_field,        pattern=r"^ef:")],
            S_EDIT_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, on_edit_name_done)],
            S_EDIT_KEYWORDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_edit_kw_done)],
            S_EDIT_INTERVAL: [CallbackQueryHandler(on_edit_interval_done, pattern=r"^ei:\d+$")],
            S_EDIT_CHANNEL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, on_edit_channel_done)],
        },
        fallbacks=[CommandHandler("cancel", edit_cancel)],
        allow_reentry=True,
    )

    # Create task conversation
    create_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(f"^({t('ua','btn_new_task')}|{t('en','btn_new_task')})$"), conv_start),
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
            S_INTERVAL: [CallbackQueryHandler(conv_interval,   pattern=r"^int:\d+$")],
            S_CHANNEL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_channel)],
            S_AI:       [CallbackQueryHandler(conv_ai,         pattern=r"^ai:")],
            S_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, conv_name)],
        },
        fallbacks=[CommandHandler("cancel", conv_cancel)],
        allow_reentry=True,
    )

    # /start with first-visit language selection
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
    app.add_handler(edit_conv)
    app.add_handler(create_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.info("Parser Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
