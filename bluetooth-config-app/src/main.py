import asyncio
import json

from bleak import BleakClient, BleakScanner


DEVICE_PROFILES = {
    "sensor-01": {
        "service": "7d2f4d90-7b9a-4f8b-8b43-3f1b7d000101",
        "read": "7d2f4d90-7b9a-4f8b-8b43-3f1b7d000102",
        "write": "7d2f4d90-7b9a-4f8b-8b43-3f1b7d000103",
    },
    "sensor-02": {
        "service": "7d2f4d90-7b9a-4f8b-8b43-3f1b7d000201",
        "read": "7d2f4d90-7b9a-4f8b-8b43-3f1b7d000202",
        "write": "7d2f4d90-7b9a-4f8b-8b43-3f1b7d000203",
    },
}


def prompt_keep(label: str, current: str = "") -> str:
    if current:
        value = input(f"{label} [{current}]: ").strip()
    else:
        value = input(f"{label}: ").strip()
    return value if value else current


def prompt_secret(label: str) -> str:
    return input(f"{label} [leave empty to keep current]: ").strip()


def format_bool(value: bool) -> str:
    return "configured" if value else "not configured"


def print_config(config: dict) -> None:
    print()
    print("Current ESP32 config")
    print("--------------------")
    print(f"SSID: {config.get('ssid', '')}")
    print(f"WiFi password: {format_bool(config.get('wifiPasswordConfigured', False))}")
    print(f"Device ID: {config.get('deviceId', '')}")
    print(f"MQTT host: {config.get('mqttHost', '')}")
    print(f"MQTT port: {config.get('mqttPort', '')}")
    print(f"MQTT topic: {config.get('mqttTopic', '')}")
    print(f"MQTT username: {config.get('mqttUsername', '')}")
    print(f"MQTT password: {format_bool(config.get('mqttPasswordConfigured', False))}")
    print()


def build_new_config(current: dict) -> dict:
    print("Enter new values. Press Enter to keep current value.")
    print()

    mqtt_port_current = str(current.get("mqttPort", 1883))
    mqtt_port_text = prompt_keep("MQTT port", mqtt_port_current)

    try:
        mqtt_port = int(mqtt_port_text)
    except ValueError:
        print("Invalid MQTT port. Keeping current port.")
        mqtt_port = int(mqtt_port_current)

    return {
        "ssid": prompt_keep("WiFi SSID", current.get("ssid", "")),
        "wifiPassword": prompt_secret("WiFi password"),
        "deviceId": prompt_keep("Device ID", current.get("deviceId", "sensor-01")),
        "mqttHost": prompt_keep("MQTT host", current.get("mqttHost", "172.20.10.3")),
        "mqttPort": mqtt_port,
        "mqttTopic": prompt_keep("MQTT topic", current.get("mqttTopic", "telemetry/sensor-01")),
        "mqttUsername": prompt_keep("MQTT username", current.get("mqttUsername", "")),
        "mqttPassword": prompt_secret("MQTT password"),
    }


async def find_config_devices():
    print("Scanning for ESP32 config devices...")
    devices = await BleakScanner.discover(timeout=8.0, return_adv=True)

    matches = []
    for device, advertisement in devices.values():
        service_uuids = [uuid.lower() for uuid in advertisement.service_uuids]
        name = device.name or advertisement.local_name or ""
        profile = profile_for_device(name, service_uuids)
        if profile is not None:
            matches.append((device, profile))

    return matches


def profile_for_device(name: str, service_uuids: list[str]):
    for profile_name, profile in DEVICE_PROFILES.items():
        if profile["service"] in service_uuids or profile_name in name:
            return profile_name
    return None


def choose_device(devices):
    print()
    print("Found devices")
    print("-------------")
    for index, (device, profile) in enumerate(devices, start=1):
        print(f"{index}. {device.name or 'Unnamed device'} ({device.address})")

    while True:
        choice = input("Choose device number: ").strip()
        try:
            index = int(choice)
            if 1 <= index <= len(devices):
                return devices[index - 1]
        except ValueError:
            pass
        print("Invalid choice.")


async def read_config(client: BleakClient, profile: dict) -> dict:
    raw = await client.read_gatt_char(profile["read"])
    text = raw.decode("utf-8")
    return json.loads(text)


async def write_config(client: BleakClient, profile: dict, config: dict) -> None:
    payload = json.dumps(config, separators=(",", ":")).encode("utf-8")
    await client.write_gatt_char(profile["write"], payload, response=True)


async def main():
    devices = await find_config_devices()

    if not devices:
        print("No ESP32 config devices found.")
        print("Make sure the ESP32 is powered on and running the VG sketch.")
        return

    device, profile_name = choose_device(devices)
    profile = DEVICE_PROFILES[profile_name]
    print(f"Connecting to {device.name or device.address}...")

    async with BleakClient(device) as client:
        current_config = await read_config(client, profile)
        print_config(current_config)

        new_config = build_new_config(current_config)

        print()
        print("New config to sync")
        print("------------------")
        preview = dict(new_config)
        preview["wifiPassword"] = "***" if preview["wifiPassword"] else "(keep current)"
        preview["mqttPassword"] = "***" if preview["mqttPassword"] else "(keep current)"
        print(json.dumps(preview, indent=2))

        confirm = input("Sync changes to ESP32? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return

        await write_config(client, profile, new_config)
        print("Config sent. ESP32 should save settings and restart.")


if __name__ == "__main__":
    asyncio.run(main())
