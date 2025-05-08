import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

dny_cesky = [
        "Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"
    ]

def get_name_info(hledane_jmeno):
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    print(f"🔍 [name_info] Hledám informace k jménu: {hledane_jmeno}...")

    # Načtení stránky se svátky
    res = session.get("https://www.nasejmena.cz/")
    if res.status_code != 200:
        print("❌ [name_info] Nepodařilo se načíst stránku se svátky.")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    dnes = datetime.now()
    den_nazev = dny_cesky[dnes.weekday()]
    datum = f"{dnes.day}.{dnes.month}.{dnes.year}"
    hledany_radek = f"{den_nazev}\xa0{datum}"  # např. Čtvrtek 1.5.2025
    print(f"🔍 [name_info] Kontroluju zda sedí datum: '{hledany_radek}'")

    # Najdi dnešní buňku s datem
    td_dens = soup.find("td", string=hledany_radek)
    if not td_dens:
        # Zkusíme alternativní formát (např. "Sobota&nbsp;3.5.2025")
        alternativni_format = f"{den_nazev}&nbsp;{datum}"
        td_dens = soup.find("td", string=alternativni_format)
        if not td_dens:
            print("❌ [name_info] Dnešní datum nebylo nalezeno v kalendáři.")
            return None

    # Procházej další řádky, dokud nenajde jméno nebo nový den
    td = td_dens.find_parent("tr").find_next_sibling("tr")
    while td:
        obsah_td = td.find("td")
        if not obsah_td:
            td = td.find_next_sibling("tr")
            continue

        # Zkontrolujeme všechny možné třídy pro jména
        if any(cls in obsah_td.get("class", []) for cls in ["kal_jme", "kal_jmev", "kal_jmes"]):
            # Najdeme všechny odkazy v buňce (pro případ více jmen)
            a_tags = obsah_td.find_all("a")
            if not a_tags:
                print("❓ [name_info] Dnes nikdo nemá svátek.")
                return None

            # Projdeme všechna jména v daný den
            for a_tag in a_tags:
                name_text = a_tag.text.strip()
                if name_text.lower() == hledane_jmeno.lower():
                    href = a_tag.get("href")
                    # Získání detailní stránky jména
                    detail_url = f"https://www.nasejmena.cz/nj/{href}"
                    res = session.get(detail_url)
                    if res.status_code != 200:
                        print("❌ [name_info] Nepodařilo se načíst detail jména.")
                        return None

                    soup = BeautifulSoup(res.text, "html.parser")
                    header = soup.find("span", {"class": "hlavicka"})
                    if not header:
                        print("❌ [name_info] Nepodařilo se najít informace o jménu.")
                        return None

                    header_text = header.text
                    cisla = re.findall(r'\d+', header_text)
                    if len(cisla) < 3:
                        print("❌ [name_info] Nepodařilo se parsovat statistiky.")
                        return None

                    # Získání původu jména
                    dopinfo = soup.find("span", {"class": "dopinfo"})
                    puvod = None
                    if dopinfo:
                        # Extrahujeme původ z textu
                        puvod_match = re.search(r'původ:\s*([^,]+)', dopinfo.text)
                        if puvod_match:
                            puvod = puvod_match.group(1).strip()

                    count = int(cisla[0])
                    rank = int(cisla[1])
                    avg_age = int(cisla[2])

                    vysledek = {
                        "name": name_text,
                        "count": count,
                        "rank": rank,
                        "avg_age": avg_age,
                        "origin": puvod if puvod else "neuvedeno"
                    }
                    print(f"✅ [name_info] Výsledek: {vysledek}")
                    return vysledek

            # Pokud jsme prošli všechna jména a nenašli jsme hledané
            print(f"❓ [name_info] Dnes má svátek {', '.join([a.text.strip() for a in a_tags])}, ale ne '{hledane_jmeno}'.")
            return None

        # Pokud narazíme na další den, končíme
        if any(cls in obsah_td.get("class", []) for cls in ["kal_dens", "kal_den", "kal_denv"]):
            break

        td = td.find_next_sibling("tr")

    print("❌ [name_info] Dnes nikdo nemá svátek.")
    return None


