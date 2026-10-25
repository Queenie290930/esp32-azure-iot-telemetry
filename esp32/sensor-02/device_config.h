#pragma once

#include <Arduino.h>

struct DeviceConfig {
  String ssid;
  String wifiPassword;
  String deviceId;
  String mqttHost;
  int mqttPort;
  String mqttTopic;
  String mqttUsername;
  String mqttPassword;
};

