"""
Unified parser interface.
Every parser returns list[ParsedItem].
"""
from dataclasses import dataclass, field


@dataclass
class ParsedItem:
    url:         str
    title:       str
    description: str  = ""
    price:       str  = ""
    image_url:   str  = ""
    pub_date:    str  = ""

    def make_hash(self) -> str:
        import hashlib
        raw = f"{self.url}|{self.title}"
        return hashlib.md5(raw.encode()).hexdigest()
