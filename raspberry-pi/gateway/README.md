# Gateway

Gatewayen körs på Raspberry Pi.

Den gör tre saker:

1. Prenumererar på MQTT-topic `telemetry/#`.
2. Tar emot JSON från båda ESP32-enheterna.
3. Skickar samma JSON vidare till Azure IoT Hub.

## Starta

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
python src/main.py
```

`config.json` ska innehålla den riktiga Azure connection string för gatewayens device identity.

