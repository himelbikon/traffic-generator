import subprocess
from PIL import Image

logo_path = "assets/logo.png"
logo_ico_path = "assets/logo.ico"
logo = Image.open(logo_path)
logo.save(logo_ico_path, format="ICO")

command = f"""pyinstaller --onefile ^
  --name "Traffic Generator v0.4" ^
  --collect-all fake_useragent --windowed ^
  --add-data "C:/Users/himel/Desktop/Projects/Nick Production/Traffic Generator/venv/Lib/site-packages/selenium_stealth;selenium_stealth" ^
  --icon="{logo_ico_path}" ^
  main.py
"""

replaces = [
  ('\n', ' '),
  ('  ', ' '),
  ('   ', ' '),
  ('^', ' ')
]

for replace in replaces:
    command = command.replace(replace[0], replace[1])

print('COMMAND:', command)

subprocess.call(command, shell=True)