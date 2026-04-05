"""
Niche templates — pre-configured source+keywords for common use cases by country.
Each template sets: source_type, source_url, keywords, suggested name.
"""

from typing import NamedTuple


class NicheTemplate(NamedTuple):
    source_type: str
    source_url: str
    keywords: str
    name_ua: str
    name_en: str


# country -> niche -> template
TEMPLATES: dict[str, dict[str, NicheTemplate]] = {

    # -- UKRAINE ------------------------------------------------------------
    "ua": {
        "realestate": NicheTemplate(
            source_type="google",
            source_url="нерухомість купити квартира Київ",
            keywords="квартира,будинок,нерухомість,оренда",
            name_ua="Нерухомість Україна",
            name_en="Real Estate Ukraine",
        ),
        "jobs": NicheTemplate(
            source_type="dou",
            source_url="Python",
            keywords="",
            name_ua="Вакансії DOU",
            name_en="DOU Jobs",
        ),
        "crypto": NicheTemplate(
            source_type="google",
            source_url="криптовалюта біткоїн Україна",
            keywords="bitcoin,ethereum,крипто,BTC",
            name_ua="Крипто Новини UA",
            name_en="Crypto News UA",
        ),
        "tech": NicheTemplate(
            source_type="rss",
            source_url="https://dou.ua/lenta/rss/",
            keywords="",
            name_ua="Tech Новини DOU",
            name_en="DOU Tech News",
        ),
        "cars": NicheTemplate(
            source_type="google",
            source_url="авто купити продаж Україна",
            keywords="авто,машина,продаж,купити",
            name_ua="Авто Україна",
            name_en="Cars Ukraine",
        ),
        "finance": NicheTemplate(
            source_type="rss",
            source_url="https://minfin.com.ua/rss/news/",
            keywords="курс,долар,гривня,ринок",
            name_ua="Фінанси Minfin",
            name_en="Finance Minfin",
        ),
        "news": NicheTemplate(
            source_type="rss",
            source_url="https://www.pravda.com.ua/rss/view_news/",
            keywords="",
            name_ua="Новини Укрправда",
            name_en="Ukrpravda News",
        ),
        "ecommerce": NicheTemplate(
            source_type="olx",
            source_url="iPhone",
            keywords="iPhone,Samsung,нова",
            name_ua="Електроніка OLX",
            name_en="Electronics OLX",
        ),
        "ai": NicheTemplate(
            source_type="google",
            source_url="штучний інтелект AI Україна",
            keywords="AI,ChatGPT,нейромережа",
            name_ua="AI Новини UA",
            name_en="AI News UA",
        ),
        "immigration": NicheTemplate(
            source_type="google",
            source_url="міграція біженці Україна ЄС дозвіл",
            keywords="міграція,виїзд,ЄС,дозвіл",
            name_ua="Міграція UA",
            name_en="Migration UA",
        ),
    },

    # -- USA ----------------------------------------------------------------
    "us": {
        "realestate": NicheTemplate(
            source_type="rss",
            source_url="https://feeds.feedburner.com/realtor-news",
            keywords="housing,mortgage,property,market",
            name_ua="Нерухомість США",
            name_en="Real Estate USA",
        ),
        "jobs": NicheTemplate(
            source_type="google",
            source_url="tech jobs hiring remote USA 2024",
            keywords="hiring,remote,engineer,developer",
            name_ua="Вакансії США",
            name_en="Jobs USA",
        ),
        "crypto": NicheTemplate(
            source_type="rss",
            source_url="https://cointelegraph.com/rss",
            keywords="bitcoin,ethereum,crypto,SEC",
            name_ua="Крипто CoinTelegraph",
            name_en="Crypto CoinTelegraph",
        ),
        "tech": NicheTemplate(
            source_type="rss",
            source_url="https://techcrunch.com/feed/",
            keywords="",
            name_ua="Tech TechCrunch",
            name_en="TechCrunch",
        ),
        "cars": NicheTemplate(
            source_type="google",
            source_url="used cars deals USA price drop",
            keywords="Tesla,Ford,Toyota,deal,price",
            name_ua="Авто США",
            name_en="Cars USA",
        ),
        "finance": NicheTemplate(
            source_type="rss",
            source_url="https://feeds.marketwatch.com/marketwatch/topstories/",
            keywords="stock,market,Fed,inflation",
            name_ua="Фінанси MarketWatch",
            name_en="Finance MarketWatch",
        ),
        "news": NicheTemplate(
            source_type="rss",
            source_url="https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            keywords="",
            name_ua="Новини NYT",
            name_en="NYT News",
        ),
        "ecommerce": NicheTemplate(
            source_type="google",
            source_url="best deals Amazon discount USA",
            keywords="deal,discount,sale,Amazon",
            name_ua="Акції Amazon США",
            name_en="Amazon Deals USA",
        ),
        "ai": NicheTemplate(
            source_type="rss",
            source_url="https://www.wired.com/feed/tag/artificial-intelligence/rss",
            keywords="AI,LLM,ChatGPT,OpenAI,Anthropic",
            name_ua="AI Wired USA",
            name_en="AI News Wired",
        ),
        "immigration": NicheTemplate(
            source_type="google",
            source_url="US immigration visa green card 2024",
            keywords="visa,green card,USCIS,immigration",
            name_ua="Імміграція США",
            name_en="US Immigration",
        ),
    },

    # -- EUROPE -------------------------------------------------------------
    "eu": {
        "realestate": NicheTemplate(
            source_type="google",
            source_url="real estate Europe housing prices 2024",
            keywords="property,housing,market,rent",
            name_ua="Нерухомість ЄС",
            name_en="Real Estate Europe",
        ),
        "jobs": NicheTemplate(
            source_type="google",
            source_url="tech jobs Europe remote hiring 2024",
            keywords="hiring,remote,engineer,Europe",
            name_ua="Вакансії ЄС",
            name_en="Jobs Europe",
        ),
        "crypto": NicheTemplate(
            source_type="rss",
            source_url="https://decrypt.co/feed",
            keywords="bitcoin,ethereum,MiCA,Europe",
            name_ua="Крипто ЄС",
            name_en="Crypto Europe",
        ),
        "tech": NicheTemplate(
            source_type="rss",
            source_url="https://sifted.eu/feed/",
            keywords="",
            name_ua="Tech стартапи ЄС",
            name_en="EU Tech Startups",
        ),
        "finance": NicheTemplate(
            source_type="rss",
            source_url="https://feeds.reuters.com/reuters/businessNews",
            keywords="ECB,euro,inflation,market",
            name_ua="Фінанси Reuters ЄС",
            name_en="Finance Reuters EU",
        ),
        "news": NicheTemplate(
            source_type="rss",
            source_url="https://www.euronews.com/rss",
            keywords="",
            name_ua="Новини Euronews",
            name_en="Euronews",
        ),
        "ai": NicheTemplate(
            source_type="google",
            source_url="AI regulation Europe EU Act 2024",
            keywords="AI,EU AI Act,regulation,artificial intelligence",
            name_ua="AI ЄС",
            name_en="AI Europe",
        ),
        "immigration": NicheTemplate(
            source_type="google",
            source_url="Europe immigration asylum visa 2024",
            keywords="asylum,visa,Schengen,refugee,immigration",
            name_ua="Імміграція ЄС",
            name_en="EU Immigration",
        ),
        "cars": NicheTemplate(
            source_type="google",
            source_url="electric cars Europe EV market 2024",
            keywords="EV,electric,Tesla,BMW,Volkswagen",
            name_ua="Авто ЄС",
            name_en="Cars Europe",
        ),
        "ecommerce": NicheTemplate(
            source_type="google",
            source_url="best deals online shopping Europe",
            keywords="deal,discount,sale",
            name_ua="Акції ЄС",
            name_en="Deals Europe",
        ),
    },

    # -- CANADA -------------------------------------------------------------
    "ca": {
        "realestate": NicheTemplate(
            source_type="google",
            source_url="Canada real estate housing prices Toronto Vancouver",
            keywords="housing,mortgage,condo,market,Toronto",
            name_ua="Нерухомість Канада",
            name_en="Real Estate Canada",
        ),
        "jobs": NicheTemplate(
            source_type="google",
            source_url="tech jobs Canada Toronto remote hiring 2024",
            keywords="hiring,remote,developer,engineer,Canada",
            name_ua="Вакансії Канада",
            name_en="Jobs Canada",
        ),
        "immigration": NicheTemplate(
            source_type="rss",
            source_url="https://www.canada.ca/en/immigration-refugees-citizenship/news/newsroom/feed/feed.xml",
            keywords="visa,PR,express entry,immigration",
            name_ua="Імміграція Канада IRCC",
            name_en="Canada IRCC News",
        ),
        "crypto": NicheTemplate(
            source_type="google",
            source_url="crypto Canada bitcoin regulation OSC 2024",
            keywords="bitcoin,crypto,OSC,regulation",
            name_ua="Крипто Канада",
            name_en="Crypto Canada",
        ),
        "tech": NicheTemplate(
            source_type="rss",
            source_url="https://betakit.com/feed/",
            keywords="",
            name_ua="Tech Betakit Канада",
            name_en="Betakit Canada",
        ),
        "finance": NicheTemplate(
            source_type="rss",
            source_url="https://financialpost.com/feed/",
            keywords="Bank of Canada,inflation,dollar,market",
            name_ua="Фінанси Канада",
            name_en="Finance Canada",
        ),
        "news": NicheTemplate(
            source_type="rss",
            source_url="https://www.cbc.ca/cmlink/rss-topstories",
            keywords="",
            name_ua="Новини CBC Канада",
            name_en="CBC News Canada",
        ),
        "cars": NicheTemplate(
            source_type="google",
            source_url="used cars deals Canada price drop EV",
            keywords="EV,Tesla,Toyota,deal,Canada",
            name_ua="Авто Канада",
            name_en="Cars Canada",
        ),
        "ai": NicheTemplate(
            source_type="google",
            source_url="AI artificial intelligence Canada startup 2024",
            keywords="AI,LLM,startup,Vector Institute",
            name_ua="AI Канада",
            name_en="AI Canada",
        ),
        "ecommerce": NicheTemplate(
            source_type="google",
            source_url="best deals Canada Amazon Costco sale",
            keywords="deal,sale,discount,Canada",
            name_ua="Акції Канада",
            name_en="Deals Canada",
        ),
    },

    # -- WORLDWIDE ----------------------------------------------------------
    "world": {
        "crypto": NicheTemplate(
            source_type="rss",
            source_url="https://cointelegraph.com/rss",
            keywords="bitcoin,ethereum,altcoin",
            name_ua="Крипто Світ",
            name_en="Crypto World",
        ),
        "tech": NicheTemplate(
            source_type="rss",
            source_url="https://techcrunch.com/feed/",
            keywords="",
            name_ua="Tech Новини Світ",
            name_en="Tech News World",
        ),
        "ai": NicheTemplate(
            source_type="rss",
            source_url="https://feeds.feedburner.com/thenextweb",
            keywords="AI,ChatGPT,LLM,machine learning",
            name_ua="AI Новини Світ",
            name_en="AI News World",
        ),
        "finance": NicheTemplate(
            source_type="rss",
            source_url="https://feeds.reuters.com/reuters/businessNews",
            keywords="",
            name_ua="Фінанси Reuters",
            name_en="Reuters Finance",
        ),
        "news": NicheTemplate(
            source_type="rss",
            source_url="https://feeds.bbci.co.uk/news/world/rss.xml",
            keywords="",
            name_ua="Новини BBC",
            name_en="BBC World News",
        ),
        "realestate": NicheTemplate(
            source_type="google",
            source_url="global real estate market trends 2024",
            keywords="housing,property,market",
            name_ua="Нерухомість Світ",
            name_en="Real Estate World",
        ),
        "jobs": NicheTemplate(
            source_type="google",
            source_url="remote jobs worldwide tech 2024",
            keywords="remote,hiring,engineer,worldwide",
            name_ua="Вакансії Ремоут",
            name_en="Remote Jobs World",
        ),
        "cars": NicheTemplate(
            source_type="google",
            source_url="electric vehicles EV global market 2024",
            keywords="EV,electric,Tesla,BYD",
            name_ua="Авто Світ",
            name_en="Cars World",
        ),
        "ecommerce": NicheTemplate(
            source_type="google",
            source_url="best tech deals gadgets 2024",
            keywords="deal,sale,discount,gadget",
            name_ua="Гаджети/Акції Світ",
            name_en="Gadget Deals World",
        ),
        "immigration": NicheTemplate(
            source_type="google",
            source_url="immigration visa news 2024 world",
            keywords="visa,immigration,expat,residence",
            name_ua="Імміграція Світ",
            name_en="Immigration World",
        ),
    },
}


COUNTRY_NICHES = {
    "ua":    ["realestate", "jobs", "crypto", "tech", "cars", "finance", "news", "ecommerce", "ai", "immigration"],
    "us":    ["realestate", "jobs", "crypto", "tech", "cars", "finance", "news", "ecommerce", "ai", "immigration"],
    "eu":    ["realestate", "jobs", "crypto", "tech", "finance", "news", "ai", "immigration", "cars", "ecommerce"],
    "ca":    ["realestate", "jobs", "immigration", "crypto", "tech", "finance", "news", "cars", "ai", "ecommerce"],
    "world": ["crypto", "tech", "ai", "finance", "news", "realestate", "jobs", "cars", "ecommerce", "immigration"],
}


def get_template(country: str, niche: str) -> NicheTemplate | None:
    return TEMPLATES.get(country, {}).get(niche)
