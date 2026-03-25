import paho.mqtt.client as mqtt
import json
from typing import Optional, Callable, Any


class MQTT:
    def __init__(self, parent=None):
        # Configuration
        self.url: str = ""
        self.port: int = 1883
        self.topic: str = ""
        self.qos: int = 0
        self.username: str = ""
        self.password: str = ""

        # State
        self.payload: str = ""
        self.data: dict[str, Any] = {}
        self.client: Optional[mqtt.Client] = None
        self.msg_callback: Optional[Callable[[str, str], None]] = None
        self.debug_callback: Optional[Callable[[str], None]] = None

    def _debug(self, message: str) -> None:
        if self.debug_callback:
            self.debug_callback(message)
        else:
            print(message)

    def set_url(self, url: str, port: int) -> None:
        self.url = url
        self.port = port

    def set_topic(self, topic: str, qos: int = 0) -> None:
        self.topic = topic
        self.qos = qos
        if self.client and self.client.is_connected():
            self.client.subscribe(topic, qos)
            self._debug(f"[MQTT]: Subscribed to topic -> {topic}")

    def set_user(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    def start(self) -> None:
        """Connect to broker and start the network loop."""
        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.reconnect_delay_set(1, 120)  # Auto-reconnect

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        try:
            self.client.connect(self.url, self.port)
        except Exception as e:
            self._debug(f"[MQTT]: Connection failed -> {e}")
            return

        self.client.loop_start()

    def stop(self) -> None:
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self._debug("[MQTT]: Stopped")

    def subscribe(self, topic: str, qos: int = 0) -> None:
        if self.client and self.client.is_connected():
            self.client.subscribe(topic, qos)
            self._debug(f"[MQTT]: Subscribed to topic -> {topic}")
        else:
            self._debug("[MQTT]: Cannot subscribe – client not connected")

    def get_current_settings(self) -> dict[str, str]:
        return {
            "host": self.url,
            "port": str(self.port),
            "topic": self.topic,
            "username": self.username,
            "password": self.password,
        }

    def get_data(self) -> dict[str, Any]:
        return self.data

    def set_msg_callback(self, callback: Callable[[str, str], None]) -> None:
        self.msg_callback = callback

    def set_debug_callback(self, callback: Callable[[str], None]) -> None:
        self.debug_callback = callback

    def on_connect(self, client, userdata, flags, reasonCode, properties=None) -> None:
        self._debug(f"[MQTT]: Connected with reason code {reasonCode}")
        if self.topic:
            self.subscribe(self.topic, self.qos)

    def on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        payload = msg.payload.decode("utf-8")
        self._debug(f"[MQTT]: Received message -> {payload}")

        self.payload = payload
        try:
            self.data = json.loads(payload)
        except json.JSONDecodeError:
            self._debug("[MQTT]: Payload is not valid JSON")

        if self.msg_callback:
            self.msg_callback(topic, payload)

    def on_disconnect(self, client, userdata, reasonCode, properties=None) -> None:
        self._debug(f"[MQTT]: Disconnected (reason {reasonCode})")
