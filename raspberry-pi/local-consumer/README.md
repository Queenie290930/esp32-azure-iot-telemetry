# Lokal MQTT-konsument

Den här appen visar telemetrin direkt från Mosquitto.

Den skickar ingenting till Azure. Den används för att visa att telemetrin går att läsa lokalt.

## Starta

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
python src/main.py
```

