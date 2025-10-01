import sys
from PyQt6.QtWidgets import QApplication
from gui import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# pyinstaller --onefile --collect-all fake_useragent main.py

# import selenium_stealth
# import os
# print(os.path.dirname(selenium_stealth.__file__))


# C:\Users\himel\Desktop\Projects\Nick Production\Traffic Generator\venv\Lib\site-packages\selenium_stealth


# pyinstaller --onefile --collect-all fake_useragent --add-data "C:/Users/himel/Desktop/Projects/Nick Production/Traffic Generator/venv/Lib/site-packages/selenium_stealth" main.py


# pyinstaller --onefile \
#   --collect-all fake_useragent \
#   --add-data "C:/Users/himel/Desktop/Projects/Nick Production/Traffic Generator/venv/Lib/site-packages/selenium_stealth;selenium_stealth" \
#   main.py