# SaveNameStats.py
import os
import json
from datetime import datetime, timedelta
from name_info import get_today_names_and_holidays, get_name_details
from name_utils import letter_map

STATS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'name_stats.json')


def save_name_stats():
    """Uloží statistiky jmen pro celý rok do JSON souboru"""
    print("💾 Spouštím ukládání statistik jmen pro celý rok...")

    # Inicializace datové struktury
    all_stats = {}
    current_date = datetime.now()

    # Projdeme všechny dny v roce
    start_date = datetime(current_date.year, 1, 1)
    end_date = datetime(current_date.year, 12, 31)
    delta = timedelta(days=1)

    date = start_date
    while date <= end_date:
        date_str = date.strftime("%Y-%m-%d")
        print(f"🔍 Zpracovávám {date_str}...")

        # Získat jména pro daný den
        names, _ = get_today_names_and_holidays(date)
        day_stats = {}

        if names:
            for name in names:
                print(f"  ⬇️ Stahuji statistiky pro {name}...")
                stats = get_name_details(name, letter_map)
                if stats:
                    day_stats[name] = stats

        all_stats[date_str] = day_stats
        date += delta

    # Uložení do souboru
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)

    print(f"✅ Statistiky uloženy do {STATS_FILE}")
    return all_stats


def load_name_stats():
    """Načte uložené statistiky ze souboru"""
    if not os.path.exists(STATS_FILE):
        return {}

    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_name_stats_failsafe(name, date):
    """Získává statistiky z lokálního úložiště"""
    date_str = date.strftime("%Y-%m-%d")
    stats = load_name_stats()

    if date_str in stats and name in stats[date_str]:
        print(f"✅ [Failsafe] Načteny statistiky pro {name} z lokálního úložiště")
        return stats[date_str][name]

    print(f"⚠️ [Failsafe] Statistiky pro {name} ({date_str}) nebyly nalezeny")
    return None



if __name__ == "__main__":
    save_name_stats()