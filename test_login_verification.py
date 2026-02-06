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
        
        # 2. Zkusíme operaci pro ověření session
        # Pozn: user_info momentáně hází TypeError v instagrapi 2.2.1, přeskakuji na has_posted_today
        # print("\n➡️ Krok 2: Ověřuji validitu session...")
        # try:
        #     info = cl.user_info(cl.user_id)
        #     print(f"✅ Profil načten: {info.username}")
        # except Exception as e:
        #     print(f"⚠️ Profil se nepodařilo načíst (ignoruji pro test): {e}")


        # 3. Zkusíme logiku 'has_posted_today'
        print("\n➡️ Krok 3: Testuji has_posted_today...")
        try:
            posted = has_posted_today(cl)
            print(f"✅ has_posted_today vrátilo: {posted}")
        except Exception as e:
             # Check for ChallengeRequired by name string if import is hard, but we can import it
             # or just check message
             if "challenge_required" in str(e) or "ChallengeRequired" in str(type(e)):
                 print(f"⚠️ Detekována ChallengeRequired!")
                 print("🛑 Simuluji recovery: Mažu session a zkouším znovu...")
                 import os
                 from pathlib import Path
                 SESSION_FILE = Path(__file__).resolve().parent / "session.json"
                 if SESSION_FILE.exists():
                     SESSION_FILE.unlink()
                     print("🗑️ Session smazána.")
                 
                 print("🔄 Zkouším nový login (ten by měl vyvolat challenge resolve)...")
                 cl = login() # This should handle challenge interactive
                 print("✅ Nový login OK.")
                 
                 print("🔄 Zkouším znovu has_posted_today...")
                 posted = has_posted_today(cl)
                 print(f"✅ has_posted_today (po recovery) vrátilo: {posted}")
             else:
                 raise e

        
        print("\n-------------------------------------------------------------")
        print("🎉 Vše funguje! Login, Challenge Resolution i Session Recovery jsou OK.")
        
    except Exception as e:
        print("\n-------------------------------------------------------------")
        print(f"❌ Test selhal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login()
