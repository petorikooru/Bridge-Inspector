import paho.mqtt.client as mqtt
import json
import csv
import time
from datetime import datetime, timezone, timedelta

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "topic_loadsensing"
CSV_FILE = "filtered_sensor_log.csv"

# Inisialisasi Header CSV
with open(CSV_FILE, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(
        [
            "timestamp",
            "sensor_precision",
            "sensor_temperature",
            "x_std(vibration)",
            "x_eng",
            "y_std(vibration)",
            "y_eng",
            "z_std(vibration)",
            "z_eng",
            "laser_temperature",
            "laser_signal_strength",
            "laser_gain",
            "object_distance",
            "laser_eng_unit",
        ]
    )


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Terhubung ke broker!")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Gagal terhubung, kode: {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get("type") == "lastil90ReadingsV1":
            read_timestamp = payload.get("readTimestamp", "")
            parsed_utc = datetime.fromisoformat(read_timestamp.replace("Z", "+00:00"))
            wib_tz = timezone(timedelta(hours=7))
            read_timestamp = parsed_utc.astimezone(wib_tz).strftime("%Y-%m-%d %H:%M:%S")

            readings = payload.get("readings", [])

            # Ekstraksi Tiltmeter
            tilt_data = next(
                (r for r in readings if r.get("readingType") == "til90"), {}
            )
            tilt_chs = tilt_data.get("readings", [])
            ch = [tilt_chs[i] if len(tilt_chs) > i else {} for i in range(3)]

            # Ekstraksi Laser
            laser_data = next(
                (r for r in readings if r.get("readingType") == "laser"), {}
            )

            data_row = [
                read_timestamp,
                tilt_data.get("highPrecision"),
                tilt_data.get("temperature"),
                ch[0].get("std"),
                ch[0].get("engineeringValue"),
                ch[1].get("std"),
                ch[1].get("engineeringValue"),
                ch[2].get("std"),
                ch[2].get("engineeringValue"),
                laser_data.get("temperature"),
                laser_data.get("signalStrength"),
                laser_data.get("gain"),
                laser_data.get("engineeringValueY"),
                laser_data.get("engineeringUnit"),
            ]

            with open(CSV_FILE, mode="a", newline="") as file:
                csv.writer(file).writerow(data_row)

            print(
                f"📡 Data diterima: [{read_timestamp}] Laser: {laser_data.get('engineeringValueY')}m"
            )

    except Exception as e:
        print(f"[ERROR] Callback: {e}")


# Setup MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

print("🚀 Menghubungkan ke broker...")
client.connect(BROKER, PORT, 60)

# Menjalankan loop MQTT di background thread
client.loop_start()

try:
    print("🟢 Program berjalan. Melakukan looping setiap 1 detik...")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n[INFO] Mematikan program...")
    client.loop_stop()
    client.disconnect()
    print("✅ Selesai.")
