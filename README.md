# Wireless Telemetry with ESP32, MQTT and Azure IoT Hub

Two ESP32 devices measure temperature and humidity and send JSON over WiFi and MQTT to Mosquitto on a Raspberry Pi. A Python gateway forwards the telemetry to Azure IoT Hub. Consumer applications display the readings locally and from Azure. The devices are configured over Bluetooth LE.

```text
ESP32 → Mosquitto on Raspberry Pi → Python gateway → Azure IoT Hub
                  ↓                                      ↓
           Local consumer                         Azure consumer
```

## Project Structure

| Directory | Purpose |
|---|---|
| `esp32/sensor-01` | Temperature, topic `telemetry/sensor-01`, unit `C` |
| `esp32/sensor-02` | Humidity, topic `telemetry/sensor-02`, unit `%` |
| `raspberry-pi/gateway` | MQTT to Azure, runs on Raspberry Pi |
| `raspberry-pi/local-consumer` | Displays local MQTT telemetry |
| `raspberry-pi/azure-consumer` | Reads telemetry from Azure |
| `bluetooth-config-app` | Configures one ESP32 at a time over BLE |

Example telemetry:

```json
{"deviceId":"sensor-01","type":"temperature","value":22.5,"unit":"C","time":"13:35:26"}
```

## Raspberry Pi and MQTT

Install and start Mosquitto on the Pi:

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
```

The broker must accept connections from the ESP32 devices on port 1883. For a local test network, a file under `/etc/mosquitto/conf.d/` can contain:

```text
listener 1883
allow_anonymous true
```

Restart after the change with `sudo systemctl restart mosquitto`. Check incoming telemetry on the Pi:

```bash
mosquitto_sub -h localhost -t "telemetry/#" -v
```

## ESP32 and Bluetooth

Install `PubSubClient`, `ArduinoJson`, `DHT sensor library` and `Adafruit Unified Sensor` in Arduino IDE. Open each `.ino` file and upload it to the corresponding ESP32.

Copy `config.example.h` to `config.h` in each sensor directory. Adjust `DHT_PIN` and `DHT_TYPE` to match your wiring; the examples use a DHT11 on GPIO 4. Sensor 1 uses `temperature` and `C`; sensor 2 uses `humidity` and `%`. WiFi and MQTT are configured over BLE.

Start the Bluetooth application on your computer from the project root:

```bash
cd bluetooth-config-app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/main.py
```

Select `ESP32-sensor-01-config` or `ESP32-sensor-02-config`. Enter the SSID, WiFi password, unique deviceId, the Pi's MQTT address, port 1883, topic and MQTT credentials if required. Confirm synchronization to save the settings and restart the device. Empty password fields keep existing passwords; reading the settings only shows whether a password is configured.

## Python Applications

Open a separate terminal for each application and change to its directory under `raspberry-pi/`. If `config.json` does not exist, copy the directory's `config.example.json` to `config.json` and fill in:

- **local-consumer:** MQTT address, port and topic `telemetry/#`.
- **gateway:** MQTT settings and the connection string for a dedicated Azure IoT Hub device identity, such as `raspberrypi-gateway`.
- **azure-consumer:** The IoT Hub Event Hub-compatible connection string, consumer group and, if needed, Event Hub name.

Then run these commands in each application directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python src/main.py
```

Use `localhost` as the MQTT address when the application runs on the same Pi as Mosquitto; otherwise use the Pi's network address. Create the Python environment on each computer; do not copy `.venv` between Mac and Pi.

The gateway should display `Forwarded ... to Azure`. The consumers should display readings from both devices, preserving the deviceId, value and unit. Also check that BLE settings persist after disconnecting and reconnecting power.
