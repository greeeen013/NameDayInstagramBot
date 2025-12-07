import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from name_utils import letter_map, dny_cesky

def get_today_names_and_holidays(dnes=datetime.now()):
    url = f"https://kalendar.beda.cz/den-v-kalendari?month={dnes.month}&day={dnes.day}"
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    res = session.get(url)
    if res.status_code != 200:
        print("❌ [name_info] Nelze načíst kalendar.beda.cz")
        return None, None
    soup = BeautifulSoup(res.text, "html.parser")
    # Najdi tabulku s <th>roky</th>...
    table = soup.find("table")
    if not table:
        return None, None

    def is_year_in_range(year_text, target_year):
        """Pomocná funkce pro kontrolu, zda je rok v rozsahu/seznamu"""
        parts = year_text.split(",")
        for part in parts:
            part = part.strip()
            if "-" in part:
                try:
                    start_str, end_str = part.split("-")
                    start = int(start_str)
                    # Pokud je konec rozsahu prázdný, bere se jako "do teď" (nebo prostě platný)
                    # Ale zde bývají např "2002-2026".
                    if end_str:
                        end = int(end_str)
                    else:
                        end = datetime.now().year + 10 # Future proof fallback
                    
                    if start <= target_year <= end:
                        return True
                except ValueError:
                    continue
            else:
                try:
                    if int(part) == target_year:
                        return True
                except ValueError:
                    continue
        return False

    names_list = []
    events_list = []
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) != 2:
            continue
        years_text = cols[0].get_text(strip=True)
        
        # Robustnější kontrola roku
        today_year = datetime.now().year
        # Pro účely testování z outside nebo pokud dnes není passed jinak
        if isinstance(dnes, datetime):
             today_year = dnes.year

        if is_year_in_range(years_text, today_year):
            # Druhý sloupec obsahuje text
            cell = cols[1]
            # Najdi všechny odkazy (klikatelné jména)
            for a in cell.find_all("a"):
                name = a.get_text(strip=True)
                if name:
                    names_list.append(name)
            # Najdi neklikatelné textové části
            for element in cell.contents:
                # pokud je element NavigableString (text) nebo Tag, který není <a>
                if getattr(element, "name", None) != "a":
                    text = str(element).strip()
                    # ignoruj prázdné texty nebo jen čárky
                    if text and text not in [",", ";"]:
                        events_list.append(text)
    
    # Odstranění duplicit a vyčištění
    names_list = sorted(list(set(names_list)))
    # U events_list chceme zachovat pořadí, ale odstranit duplicity
    events_list_clean = []
    seen = set()
    for e in events_list:
        if e not in seen:
            events_list_clean.append(e)
            seen.add(e)
            
    return names_list, events_list_clean


def get_name_details(name, letter_map, use_failsafe=True):
    """Získává detaily jména s možností fallbacku na lokální data"""
    try:
        # Zjisti písmeno (vč. "Ch" výjimky)
        if name.lower().startswith("ch") and "Ch" in letter_map:
            letter_key = "Ch"
        else:
            letter_key = name[0].upper()

        if letter_key not in letter_map:
            print(f"⚠️ Písmeno '{letter_key}' pro jméno {name} nebylo nalezeno v mapě.")

        letter_id = letter_map[letter_key]

        # Načti stránku s výpisem jmen pro dané písmeno
        url = f"https://www.nasejmena.cz/nj/cetnost.php?id={letter_id}&typ=ab"
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            print(f"❌ Nelze načíst seznam jmen pro písmeno {letter_key}")

        soup = BeautifulSoup(res.text, "html.parser")

        # Najdi konkrétní div s jmény
        jmena_div = soup.find("div", id="tab_overflow_jmeno")
        if not jmena_div:
            print("❌ Nenalezen div s jmény (tab_overflow_jmeno)")

        # Najdi všechny buňky s třídou tab_vyplneny
        name_cells = jmena_div.find_all("td", class_="tab_vyplneny")

        for cell in name_cells:
            name_text = next((text for text in cell.stripped_strings), "")
            if name_text.lower() == name.lower():
                onclick = cell.get("onclick", "")
                match = re.search(r"TabClick\((\d+),\s*['\"]jmeno['\"]\)", onclick)
                if not match:
                    print(f"❌ Nenalezeno ID pro jméno {name_text}")

                name_id = match.group(1)
                # Načtení detailní stránky
                detail_url = f"https://www.nasejmena.cz/nj/cetnost.php?id={name_id}&typ=jmeno"
                res = requests.get(detail_url, timeout=10)
                if res.status_code != 200:
                    print("❌ Nelze načíst detail jména.")

                detail_soup = BeautifulSoup(res.text, "html.parser")
                header = detail_soup.find("span", {"class": "hlavicka"})
                dopinfo = detail_soup.find("span", {"class": "dopinfo"})

                if not header:
                    print("❌ Informace o jménu nenalezeny.")

                # Zpracování statistik
                header_text = header.get_text()
                numbers = re.findall(r'\d+', header_text)
                if len(numbers) < 3:
                    print("❌ Nepodařilo se parsovat statistiky pro jméno.")

                count = int("".join(numbers[0:-2])) if len(numbers) > 3 else int(numbers[0])
                rank = int(numbers[-2])
                avg_age = int(numbers[-1])

                # Zpracování doplňujících informací
                origin = "neuvedeno"
                meaning = "neuvedeno"
                if dopinfo:
                    dopinfo_text = dopinfo.get_text()
                    origin_match = re.search(r'původ:\s*([^,]+)', dopinfo_text)
                    if origin_match:
                        origin = origin_match.group(1).strip()
                    meaning_match = re.search(r'význam:\s*([^,]+)', dopinfo_text, re.IGNORECASE)
                    if meaning_match:
                        meaning = meaning_match.group(1).strip()

                return {
                    "name": name_text,
                    "count": count,
                    "rank": rank,
                    "avg_age": avg_age,
                    "origin": origin,
                    "meaning": meaning
                }

        print(f"❌ Jméno '{name}' nebylo nalezeno na stránce písmene {letter_key}.")

    except Exception as e:
        print(f"❌ Neočekávaná chyba při získávání statistik pro {name}: {str(e)}")