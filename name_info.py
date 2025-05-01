import requests
from bs4 import BeautifulSoup
import re

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import locale

# Nastavení české lokalizace pro datum
try:
    locale.setlocale(locale.LC_TIME, 'cs_CZ.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'C')

dny_cesky = [
    "Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"
]

def get_name_info(hledane_jmeno):
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    print(f"Hledám svátek pro jméno '{hledane_jmeno}'...")

    # Načtení stránky s kalendářem
    res = session.get("https://www.nasejmena.cz/")
    if res.status_code != 200:
        print("Nepodařilo se načíst stránku se svátky.")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    # Sestavení dnešního datumu ve formátu stránky
    dnes = datetime.now()
    den_nazev = dny_cesky[dnes.weekday()]  # např. "Čtvrtek"
    datum = f"{dnes.day}.{dnes.month}.{dnes.year}"
    hledany_radek = f"{den_nazev}\xa0{datum}"  # \xa0 je &nbsp;
    print(f"Hledaný řádek: '{hledany_radek}'")

    # Nalezení dnešního dne v tabulce
    td_dens = soup.find("td", class_="kal_dens", string=hledany_radek)
    if not td_dens:
        print("Dnešní datum nebylo nalezeno v kalendáři.")
        return None

    # Najdeme následující <td> s případným jménem
    td_name = td_dens.find_next_sibling("tr")
    while td_name and not td_name.find("td"):
        td_name = td_name.find_next_sibling("tr")

    if not td_name:
        print("Žádné informace o svátku nenalezeny.") # Pokud není nalezeno hledané jméno
        return None

    td_tag = td_name.find("td")
    if not td_tag or not td_tag.find("a"):
        print("Dnes nikdo nemá svátek.")
        return None

    name_tag = td_tag.find("a")
    name_text = name_tag.text.strip()
    href = name_tag.get("href")

    if name_text.lower() != hledane_jmeno.lower():
        print(f"Dnes má svátek někdo jiný ({name_text}), ne '{hledane_jmeno}'.")
        return None

    # Získání ID z URL
    match = re.search(r'id=(\d+)', href)
    if not match:
        print("Nepodařilo se získat ID jména.")
        return None
    onclick_id = match.group(1)

    # Získání detailů podle ID
    detail_url = f"https://www.nasejmena.cz/nj/{href}"
    res = session.get(detail_url)
    if res.status_code != 200:
        print("Nepodařilo se načíst detail jména.")
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    header = soup.find("span", {"class": "hlavicka"})
    if not header:
        print("Nepodařilo se najít informace o jménu.")
        return None

    header_text = header.text
    cisla = re.findall(r'\d+', header_text)
    if len(cisla) < 3:
        print("Nepodařilo se parsovat statistiky.")
        return None

    count = int(cisla[0])
    rank = int(cisla[1])
    avg_age = int(cisla[2])

    vysledek = {
        "name": name_text,
        "count": count,
        "rank": rank,
        "avg_age": avg_age
    }
    print(f"Výsledek: {vysledek}")
    return vysledek
