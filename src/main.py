import sys

from PyQt6.QtWidgets import QApplication
from controller import MainController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainController()
    widget.setWindowTitle("KAI MQTT Dashboard")
    widget.show()
    sys.exit(app.exec())
