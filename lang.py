"""
UA / EN translations for Parser Bot.
"""
from typing import Any

_T: dict[str, dict[str, str]] = {
    "welcome": {
        "ua": "👋 Привіт, {name}!\n\nЯ Parser Bot — автоматично слідкую за новинами, оголошеннями, вакансіями та іншим і надсилаю свіжі результати у ваш Telegram канал.\n\nОберіть мову / Choose language:",
        "en": "👋 Hi, {name}!\n\nI'm Parser Bot — I track news, listings, jobs and more, and send fresh results to your Telegram channel.\n\nОберіть мову / Choose language:",
    },
    "choose_lang": {
        "ua": "🌐 Оберіть мову інтерфейсу:",
        "en": "🌐 Choose interface language:",
    },
    "main_menu": {
        "ua": "📋 Головне меню\n\nВаші активні задачі: {count}",
        "en": "📋 Main menu\n\nYour active tasks: {count}",
    },
    "btn_new_task": {
        "ua": "➕ Нова задача",
        "en": "➕ New task",
    },
    "btn_my_tasks": {
        "ua": "📂 Мої задачі",
        "en": "📂 My tasks",
    },
    "btn_settings": {
        "ua": "⚙️ Налаштування",
        "en": "⚙️ Settings",
    },
    "btn_help": {
        "ua": "❓ Допомога",
        "en": "❓ Help",
    },
    "step_country": {
        "ua": "🌍 Крок 1/9 — Оберіть країну/регіон:",
        "en": "🌍 Step 1/9 — Choose country/region:",
    },
    "step_niche": {
        "ua": "📌 Крок 2/9 — Оберіть нішу або Custom для власних налаштувань:",
        "en": "📌 Step 2/9 — Choose a niche or Custom for your own settings:",
    },
    "step_source": {
        "ua": "📡 Крок 3/9 — Оберіть тип джерела:",
        "en": "📡 Step 3/9 — Choose source type:",
    },
    "step_url": {
        "ua": "🔗 Крок 4/9 — Вкажіть URL або пошуковий запит:\n\nДля RSS/Atom — пряме посилання на фід.\nДля Google News, OLX, Rozetka — ключові слова для пошуку.",
        "en": "🔗 Step 4/9 — Enter URL or search query:\n\nFor RSS/Atom — direct feed link.\nFor Google News, OLX, Rozetka — search keywords.",
    },
    "step_keywords": {
        "ua": "🔍 Крок 5/9 — Додаткові ключові слова для фільтрації (через кому) або пропустіть:",
        "en": "🔍 Step 5/9 — Additional filter keywords (comma-separated) or skip:",
    },
    "step_interval": {
        "ua": "⏱ Крок 6/9 — Як часто перевіряти?",
        "en": "⏱ Step 6/9 — How often to check?",
    },
    "step_channel": {
        "ua": "📢 Крок 7/9 — Вкажіть ID каналу або групи куди надсилати результати:\n\nПриклад: @mychannel або -1001234567890\n\n⚠️ Бот повинен бути адміністратором каналу!",
        "en": "📢 Step 7/9 — Enter channel or group ID to send results to:\n\nExample: @mychannel or -1001234567890\n\n⚠️ Bot must be an admin of the channel!",
    },
    "step_ai": {
        "ua": "🤖 Крок 8/9 — AI-фільтрація (Claude Haiku)?\n\nФільтрує нерелевантні матеріали. Потребує ANTHROPIC_API_KEY.",
        "en": "🤖 Step 8/9 — AI filtering (Claude Haiku)?\n\nFilters irrelevant content. Requires ANTHROPIC_API_KEY.",
    },
    "step_name": {
        "ua": "✏️ Крок 9/9 — Назва задачі (для зручності):",
        "en": "✏️ Step 9/9 — Task name (for your reference):",
    },
    "btn_skip": {
        "ua": "⏭ Пропустити",
        "en": "⏭ Skip",
    },
    "btn_ai_yes": {
        "ua": "✅ Увімкнути AI-фільтр",
        "en": "✅ Enable AI filter",
    },
    "btn_ai_no": {
        "ua": "❌ Без AI-фільтру",
        "en": "❌ No AI filter",
    },
    "btn_cancel": {
        "ua": "❌ Скасувати",
        "en": "❌ Cancel",
    },
    "task_created": {
        "ua": "✅ Задача <b>{name}</b> створена!\n\nДжерело: {source_type}\nКраїна: {country}\nІнтервал: кожні {interval} хв\nКанал: {channel}\nAI-фільтр: {ai}",
        "en": "✅ Task <b>{name}</b> created!\n\nSource: {source_type}\nCountry: {country}\nInterval: every {interval} min\nChannel: {channel}\nAI filter: {ai}",
    },
    "task_cancelled": {
        "ua": "❌ Створення задачі скасовано.",
        "en": "❌ Task creation cancelled.",
    },
    "no_tasks": {
        "ua": "У вас поки немає задач. Натисніть «Нова задача» щоб почати.",
        "en": "You have no tasks yet. Tap «New task» to start.",
    },
    "task_info": {
        "ua": "📌 <b>{name}</b>\n\n🔹 Джерело: {source_type} | {country}\n🔹 Інтервал: {interval} хв\n🔹 Канал: {channel}\n🔹 AI-фільтр: {ai}\n🔹 Статус: {status}\n🔹 Результатів: {results}\n🔹 Остання перевірка: {last_run}",
        "en": "📌 <b>{name}</b>\n\n🔹 Source: {source_type} | {country}\n🔹 Interval: {interval} min\n🔹 Channel: {channel}\n🔹 AI filter: {ai}\n🔹 Status: {status}\n🔹 Results: {results}\n🔹 Last check: {last_run}",
    },
    "btn_toggle": {
        "ua": "⏸ Пауза / ▶️ Запустити",
        "en": "⏸ Pause / ▶️ Resume",
    },
    "btn_delete": {
        "ua": "🗑 Видалити",
        "en": "🗑 Delete",
    },
    "btn_back": {
        "ua": "◀️ Назад",
        "en": "◀️ Back",
    },
    "task_paused": {
        "ua": "⏸ Задача «{name}» призупинена.",
        "en": "⏸ Task «{name}» paused.",
    },
    "task_resumed": {
        "ua": "▶️ Задача «{name}» відновлена.",
        "en": "▶️ Task «{name}» resumed.",
    },
    "task_deleted": {
        "ua": "🗑 Задача видалена.",
        "en": "🗑 Task deleted.",
    },
    "status_active": {
        "ua": "✅ Активна",
        "en": "✅ Active",
    },
    "status_paused": {
        "ua": "⏸ Пауза",
        "en": "⏸ Paused",
    },
    "ai_on":  {"ua": "✅ увімк.", "en": "✅ on"},
    "ai_off": {"ua": "❌ вимк.", "en": "❌ off"},
    "never":  {"ua": "ніколи", "en": "never"},
    "settings_menu": {
        "ua": "⚙️ Налаштування\n\nПоточна мова: Українська",
        "en": "⚙️ Settings\n\nCurrent language: English",
    },
    "lang_changed": {
        "ua": "✅ Мову змінено на Українську.",
        "en": "✅ Language changed to English.",
    },
    "help_text": {
        "ua": "❓ <b>Довідка Parser Bot</b>\n\n/start — головне меню\n/newtask — нова задача\n/tasks — мої задачі\n/settings — налаштування\n\n<b>Підтримувані джерела:</b>\n• RSS/Atom фіди\n• Google News (5 регіонів)\n• OLX оголошення\n• Rozetka товари\n• DOU вакансії\n• Telegram-канали (публічні)\n• Довільний сайт (CSS-селектори)",
        "en": "❓ <b>Parser Bot Help</b>\n\n/start — main menu\n/newtask — new task\n/tasks — my tasks\n/settings — settings\n\n<b>Supported sources:</b>\n• RSS/Atom feeds\n• Google News (5 regions)\n• OLX listings\n• Rozetka products\n• DOU jobs\n• Telegram channels (public)\n• Custom website (CSS selectors)",
    },
    "country_ua":    {"ua": "🇺🇦 Україна",   "en": "🇺🇦 Ukraine"},
    "country_us":    {"ua": "🇺🇸 США",        "en": "🇺🇸 USA"},
    "country_eu":    {"ua": "🇪🇺 Європа",     "en": "🇪🇺 Europe"},
    "country_ca":    {"ua": "🇨🇦 Канада",     "en": "🇨🇦 Canada"},
    "country_world": {"ua": "🌍 Весь світ",   "en": "🌍 World"},
    "niche_realestate":  {"ua": "🏠 Нерухомість", "en": "🏠 Real Estate"},
    "niche_jobs":        {"ua": "💼 Вакансії",    "en": "💼 Jobs"},
    "niche_crypto":      {"ua": "₿ Крипто",       "en": "₿ Crypto"},
    "niche_tech":        {"ua": "💻 Технології",  "en": "💻 Tech"},
    "niche_cars":        {"ua": "🚗 Авто",        "en": "🚗 Cars"},
    "niche_finance":     {"ua": "💰 Фінанси",     "en": "💰 Finance"},
    "niche_news":        {"ua": "📰 Новини",      "en": "📰 News"},
    "niche_ecommerce":   {"ua": "🛒 E-commerce",  "en": "🛒 E-commerce"},
    "niche_ai":          {"ua": "🤖 AI/Tech",     "en": "🤖 AI/Tech"},
    "niche_immigration": {"ua": "✈️ Міграція",    "en": "✈️ Immigration"},
    "niche_custom":      {"ua": "⚙️ Custom",      "en": "⚙️ Custom"},
    "src_rss":      {"ua": "📡 RSS/Atom фід",      "en": "📡 RSS/Atom feed"},
    "src_google":   {"ua": "🔍 Google News",       "en": "🔍 Google News"},
    "src_olx":      {"ua": "🛍 OLX",              "en": "🛍 OLX"},
    "src_rozetka":  {"ua": "🟣 Rozetka",           "en": "🟣 Rozetka"},
    "src_dou":      {"ua": "👨‍💻 DOU Jobs",       "en": "👨‍💻 DOU Jobs"},
    "src_telegram": {"ua": "✈️ Telegram канал",    "en": "✈️ Telegram channel"},
    "src_web":      {"ua": "🌐 Сайт (CSS)",        "en": "🌐 Website (CSS)"},
    "interval_15":   {"ua": "15 хв",      "en": "15 min"},
    "interval_30":   {"ua": "30 хв",      "en": "30 min"},
    "interval_45":   {"ua": "45 хв",      "en": "45 min"},
    "interval_60":   {"ua": "1 година",   "en": "1 hour"},
    "interval_120":  {"ua": "2 години",   "en": "2 hours"},
    "interval_240":  {"ua": "4 години",   "en": "4 hours"},
    "interval_720":  {"ua": "12 годин",   "en": "12 hours"},
    "interval_1440": {"ua": "1 день",     "en": "1 day"},
    "tpl_applied": {
        "ua": "✅ Шаблон <b>{name}</b> застосовано!\n\nДжерело: {source_type}\nЗапит: {url}\nКлючові слова: {keywords}\n\nМожете змінити або прийняти:",
        "en": "✅ Template <b>{name}</b> applied!\n\nSource: {source_type}\nQuery: {url}\nKeywords: {keywords}\n\nYou can change or accept:",
    },
    "btn_accept_tpl": {
        "ua": "✅ Прийняти шаблон",
        "en": "✅ Accept template",
    },
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