def get_todays_holiday():
    dny_cesky = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    print("🔍 Hledám neklikatelná jména pro dnešní den...")

    res = session.get("https://www.nasejmena.cz/")
    if res.status_code != 200:
        print("❌ Nepodařilo se načíst stránku se svátky.")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    dnes = datetime.now()
    den_nazev = dny_cesky[dnes.weekday()]
    datum = f"{dnes.day}.{dnes.month}.{dnes.year}"
    hledany_radek = f"{den_nazev}\xa0{datum}"

    td_dens = soup.find("td", string=hledany_radek)
    if not td_dens:
        alternativni_format = f"{den_nazev}&nbsp;{datum}"
        td_dens = soup.find("td", string=alternativni_format)
        if not td_dens:
            print("❌ Dnešní datum nebylo nalezeno v kalendáři.")
            return None

    td = td_dens.find_parent("tr").find_next_sibling("tr")
    non_clickable_names = []

    while td:
        obsah_td = td.find("td")
        if not obsah_td:
            td = td.find_next_sibling("tr")
            continue

        if any(cls in obsah_td.get("class", []) for cls in ["kal_jme", "kal_jmev", "kal_jmes"]):
            for element in obsah_td.contents:
                if element.name != "a" and element.strip():
                    non_clickable_names.append(element.strip())

        if any(cls in obsah_td.get("class", []) for cls in ["kal_dens", "kal_den", "kal_denv"]):
            break

        td = td.find_next_sibling("tr")

    if non_clickable_names:
        print(f"✅ Neklikatelné jméno: {non_clickable_names[0]}")
        return non_clickable_names[0]  # Vrátíme pouze první jméno jako string
    else:
        print("❌ Dnes nebyla nalezena žádná neklikatelná jména.")
        return None

    
def get_todays_names():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    print("🔍 [name_info] Zjišťuji, jaké jméno má dnes svátek...")

    # Načtení stránky se svátky
    res = session.get("https://www.nasejmena.cz/")
    if res.status_code != 200:
        print("❌ [name_info] Nepodařilo se načíst stránku se svátky.")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    # Vlastní mapování českých dnů
    dny_cesky = [
        "Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"
    ]
    dnes = datetime.now()
    den_nazev = dny_cesky[dnes.weekday()]
    datum = f"{dnes.day}.{dnes.month}.{dnes.year}"
    hledane_formaty = [
        f"{den_nazev}\xa0{datum}",  # např. "Čtvrtek\xa01.5.2025"
        f"{den_nazev}&nbsp;{datum}" # např. "Sobota&nbsp;3.5.2025"
    ]

    # Najdi dnešní buňku s datem
    td_dens = None
    for format in hledane_formaty:
        td_dens = soup.find("td", string=format)
        if td_dens:
            break

    if not td_dens:
        print("❌ [name_info] Dnešní datum nebylo nalezeno v kalendáři.")
        return None

    # Procházej další řádky, dokud nenajde jména nebo nový den
    td = td_dens.find_parent("tr").find_next_sibling("tr")
    jmena = []

    while td:
        obsah_td = td.find("td")
        if not obsah_td:
            td = td.find_next_sibling("tr")
            continue

        # Zkontrolujeme všechny možné třídy pro jména
        if any(cls in obsah_td.get("class", []) for cls in ["kal_jme", "kal_jmev", "kal_jmes"]):
            # Najdeme všechny odkazy v buňce (pro případ více jmen)
            a_tags = obsah_td.find_all("a")
            if a_tags:
                jmena.extend([a.text.strip() for a in a_tags])

        # Pokud narazíme na další den, končíme
        if any(cls in obsah_td.get("class", []) for cls in ["kal_dens", "kal_den", "kal_denv"]):
            break

        td = td.find_next_sibling("tr")

    if not jmena:
        print("❓ [name_info] Dnes nikdo nemá svátek.")
        return None

    print(f"✅ [name_info] Dnes má svátek: {', '.join(jmena)}")
    return jmena

if __name__ == "__main__":
    jmeno = get_todays_names()
    print(jmeno)
    info = get_name_info(jmeno)
    if info:
        print(f"Jméno: {info['name']}, Počet nositelů: {info['count']}, Pořadí: {info['rank']}, Průměrný věk: {info['avg_age']} půvopd: {info['origin']}")
    else:
        print("Žádné informace nebyly nalezeny.")