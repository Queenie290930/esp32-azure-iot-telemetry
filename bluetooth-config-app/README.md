# Bluetooth Config App

Den här appen används för VG-delen. Den konfigurerar en ESP32-enhet i taget via Bluetooth LE.

## Starta

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

Appen söker efter ESP32-enheter som annonserar BLE-config service, läser nuvarande config och skickar ändringar när du väljer att synka.

Lösenord visas inte i klartext. Om du lämnar lösenordsfält tomma behåller ESP32 sitt gamla lösenord.

