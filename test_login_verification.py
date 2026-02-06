from instagram_bot import login, has_posted_today
import sys

def test_login():
    print("🚀 Spouštím izolovaný test přihlášení (bez AI generování)...")
    print("-------------------------------------------------------------")
    try:
        # 1. Zkusíme se přihlásit
        print("➡️ Krok 1: Volám login()...")
        cl = login()
        print(f"✅ Přihlášení proběhlo úspěšně. User ID: {cl.user_id}")
        
        # 2. Zkusíme operaci, která ověří, že session je "živá" a není flaggovaná
        print("\n➡️ Krok 2: Ověřuji validitu session...")
        try:
            info = cl.user_info(cl.user_id)
            print(f"✅ Profil načten: {info.username}")
        except Exception as e:
            print(f"⚠️ Profil se nepodařilo načíst (možná ban/challenge?): {e}")
            raise e

        # 3. Zkusíme logiku 'has_posted_today'
        print("\n➡️ Krok 3: Testuji has_posted_today...")
        posted = has_posted_today(cl)
        print(f"✅ has_posted_today vrátilo: {posted}")
        
        print("\n-------------------------------------------------------------")
        print("🎉 Vše funguje! Login, Challenge Resolution i Session Recovery jsou OK.")
        
    except Exception as e:
        print("\n-------------------------------------------------------------")
        print(f"❌ Test selhal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login()
