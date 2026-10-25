#include <WiFi.h>
#include "network_mqtt.h"

bool connectToWifi(const DeviceConfig &config) {
  if (config.ssid.length() == 0) {
    Serial.println("No WiFi SSID configured. Use BLE config app.");
    return false;
  }

  Serial.print("Connecting to WiFi: ");
  Serial.println(config.ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(config.ssid.c_str(), config.wifiPassword.c_str());

  unsigned long startedAt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startedAt < 20000) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi connected.");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    return true;
  }

  Serial.println("WiFi connection failed. Use BLE config app if settings changed.");
  return false;
}

bool connectToMqtt(PubSubClient &mqttClient, const DeviceConfig &config) {
  if (WiFi.status() != WL_CONNECTED) {
    return false;
  }

  mqttClient.setServer(config.mqttHost.c_str(), config.mqttPort);

  Serial.print("Connecting to MQTT broker: ");
  Serial.println(config.mqttHost);

  bool connected;
  if (config.mqttUsername.length() > 0) {
    connected = mqttClient.connect(
      config.deviceId.c_str(),
      config.mqttUsername.c_str(),
      config.mqttPassword.c_str()
    );
  } else {
    connected = mqttClient.connect(config.deviceId.c_str());
  }

  if (connected) {
    Serial.println("MQTT connected.");
  } else {
    Serial.print("MQTT failed. State: ");
    Serial.println(mqttClient.state());
  }

  return connected;
}

