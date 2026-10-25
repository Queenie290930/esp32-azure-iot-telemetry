# Azure-konsument

Den här appen läser device-to-cloud-meddelanden från Azure IoT Hub.

Azure IoT Hub exponerar inkommande telemetri via en Event Hub-compatible endpoint. Därför använder appen Python-paketet `azure-eventhub`.

## Starta

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
python src/main.py
```

Om din connection string redan innehåller `EntityPath` kan `eventHubName` vara tom.

