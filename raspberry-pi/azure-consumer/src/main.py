import json
import signal
import sys
from pathlib import Path

from azure.eventhub import EventHubConsumerClient


APP_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = APP_DIR / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Missing {CONFIG_PATH}. Copy config.example.json to config.json first."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def format_event_body(event) -> str:
    body_parts = []
    for body_part in event.body:
        if isinstance(body_part, bytes):
            body_parts.append(body_part.decode("utf-8"))
        else:
            body_parts.append(str(body_part))

    return "".join(body_parts)


def main() -> int:
    config = load_config()
    eventhub_config = config["eventHub"]

    connection_string = eventhub_config["connectionString"]
    consumer_group = eventhub_config.get("consumerGroup", "$Default")
    eventhub_name = eventhub_config.get("eventHubName", "")

    kwargs = {
        "conn_str": connection_string,
        "consumer_group": consumer_group,
    }
    if eventhub_name:
        kwargs["eventhub_name"] = eventhub_name

    client = EventHubConsumerClient.from_connection_string(**kwargs)

    def on_event(partition_context, event):
        raw_payload = format_event_body(event)

        try:
            telemetry = json.loads(raw_payload)
        except json.JSONDecodeError:
            print(f"[azure] invalid JSON: {raw_payload}")
            partition_context.update_checkpoint(event)
            return

        device_id = telemetry.get("deviceId", "unknown-device")
        telemetry_type = telemetry.get("type", "value")
        value = telemetry.get("value", "?")
        unit = telemetry.get("unit", "")
        timestamp = telemetry.get("time", "unknown time")

        print(f"[azure] {timestamp} {device_id} {telemetry_type} = {value} {unit}")
        partition_context.update_checkpoint(event)

    def shutdown(signum, frame):
        print("\nStopping Azure consumer...")
        client.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("Listening for Azure IoT Hub telemetry...")
    with client:
        client.receive(
            on_event=on_event,
            starting_position="-1",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
