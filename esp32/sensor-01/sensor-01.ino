#include <ArduinoJson.h>
#include <DHT.h>
#include <PubSubClient.h>
#include <WiFi.h>

#include "ble_config.h"
#include "config.h"
#include "config_storage.h"
#include "device_config.h"
#include "network_mqtt.h"
#include "time_helper.h"

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
DHT dht(DHT_PIN, DHT_TYPE);
DeviceConfig config;

unsigned long lastPublishMs = 0;
unsigned long lastWifiAttemptMs = 0;
unsigned long lastMqttAttemptMs = 0;

const unsigned long publishIntervalMs = 10000;
const unsigned long wifiRetryIntervalMs = 15000;
const unsigned long mqttRetryIntervalMs = 5000;

float readSensorValue() {
  return dht.readTemperature();
}

void publishTelemetry() {
  if (!mqttClient.connected()) {
    return;
  }

  float value = readSensorValue();

  if (isnan(value)) {
    Serial.println("Sensor read failed. Skipping publish.");
    return;
  }

  StaticJsonDocument<256> doc;
  doc["deviceId"] = config.deviceId;
  doc["type"] = TELEMETRY_TYPE;
  doc["value"] = value;
  doc["unit"] = TELEMETRY_UNIT;
  doc["time"] = getCurrentTime();

  char payload[256];
  serializeJson(doc, payload);

  bool ok = mqttClient.publish(config.mqttTopic.c_str(), payload);

  if (ok) {
    Serial.print("Published to ");
    Serial.print(config.mqttTopic);
    Serial.print(": ");
    Serial.println(payload);
  } else {
    Serial.println("Publish failed.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("ESP32 sensor-01 started.");

  dht.begin();
  loadConfig(config);
  startBleConfig(config);

  if (connectToWifi(config)) {
    syncTime();
    connectToMqtt(mqttClient, config);
  }
}

void loop() {
  unsigned long now = millis();

  handleBleConfig();

  if (WiFi.status() != WL_CONNECTED && now - lastWifiAttemptMs >= wifiRetryIntervalMs) {
    lastWifiAttemptMs = now;
    connectToWifi(config);
  }

  if (WiFi.status() == WL_CONNECTED && !mqttClient.connected() && now - lastMqttAttemptMs >= mqttRetryIntervalMs) {
    lastMqttAttemptMs = now;
    connectToMqtt(mqttClient, config);
  }

  if (mqttClient.connected()) {
    mqttClient.loop();
  }

  if (now - lastPublishMs >= publishIntervalMs) {
    lastPublishMs = now;
    publishTelemetry();
  }
}
