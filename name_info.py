import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

dny_cesky = [
        "Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"
    ]

def get_today_names_and_holidays():
    dnes = datetime.now()
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
    names_list = []
    events_list = []
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) != 2:
            continue
        years_text = cols[0].get_text(strip=True)
        # Hledáme řádek končící "-2025"
        today_year = str(datetime.now().year)
        if years_text.endswith(today_year):
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
    return names_list, events_list

letter_map = {
    "A": 1, "Á": 2, "Ą": 3, "B": 4, "C": 5, "Č": 6, "Ć": 7, "Ç": 8,
    "D": 9, "Ď": 10, "Đ": 11, "E": 12, "É": 13, "Ě": 14, "F": 15, "G": 16,
    "H": 17, "I": 18, "J": 19, "K": 20, "L": 21, "Ĺ": 22, "Ł": 23, "M": 24,
    "N": 25, "Ň": 26, "O": 27, "Ó": 28, "Ö": 29, "Ő": 30, "P": 31, "Q": 32,
    "R": 33, "Ř": 34, "Ŕ": 35, "S": 36, "Š": 37, "Ś": 38, "Ş": 39, "T": 40,
    "Ť": 41, "Ţ": 42, "U": 43, "Ú": 44, "Ü": 45, "Ű": 46, "V": 47, "W": 48,
    "X": 49, "Y": 50, "Z": 51, "Ž": 52, "Ż": 53, "¬": 54
}

def get_name_details(name, letter_map):
    # Zjisti písmeno (vč. "Ch" výjimky)
    if name.lower().startswith("ch") and "Ch" in letter_map:
        letter_key = "Ch"
    else:
        letter_key = name[0].upper()
    if letter_key not in letter_map:
        print(f"⚠️ Písmeno '{letter_key}' pro jméno {name} nebylo nalezeno v mapě.")
        return None
    letter_id = letter_map[letter_key]

    # Načti stránku s výpisem jmen pro dané písmeno
    url = f"https://www.nasejmena.cz/nj/cetnost.php?id={letter_id}&typ=ab"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"❌ Nelze načíst seznam jmen pro písmeno {letter_key}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    # Najdi konkrétní div s jmény
    jmena_div = soup.find("div", id="tab_overflow_jmeno")
    if not jmena_div:
        print("❌ Nenalezen div s jmény (tab_overflow_jmeno)")
        return None

    # Najdi všechny buňky s třídou tab_vyplneny
    name_cells = jmena_div.find_all("td", class_="tab_vyplneny")

    for cell in name_cells:
        # Získat čistý text jména
        name_text = next((text for text in cell.stripped_strings), "")

        if name_text.lower() == name.lower():
            onclick = cell.get("onclick", "")
            match = re.search(r"TabClick\((\d+),\s*['\"]jmeno['\"]\)", onclick)
            if not match:
                print(f"❌ Nenalezeno ID pro jméno {name_text}")
                return None

            name_id = match.group(1)
            # Načtení detailní stránky
            detail_url = f"https://www.nasejmena.cz/nj/cetnost.php?id={name_id}&typ=jmeno"
            res = requests.get(detail_url)
            if res.status_code != 200:
                print("❌ Nelze načíst detail jména.")
                return None

            detail_soup = BeautifulSoup(res.text, "html.parser")
            header = detail_soup.find("span", {"class": "hlavicka"})
            dopinfo = detail_soup.find("span", {"class": "dopinfo"})

            if not header:
                print("❌ Informace o jménu nenalezeny.")
                return None

            # Zpracování statistik
            header_text = header.get_text()
            numbers = re.findall(r'\d+', header_text)
            if len(numbers) < 3:
                print("❌ Nepodařilo se parsovat statistiky pro jméno.")
                return None

            count = int("".join(numbers[0:-2])) if len(numbers) > 3 else int(numbers[0])
            rank = int(numbers[-2])
            avg_age = int(numbers[-1])

            # Zpracování doplňujících informací
            origin = "neuvedeno"
            meaning = "neuvedeno"
            if dopinfo:
                dopinfo_text = dopinfo.get_text()
                # Parsování původu
                origin_match = re.search(r'původ:\s*([^,]+)', dopinfo_text)
                if origin_match:
                    origin = origin_match.group(1).strip()
                # Parsování významu
                meaning_match = re.search(r'význam:\s*([^,]+)', dopinfo_text, re.IGNORECASE)
                if meaning_match:
                    meaning = meaning_match.group(1).strip()

            return {
                "name": name_text,
                "count": count,
                "rank": rank,
                "avg_age": avg_age,
                "origin": origin,
                "meaning": meaning  # Přidán význam jména
            }

    print(f"❌ Jméno '{name}' nebylo nalezeno na stránce písmene {letter_key}.")
    return None