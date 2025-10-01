import subprocess



command = """pyinstaller --onefile 
  --collect-all fake_useragent --windowed
  --add-data "C:/Users/himel/Desktop/Projects/Nick Production/Traffic Generator/venv/Lib/site-packages/selenium_stealth;selenium_stealth" 
  main.py"""

command = command.replace('\n', ' ').replace('  ', ' ').replace('   ', ' ')

print('COMMAND:', command)

subprocess.call(command, shell=True)