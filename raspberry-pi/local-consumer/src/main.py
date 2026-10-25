import json
import signal
import sys
from pathlib import Path

import paho.mqtt.client as mqtt


APP_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = APP_DIR / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CONFIG_PATH}. Copy config.example.json to config.json first."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def create_mqtt_client(client_id: str) -> mqtt.Client:
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except AttributeError:
        return mqtt.Client(client_id=client_id)


def mqtt_connect_succeeded(reason_code) -> bool:
    return reason_code == 0 or str(reason_code).lower() in ["0", "success"]


def main() -> int:
    config = load_config()
    mqtt_config = config["mqtt"]

    mqtt_client = create_mqtt_client("local-telemetry-consumer")

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if mqtt_connect_succeeded(reason_code):
            topic = mqtt_config["topic"]
            print(f"Connected to MQTT. Listening on {topic}")
            client.subscribe(topic)
        else:
            print(f"MQTT connection failed with code: {reason_code}")

    def on_message(client, userdata, msg):
        raw_payload = msg.payload.decode("utf-8")

        try:
            telemetry = json.loads(raw_payload)
        except json.JSONDecodeError:
            print(f"[{msg.topic}] invalid JSON: {raw_payload}")
            return

        device_id = telemetry.get("deviceId", "unknown-device")
        telemetry_type = telemetry.get("type", "value")
        value = telemetry.get("value", "?")
        unit = telemetry.get("unit", "")
        timestamp = telemetry.get("time", "unknown time")

        print(f"[local] {timestamp} {device_id} {telemetry_type} = {value} {unit}")

    def shutdown(signum, frame):
        print("\nStopping local consumer...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    username = mqtt_config.get("username", "")
    password = mqtt_config.get("password", "")
    if username:
        mqtt_client.username_pw_set(username, password)

    mqtt_client.connect(mqtt_config["host"], int(mqtt_config["port"]), keepalive=60)
    mqtt_client.loop_forever()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
