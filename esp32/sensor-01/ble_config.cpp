#include <ArduinoJson.h>
#include <BLE2902.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

#include "ble_config.h"
#include "config_storage.h"

#define CONFIG_SERVICE_UUID "7d2f4d90-7b9a-4f8b-8b43-3f1b7d000101"
#define CONFIG_READ_UUID "7d2f4d90-7b9a-4f8b-8b43-3f1b7d000102"
#define CONFIG_WRITE_UUID "7d2f4d90-7b9a-4f8b-8b43-3f1b7d000103"

static DeviceConfig *activeConfig = nullptr;
static BLECharacteristic *readCharacteristic = nullptr;
static bool restartRequested = false;
static unsigned long restartAtMs = 0;

String configForRead(const DeviceConfig &config) {
  StaticJsonDocument<384> doc;
  doc["ssid"] = config.ssid;
  doc["wifiPasswordConfigured"] = config.wifiPassword.length() > 0;
  doc["deviceId"] = config.deviceId;
  doc["mqttHost"] = config.mqttHost;
  doc["mqttPort"] = config.mqttPort;
  doc["mqttTopic"] = config.mqttTopic;
  doc["mqttUsername"] = config.mqttUsername;
  doc["mqttPasswordConfigured"] = config.mqttPassword.length() > 0;

  String json;
  serializeJson(doc, json);
  return json;
}

void updateReadCharacteristic() {
  if (readCharacteristic != nullptr && activeConfig != nullptr) {
    readCharacteristic->setValue(configForRead(*activeConfig).c_str());
  }
}

void applyConfigJson(String json) {
  if (activeConfig == nullptr) {
    return;
  }

  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, json);

  if (error) {
    Serial.print("BLE config JSON error: ");
    Serial.println(error.c_str());
    return;
  }

  if (doc["ssid"].is<const char *>()) {
    activeConfig->ssid = doc["ssid"].as<String>();
  }
  if (doc["wifiPassword"].is<const char *>() && strlen(doc["wifiPassword"]) > 0) {
    activeConfig->wifiPassword = doc["wifiPassword"].as<String>();
  }
  if (doc["deviceId"].is<const char *>()) {
    activeConfig->deviceId = doc["deviceId"].as<String>();
  }
  if (doc["mqttHost"].is<const char *>()) {
    activeConfig->mqttHost = doc["mqttHost"].as<String>();
  }
  if (doc["mqttPort"].is<int>()) {
    activeConfig->mqttPort = doc["mqttPort"].as<int>();
  }
  if (doc["mqttTopic"].is<const char *>()) {
    activeConfig->mqttTopic = doc["mqttTopic"].as<String>();
  }
  if (doc["mqttUsername"].is<const char *>()) {
    activeConfig->mqttUsername = doc["mqttUsername"].as<String>();
  }
  if (doc["mqttPassword"].is<const char *>() && strlen(doc["mqttPassword"]) > 0) {
    activeConfig->mqttPassword = doc["mqttPassword"].as<String>();
  }

  saveConfig(*activeConfig);
  updateReadCharacteristic();

  Serial.println("BLE config saved. Restarting soon...");
  restartRequested = true;
  restartAtMs = millis() + 3000;
}

class ConfigWriteCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *characteristic) {
    String value = characteristic->getValue();
    if (value.length() == 0) {
      return;
    }

    Serial.print("BLE write received: ");
    Serial.println(value);
    applyConfigJson(value);
  }
};

void startBleConfig(DeviceConfig &config) {
  activeConfig = &config;

  BLEDevice::init("ESP32-sensor-01-config");
  BLEServer *server = BLEDevice::createServer();
  BLEService *service = server->createService(CONFIG_SERVICE_UUID);

  readCharacteristic = service->createCharacteristic(
    CONFIG_READ_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );

  BLECharacteristic *writeCharacteristic = service->createCharacteristic(
    CONFIG_WRITE_UUID,
    BLECharacteristic::PROPERTY_WRITE
  );

  writeCharacteristic->setCallbacks(new ConfigWriteCallbacks());
  readCharacteristic->addDescriptor(new BLE2902());
  updateReadCharacteristic();

  service->start();

  BLEAdvertising *advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID(CONFIG_SERVICE_UUID);
  advertising->setScanResponse(true);
  BLEDevice::startAdvertising();

  Serial.println("BLE config service started as ESP32-sensor-01-config.");
}

void handleBleConfig() {
  if (restartRequested && millis() >= restartAtMs) {
    Serial.println("Restarting after BLE config sync.");
    delay(200);
    ESP.restart();
  }
}
