import os
import winreg
from dotenv import load_dotenv

load_dotenv()

# Check env first
key = os.environ.get("GEMINI_API_KEY")
if key:
    print(f"Direct Env: GEMINI_API_KEY found! Length: {len(key)}")
else:
    print("Direct Env: GEMINI_API_KEY not found.")

# Check Registry HKCU (User Environment Variables)
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key_reg:
        val, _ = winreg.QueryValueEx(key_reg, "GEMINI_API_KEY")
        print(f"Registry HKCU: GEMINI_API_KEY found! Length: {len(val)}, Start: {val[:4]}")
except Exception as e:
    print(f"Registry HKCU: Not found. ({e})")

# Check Registry HKLM (System Environment Variables)
try:
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"System\CurrentControlSet\Control\Session Manager\Environment") as key_reg:
        val, _ = winreg.QueryValueEx(key_reg, "GEMINI_API_KEY")
        print(f"Registry HKLM: GEMINI_API_KEY found! Length: {len(val)}, Start: {val[:4]}")
except Exception as e:
    print(f"Registry HKLM: Not found. ({e})")
