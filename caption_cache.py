"""
caption_cache.py
----------------
Trvalá cache AI popisků (caption) klíčovaná jménem / svátkem (bez roku).

Soubor: output/caption_cache.json
Formát:
{
    "Svatopluk": {
        "text": "...",
        "saved_at": "2026-02-23T19:00:00"
    },
    "Den míru a porozumění": {
        "text": "...",
        "saved_at": "2026-02-23T19:00:00"
    },
    ...
}

Použití:
    from caption_cache import get_cached_caption, save_caption_to_cache

    text = get_cached_caption("Svatopluk")
    if text is None:
        text = call_ai(...)
        save_caption_to_cache("Svatopluk", text)
"""

import json
import os
from datetime import datetime

# Cesta ke cache souboru – vždy relativně ke složce tohoto modulu
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(_BASE_DIR, "output", "caption_cache.json")


def _load_cache() -> dict:
    """Načte cache ze souboru, nebo vrátí prázdný dict."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️ [caption_cache] Nelze načíst cache: {e} – začínám s prázdnou cache.")
        return {}


def _save_cache(cache: dict) -> None:
    """Zapíše cache do souboru."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"⚠️ [caption_cache] Nelze uložit cache: {e}")


def get_cached_caption(key: str) -> str | None:
    """
    Vrátí uložený AI popisek pro daný klíč (jméno / svátek),
    nebo None pokud v cache není.

    Args:
        key: Jméno nebo název svátku (nezávislé na roku).

    Returns:
        Uložený text nebo None.
    """
    cache = _load_cache()
    entry = cache.get(key)
    if entry and entry.get("text"):
        print(f"📦 [caption_cache] Cache HIT pro '{key}' (uloženo: {entry.get('saved_at', '?')})")
        return entry["text"]
    print(f"🔍 [caption_cache] Cache MISS pro '{key}' – budu volat AI.")
    return None


def save_caption_to_cache(key: str, text: str) -> None:
    """
    Uloží AI popisek do trvalé cache.

    Args:
        key:  Jméno nebo název svátku.
        text: Vygenerovaný AI text.
    """
    cache = _load_cache()
    cache[key] = {
        "text": text,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }
    _save_cache(cache)
    print(f"💾 [caption_cache] Uloženo do cache: '{key}'")


def list_cached_keys() -> list[str]:
    """Vrátí seznam všech klíčů v cache (pro ladění)."""
    return list(_load_cache().keys())
