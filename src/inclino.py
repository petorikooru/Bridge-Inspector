import paho.mqtt.client as mqtt
import json
import csv
import time
from datetime import datetime, timezone, timedelta

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "topic_loadsensing"
CSV_FILE = "filtered_sensor_log.csv"

# Inisialisasi Header CSV baru
with open(CSV_FILE, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(
        [
            "timestamp_wib",
            "node_id",
            "node_model",
            "output_parameter",
            "alert_report",
            "temperature",
            "num_events_above_threshold",
            "num_active_windows",
            "transmission_threshold",
            "event_timestamp_wib",
            "event_duration_seconds",
            "num_windows_event",
            "dominant_freq_x",
            "dominant_freq_y",
            "dominant_freq_z",
            "error_code_x",
            "error_code_y",
            "error_code_z",
            "composed_error_code",
        ]
    )


def convert_to_wib(utc_string):
    parsed_utc = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    wib_tz = timezone(timedelta(hours=7))
    return parsed_utc.astimezone(wib_tz).strftime("%Y-%m-%d %H:%M:%S")


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Terhubung ke broker!")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Gagal terhubung, kode: {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        # Filter hanya vibrationRegulationDataMsgV1
        if payload.get("type") == "vibrationRegulationDataMsgV1":
            read_timestamp_wib = convert_to_wib(payload.get("readTimestamp"))

            node_id = payload.get("nodeId")
            node_model = payload.get("nodeModel")
            output_parameter = payload.get("outputParameter")
            alert_report = payload.get("alertReport")

            readings = payload.get("readings", [])

            for reading in readings:
                reporting_info = reading.get("reportingInfo", {})
                events = reading.get("reportingEvents", [])

                temperature = reporting_info.get("temperature")
                num_events_above = reporting_info.get("numEventsAboveReportThreshold")
                num_active_windows = reporting_info.get("numActiveWindows")
                transmission_threshold = reporting_info.get("transmissionThreshold")

                for event in events:
                    event_timestamp_wib = convert_to_wib(event.get("timestampEvent"))

                    data_row = [
                        read_timestamp_wib,
                        node_id,
                        node_model,
                        output_parameter,
                        alert_report,
                        temperature,
                        num_events_above,
                        num_active_windows,
                        transmission_threshold,
                        event_timestamp_wib,
                        event.get("eventDurationSeconds"),
                        event.get("numWindowsEvent"),
                        event.get("predominantFrequencyAxisXEvent"),
                        event.get("predominantFrequencyAxisYEvent"),
                        event.get("predominantFrequencyAxisZEvent"),
                        event.get("particlePeakVelocityAxisXErrorCode"),
                        event.get("particlePeakVelocityAxisYErrorCode"),
                        event.get("particlePeakVelocityAxisZErrorCode"),
                        event.get("particlePeakVelocityAxisComposedErrorCode"),
                    ]

                    with open(CSV_FILE, mode="a", newline="") as file:
                        csv.writer(file).writerow(data_row)

                    print(
                        f"📡 Event diterima [{read_timestamp_wib}] "
                        f"Node {node_id} | Temp {temperature}°C | "
                        f"Durasi {event.get('eventDurationSeconds')}s"
                    )

    except Exception as e:
        print(f"[ERROR] Callback: {e}")


# Setup MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

print("🚀 Menghubungkan ke broker...")
client.connect(BROKER, PORT, 60)

client.loop_start()

try:
    print("🟢 Program berjalan...")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[INFO] Mematikan program...")
    client.loop_stop()
    client.disconnect()
    print("✅ Selesai.")
