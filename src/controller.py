from PyQt6.QtCore import QUrl, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QApplication
from datetime import datetime

from dashboard import Ui_MainWindow
from mqtt import MQTT


class MainController(QMainWindow):
    debug_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.textDebug.setReadOnly(True)
        self.debug_signal.connect(self._append_debug_text)

        self.mqtt = MQTT()

        # Default config
        self.node_red_url: str = "http://localhost:1880"
        self.broker_url: str = "broker.hivemq.com"
        self.broker_port: int = 1883
        self.broker_topic: str = "MQTT/accelerometer"

        self.mqtt_settings = self.mqtt.get_current_settings()

        self.setup_web_view()
        self.setup_mqtt()
        self.setup_settings_connections()
        self.setup_stacked_widget()

        self.ui.stackedWidget.setCurrentWidget(self.ui.pageHome)

        app = QApplication.instance()
        app.aboutToQuit.connect(self.cleanup)

    # =========================
    # Web View Setup
    # =========================

    def setup_web_view(self):
        self.ui.webNodeRed.loadFinished.connect(
            lambda ok: self.debug_print(
                "[Web]: Successfully loaded"
                if ok
                else "[Web]: Failed to connect! Check internet or URL!"
            )
        )
        self.ui.webNodeRed.loadStarted.connect(
            lambda: self.debug_print("[Web]: Loading the web...")
        )
        self.ui.webNodeRed.loadProgress.connect(
            lambda progress: self.debug_print(f"[Web]: Progress {progress}%")
        )

    def setup_web(self, ok: bool):
        pass

    # =========================
    # MQTT Setup
    # =========================

    def setup_mqtt(self):
        self.mqtt.set_debug_callback(self.debug_print)
        self.mqtt.set_url(self.broker_url, self.broker_port)
        self.mqtt.set_user("", "")
        self.mqtt.set_topic(self.broker_topic)
        self.mqtt.start()

    # =========================
    # Settings Page
    # =========================

    def setup_settings_connections(self):
        self.ui.lineHostMQTT.textChanged.connect(
            lambda text: self.mqtt_settings.update({"host": text})
        )
        self.ui.linePortMQTT.textChanged.connect(
            lambda text: self.mqtt_settings.update({"port": text})
        )
        self.ui.lineTopicMQTT.textChanged.connect(
            lambda text: self.mqtt_settings.update({"topic": text})
        )
        self.ui.lineUsernameMQTT.textChanged.connect(
            lambda text: self.mqtt_settings.update({"username": text})
        )
        self.ui.linePasswordMQTT.textChanged.connect(
            lambda text: self.mqtt_settings.update({"password": text})
        )
        self.ui.btnSaveMQTT.clicked.connect(self.on_save_mqtt)

    def on_save_mqtt(self):
        try:
            port = int(self.mqtt_settings["port"])
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "Port must be a number.")
            return

        self.mqtt.stop()

        self.mqtt.set_url(self.mqtt_settings["host"], port)
        self.mqtt.set_user(
            self.mqtt_settings["username"], self.mqtt_settings["password"]
        )
        self.mqtt.set_topic(self.mqtt_settings["topic"])
        self.mqtt.start()

        QMessageBox.information(self, "MQTT", "Settings applied and reconnected.")

    # =========================
    # Navigation
    # =========================

    def setup_stacked_widget(self):
        self.ui.stackedWidget.currentChanged.connect(self.page_change)

        self.ui.btnHome.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.pageHome)
        )
        self.ui.btnNodeRed.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.pageNodeRed)
        )
        self.ui.btnSettings.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.pageSettings)
        )
        self.ui.btnDebug.clicked.connect(
            lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.pageDebug)
        )

    def page_change(self, index: int):
        widget = self.ui.stackedWidget.widget(index)
        if widget is self.ui.pageNodeRed:
            self.page_web()
        elif widget is self.ui.pageSettings:
            self.page_settings()

    def page_web(self):
        if self.ui.webNodeRed.url().toString() == "about:blank":
            self.ui.webNodeRed.setUrl(QUrl(self.node_red_url))

    def page_settings(self):
        self.mqtt_settings = self.mqtt.get_current_settings()

        self.ui.lineHostMQTT.setText(self.mqtt_settings["host"])
        self.ui.linePortMQTT.setText(self.mqtt_settings["port"])
        self.ui.lineTopicMQTT.setText(self.mqtt_settings["topic"])
        self.ui.lineUsernameMQTT.setText(self.mqtt_settings["username"])
        self.ui.linePasswordMQTT.setText(self.mqtt_settings["password"])

    # =========================
    # Cleanup
    # =========================

    def cleanup(self):
        self.mqtt.stop()

    # =========================
    # Thread-Safe Debug System
    # =========================

    def debug_print(self, message: str) -> None:
        """
        Called from MQTT thread or UI thread.
        NEVER update UI directly here.
        """
        print(message)
        self.debug_signal.emit(message)

    def _append_debug_text(self, message: str):
        """
        Runs in Qt main thread safely.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"

        self.ui.textDebug.append(formatted)

        # Auto-scroll
        scrollbar = self.ui.textDebug.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # Optional: limit log size
        max_lines = 300
        if self.ui.textDebug.document().blockCount() > max_lines:
            cursor = self.ui.textDebug.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
