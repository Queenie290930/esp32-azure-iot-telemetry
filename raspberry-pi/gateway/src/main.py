import json
import signal
import sys
from pathlib import Path

import paho.mqtt.client as mqtt
from azure.iot.device import IoTHubDeviceClient, Message


APP_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = APP_DIR / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CONFIG_PATH}. Copy config.example.json to config.json first."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_telemetry(payload: dict) -> None:
    required_fields = ["deviceId", "value", "unit"]
    missing_fields = [field for field in required_fields if field not in payload]

    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


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
    azure_config = config["azure"]

    azure_client = IoTHubDeviceClient.create_from_connection_string(
        azure_config["connectionString"]
    )
    azure_client.connect()
    print("Connected to Azure IoT Hub.")

    mqtt_client = create_mqtt_client("raspberrypi-gateway")

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if mqtt_connect_succeeded(reason_code):
            topic = mqtt_config["topic"]
            print(f"Connected to MQTT. Subscribing to {topic}")
            client.subscribe(topic)
        else:
            print(f"MQTT connection failed with code: {reason_code}")

    def on_message(client, userdata, msg):
        raw_payload = msg.payload.decode("utf-8")

        try:
            telemetry = json.loads(raw_payload)
            validate_telemetry(telemetry)
        except Exception as error:
            print(f"Ignoring invalid MQTT message on {msg.topic}: {error}")
            return

        azure_message = Message(json.dumps(telemetry))
        azure_message.content_encoding = "utf-8"
        azure_message.content_type = "application/json"
        azure_message.custom_properties["mqttTopic"] = msg.topic
        azure_message.custom_properties["source"] = "local-mqtt"

        azure_client.send_message(azure_message)

        device_id = telemetry["deviceId"]
        value = telemetry["value"]
        unit = telemetry["unit"]
        telemetry_type = telemetry.get("type", "value")
        timestamp = telemetry.get("time", "unknown time")

        print(
            f"Forwarded {timestamp} {device_id}: {telemetry_type}={value} {unit} "
            f"from MQTT topic {msg.topic} to Azure"
        )

    def shutdown(signum, frame):
        print("\nStopping gateway...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        azure_client.disconnect()
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
