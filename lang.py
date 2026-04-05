"""
UA / EN translations for Parser Bot.
"""
from typing import Any

_T: dict[str, dict[str, str]] = {
    "welcome": {
        "ua": "👋 Привіт, {name}!\n\nЯ <b>Parser Bot</b> — автоматично слідкую за новинами, оголошеннями, вакансіями та іншим і надсилаю свіжі результати у ваш Telegram канал.\n\nОберіть мову / Choose language:",
        "en": "👋 Hi, {name}!\n\nI'm <b>Parser Bot</b> — I track news, listings, jobs and more, and send fresh results to your Telegram channel.\n\nОберіть мову / Choose language:",
    },
    "main_menu": {
        "ua": "📋 <b>Головне меню</b>\n\nАктивних задач: <b>{count}</b>",
        "en": "📋 <b>Main menu</b>\n\nActive tasks: <b>{count}</b>",
    },
    "btn_new_task": {"ua": "➕ Нова задача",    "en": "➕ New task"},
    "btn_my_tasks": {"ua": "📂 Мої задачі",     "en": "📂 My tasks"},
    "btn_settings": {"ua": "⚙️ Налаштування",   "en": "⚙️ Settings"},
    "btn_help":     {"ua": "❓ Довідка",         "en": "❓ Help"},
    "btn_skip":     {"ua": "⏭ Пропустити",      "en": "⏭ Skip"},
    "btn_cancel":   {"ua": "❌ Скасувати",       "en": "❌ Cancel"},
    "btn_back":     {"ua": "◀️ До списку",       "en": "◀️ Back to list"},
    "btn_pause":    {"ua": "⏸ Пауза",           "en": "⏸ Pause"},
    "btn_resume":   {"ua": "▶️ Запустити",       "en": "▶️ Resume"},
    "btn_run_now":  {"ua": "▶️ Запуск зараз",    "en": "▶️ Run now"},
    "btn_edit":     {"ua": "✏️ Редагувати",      "en": "✏️ Edit"},
    "btn_delete":   {"ua": "🗑 Видалити",        "en": "🗑 Delete"},

    # -- Task creation flow -------------------------------------------------
    "step_country": {
        "ua": "🌍 <b>Крок 1/9</b> — Оберіть країну/регіон:",
        "en": "🌍 <b>Step 1/9</b> — Choose country/region:",
    },
    "step_niche": {
        "ua": "📌 <b>Крок 2/9</b> — Оберіть нішу або Custom:",
        "en": "📌 <b>Step 2/9</b> — Choose a niche or Custom:",
    },
    "step_source": {
        "ua": "📡 <b>Крок 3/9</b> — Оберіть тип джерела:",
        "en": "📡 <b>Step 3/9</b> — Choose source type:",
    },
    "step_url": {
        "ua": "🔗 <b>Крок 4/9</b> — URL або пошуковий запит для <b>{source}</b>:\n\n<i>Приклад: <code>{hint}</code></i>",
        "en": "🔗 <b>Step 4/9</b> — URL or search query for <b>{source}</b>:\n\n<i>Example: <code>{hint}</code></i>",
    },
    "step_keywords": {
        "ua": "🔍 <b>Крок 5/9</b> — Ключові слова для фільтрації (через кому):\n\n<i>Наприклад: bitcoin, крипто, BTC</i>\nАбо натисніть «Пропустити» щоб отримувати всі результати.",
        "en": "🔍 <b>Step 5/9</b> — Filter keywords (comma-separated):\n\n<i>Example: bitcoin, crypto, BTC</i>\nOr tap «Skip» to receive all results.",
    },
    "step_interval": {
        "ua": "⏱ <b>Крок 6/9</b> — Як часто перевіряти?",
        "en": "⏱ <b>Step 6/9</b> — How often to check?",
    },
    "step_channel": {
        "ua": "📢 <b>Крок 7/9</b> — ID каналу або групи для відправки результатів:\n\n<i>Приклад: @mychannel або -1001234567890</i>\n\n⚠️ Бот повинен бути адміністратором каналу!",
        "en": "📢 <b>Step 7/9</b> — Channel or group ID to send results to:\n\n<i>Example: @mychannel or -1001234567890</i>\n\n⚠️ Bot must be an admin of the channel!",
    },
    "step_ai": {
        "ua": "🤖 <b>Крок 8/9</b> — AI-фільтрація через Claude Haiku?\n\nВідсіює нерелевантні матеріали автоматично.\n<i>Потребує ANTHROPIC_API_KEY у налаштуваннях.</i>",
        "en": "🤖 <b>Step 8/9</b> — AI filtering via Claude Haiku?\n\nAutomatically filters irrelevant content.\n<i>Requires ANTHROPIC_API_KEY in settings.</i>",
    },
    "step_name": {
        "ua": "✏️ <b>Крок 9/9</b> — Назва задачі:{hint}",
        "en": "✏️ <b>Step 9/9</b> — Task name:{hint}",
    },
    "btn_ai_yes": {"ua": "✅ Увімкнути AI-фільтр", "en": "✅ Enable AI filter"},
    "btn_ai_no":  {"ua": "❌ Без AI-фільтру",       "en": "❌ No AI filter"},
    "tpl_applied": {
        "ua": "✅ Шаблон <b>{name}</b> застосовано!\n\n📡 Джерело: {source_type}\n🔗 Запит: <code>{url}</code>\n🔑 Ключові слова: {keywords}\n\nПрийняти або відредагувати URL?",
        "en": "✅ Template <b>{name}</b> applied!\n\n📡 Source: {source_type}\n🔗 Query: <code>{url}</code>\n🔑 Keywords: {keywords}\n\nAccept or edit the URL?",
    },
    "btn_accept_tpl": {"ua": "✅ Прийняти",    "en": "✅ Accept"},
    "btn_edit_url":   {"ua": "✏️ Змінити URL", "en": "✏️ Edit URL"},
    "channel_invalid": {
        "ua": "❌ Невірний формат!\n\nВведіть @username або числовий ID\n<i>Приклад: @mychannel або -1001234567890</i>",
        "en": "❌ Invalid format!\n\nEnter @username or numeric ID\n<i>Example: @mychannel or -1001234567890</i>",
    },

    # -- Task created -------------------------------------------------------
    "task_created": {
        "ua": "✅ Задача <b>{name}</b> створена!\n\n📡 Джерело: {source_type}\n🌍 Країна: {country}\n⏱ Інтервал: кожні {interval} хв\n📢 Канал: {channel}\n🤖 AI-фільтр: {ai}\n\n▶️ Перший запуск через ~1 хвилину.",
        "en": "✅ Task <b>{name}</b> created!\n\n📡 Source: {source_type}\n🌍 Country: {country}\n⏱ Interval: every {interval} min\n📢 Channel: {channel}\n🤖 AI filter: {ai}\n\n▶️ First run in ~1 minute.",
    },
    "task_cancelled": {
        "ua": "❌ Створення задачі скасовано.",
        "en": "❌ Task creation cancelled.",
    },
    "ai_no_key_warn": {
        "ua": "\n\n⚠️ <b>Увага:</b> ANTHROPIC_API_KEY не встановлено — AI-фільтрацію вимкнено.",
        "en": "\n\n⚠️ <b>Note:</b> ANTHROPIC_API_KEY not set — AI filtering is disabled.",
    },

    # -- Task list ----------------------------------------------------------
    "no_tasks": {
        "ua": "📂 Задач поки немає.\n\nНатисніть <b>➕ Нова задача</b> щоб розпочати.",
        "en": "📂 No tasks yet.\n\nTap <b>➕ New task</b> to get started.",
    },
    "tasks_header": {
        "ua": "📂 <b>Мої задачі ({count})</b>\n\n✅ активна  ⏸ пауза",
        "en": "📂 <b>My tasks ({count})</b>\n\n✅ active  ⏸ paused",
    },

    # -- Task info ----------------------------------------------------------
    "task_info": {
        "ua": (
            "📌 <b>{name}</b>\n\n"
            "📡 Джерело: <b>{source_type}</b> | 🌍 {country}\n"
            "🔗 URL/запит: <code>{url}</code>\n"
            "🔑 Ключові слова: {keywords}\n"
            "⏱ Інтервал: {interval} хв\n"
            "📢 Канал: {channel}\n"
            "🤖 AI-фільтр: {ai}\n"
            "📊 Статус: {status}\n"
            "📈 Результатів: {results}\n"
            "🕐 Остання перевірка: {last_run}\n"
            "🔜 Наступна: {next_run}"
        ),
        "en": (
            "📌 <b>{name}</b>\n\n"
            "📡 Source: <b>{source_type}</b> | 🌍 {country}\n"
            "🔗 URL/query: <code>{url}</code>\n"
            "🔑 Keywords: {keywords}\n"
            "⏱ Interval: {interval} min\n"
            "📢 Channel: {channel}\n"
            "🤖 AI filter: {ai}\n"
            "📊 Status: {status}\n"
            "📈 Results: {results}\n"
            "🕐 Last check: {last_run}\n"
            "🔜 Next: {next_run}"
        ),
    },
    "status_active": {"ua": "✅ Активна",   "en": "✅ Active"},
    "status_paused": {"ua": "⏸ Пауза",     "en": "⏸ Paused"},
    "ai_on":         {"ua": "✅ увімк.",    "en": "✅ on"},
    "ai_off":        {"ua": "❌ вимк.",     "en": "❌ off"},
    "never":         {"ua": "ще не було",  "en": "never"},
    "no_url":        {"ua": "—",           "en": "—"},
    "no_keywords":   {"ua": "всі результати", "en": "all results"},

    # -- Task actions -------------------------------------------------------
    "task_paused":   {"ua": "⏸ Задача «{name}» призупинена.",   "en": "⏸ Task «{name}» paused."},
    "task_resumed":  {"ua": "▶️ Задача «{name}» відновлена.",   "en": "▶️ Task «{name}» resumed."},
    "task_deleted":  {"ua": "🗑 Задача «{name}» видалена.",      "en": "🗑 Task «{name}» deleted."},
    "run_triggered": {
        "ua": "▶️ Задача запущена! Результати з'являться у каналі протягом хвилини.",
        "en": "▶️ Task triggered! Results will appear in the channel within a minute.",
    },
    "delete_confirm": {
        "ua": "🗑 <b>Видалити задачу «{name}»?</b>\n\nЦю дію не можна скасувати.",
        "en": "🗑 <b>Delete task «{name}»?</b>\n\nThis cannot be undone.",
    },
    "btn_confirm_delete": {"ua": "✅ Так, видалити", "en": "✅ Yes, delete"},
    "btn_cancel_action":  {"ua": "❌ Скасувати",     "en": "❌ Cancel"},

    # -- Edit task ----------------------------------------------------------
    "edit_what": {
        "ua": "✏️ <b>Редагування: {name}</b>\n\nЩо змінити?",
        "en": "✏️ <b>Edit: {name}</b>\n\nWhat to change?",
    },
    "edit_name_btn":     {"ua": "✏️ Назва",         "en": "✏️ Name"},
    "edit_kw_btn":       {"ua": "🔑 Ключові слова", "en": "🔑 Keywords"},
    "edit_interval_btn": {"ua": "⏱ Інтервал",       "en": "⏱ Interval"},
    "edit_channel_btn":  {"ua": "📢 Канал",          "en": "📢 Channel"},
    "edit_ai_btn":       {"ua": "🤖 AI: {state}",    "en": "🤖 AI: {state}"},
    "edit_name_prompt": {
        "ua": "✏️ Введіть нову назву задачі:",
        "en": "✏️ Enter new task name:",
    },
    "edit_kw_prompt": {
        "ua": "🔑 Введіть нові ключові слова (через кому)\nАбо «-» щоб прибрати фільтр:",
        "en": "🔑 Enter new keywords (comma-separated)\nOr «-» to remove filter:",
    },
    "edit_channel_prompt": {
        "ua": "📢 Введіть новий @username або ID каналу:",
        "en": "📢 Enter new channel @username or ID:",
    },
    "edit_interval_prompt": {
        "ua": "⏱ Оберіть новий інтервал:",
        "en": "⏱ Choose new interval:",
    },
    "edit_saved": {"ua": "✅ Збережено!", "en": "✅ Saved!"},

    # -- Settings -----------------------------------------------------------
    "settings_header": {
        "ua": "⚙️ <b>Налаштування</b>\n\nПоточна мова: <b>{lang_name}</b>\n\nОберіть нову:",
        "en": "⚙️ <b>Settings</b>\n\nCurrent language: <b>{lang_name}</b>\n\nChoose new:",
    },
    "lang_changed": {
        "ua": "✅ Мову змінено на <b>Українську</b>.",
        "en": "✅ Language changed to <b>English</b>.",
    },

    # -- Help ---------------------------------------------------------------
    "help_text": {
        "ua": (
            "❓ <b>Довідка Parser Bot</b>\n\n"
            "<b>Команди:</b>\n"
            "/start — головне меню\n"
            "/newtask — нова задача\n"
            "/tasks — мої задачі\n"
            "/settings — мова\n"
            "/cancel — скасувати\n\n"
            "<b>Джерела:</b>\n"
            "• RSS/Atom фіди\n"
            "• Google News (5 регіонів)\n"
            "• OLX оголошення\n"
            "• Rozetka товари\n"
            "• DOU вакансії\n"
            "• Telegram-канали (публічні)\n"
            "• Будь-який сайт\n\n"
            "<b>Ніші:</b> Нерухомість, Вакансії, Крипто, Tech, Авто, Фінанси, Новини, E-commerce, AI, Міграція\n\n"
            "<b>Країни:</b> 🇺🇦 UA | 🇺🇸 US | 🇪🇺 EU | 🇨🇦 CA | 🌍 World"
        ),
        "en": (
            "❓ <b>Parser Bot Help</b>\n\n"
            "<b>Commands:</b>\n"
            "/start — main menu\n"
            "/newtask — new task\n"
            "/tasks — my tasks\n"
            "/settings — language\n"
            "/cancel — cancel\n\n"
            "<b>Sources:</b>\n"
            "• RSS/Atom feeds\n"
            "• Google News (5 regions)\n"
            "• OLX listings\n"
            "• Rozetka products\n"
            "• DOU jobs\n"
            "• Telegram channels (public)\n"
            "• Any website\n\n"
            "<b>Niches:</b> Real Estate, Jobs, Crypto, Tech, Cars, Finance, News, E-commerce, AI, Immigration\n\n"
            "<b>Countries:</b> 🇺🇦 UA | 🇺🇸 US | 🇪🇺 EU | 🇨🇦 CA | 🌍 World"
        ),
    },

    # -- Countries ----------------------------------------------------------
    "country_ua":    {"ua": "🇺🇦 Україна",   "en": "🇺🇦 Ukraine"},
    "country_us":    {"ua": "🇺🇸 США",        "en": "🇺🇸 USA"},
    "country_eu":    {"ua": "🇪🇺 Європа",     "en": "🇪🇺 Europe"},
    "country_ca":    {"ua": "🇨🇦 Канада",     "en": "🇨🇦 Canada"},
    "country_world": {"ua": "🌍 Весь світ",   "en": "🌍 World"},

    # -- Niches -------------------------------------------------------------
    "niche_realestate":  {"ua": "🏠 Нерухомість", "en": "🏠 Real Estate"},
    "niche_jobs":        {"ua": "💼 Вакансії",    "en": "💼 Jobs"},
    "niche_crypto":      {"ua": "₿ Крипто",       "en": "₿ Crypto"},
    "niche_tech":        {"ua": "💻 Tech",         "en": "💻 Tech"},
    "niche_cars":        {"ua": "🚗 Авто",         "en": "🚗 Cars"},
    "niche_finance":     {"ua": "💰 Фінанси",      "en": "💰 Finance"},
    "niche_news":        {"ua": "📰 Новини",       "en": "📰 News"},
    "niche_ecommerce":   {"ua": "🛒 E-commerce",   "en": "🛒 E-commerce"},
    "niche_ai":          {"ua": "🤖 AI/Tech",      "en": "🤖 AI/Tech"},
    "niche_immigration": {"ua": "✈️ Міграція",     "en": "✈️ Immigration"},
    "niche_custom":      {"ua": "⚙️ Custom",       "en": "⚙️ Custom"},

    # -- Sources ------------------------------------------------------------
    "src_rss":      {"ua": "📡 RSS/Atom фід",      "en": "📡 RSS/Atom feed"},
    "src_google":   {"ua": "🔍 Google News",        "en": "🔍 Google News"},
    "src_olx":      {"ua": "🛍 OLX",               "en": "🛍 OLX"},
    "src_rozetka":  {"ua": "🟣 Rozetka",            "en": "🟣 Rozetka"},
    "src_dou":      {"ua": "👨‍💻 DOU Jobs",        "en": "👨‍💻 DOU Jobs"},
    "src_telegram": {"ua": "✈️ Telegram канал",     "en": "✈️ Telegram channel"},
    "src_web":      {"ua": "🌐 Сайт",               "en": "🌐 Website"},

    # -- Intervals ----------------------------------------------------------
    "interval_15":   {"ua": "15 хв",    "en": "15 min"},
    "interval_30":   {"ua": "30 хв",    "en": "30 min"},
    "interval_45":   {"ua": "45 хв",    "en": "45 min"},
    "interval_60":   {"ua": "1 год",    "en": "1 hour"},
    "interval_120":  {"ua": "2 год",    "en": "2 hours"},
    "interval_240":  {"ua": "4 год",    "en": "4 hours"},
    "interval_720":  {"ua": "12 год",   "en": "12 hours"},
    "interval_1440": {"ua": "1 день",   "en": "1 day"},
}


def t(lang: str, key: str, **kwargs: Any) -> str:
    """Return translated string for the given lang (ua/en)."""
    entry = _T.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get("ua") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text
