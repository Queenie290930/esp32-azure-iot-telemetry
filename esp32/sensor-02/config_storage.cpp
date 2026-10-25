#include "config_storage.h"

void loadConfig(DeviceConfig &config) {
  Preferences preferences;
  preferences.begin("devicecfg", true);
  config.ssid = preferences.getString("ssid", "");
  config.wifiPassword = preferences.getString("wifiPass", "");
  config.deviceId = preferences.getString("deviceId", "sensor-02");
  config.mqttHost = preferences.getString("mqttHost", "172.20.10.3");
  config.mqttPort = preferences.getInt("mqttPort", 1883);
  config.mqttTopic = preferences.getString("mqttTopic", "telemetry/sensor-02");
  config.mqttUsername = preferences.getString("mqttUser", "");
  config.mqttPassword = preferences.getString("mqttPass", "");
  preferences.end();
}

void saveConfig(const DeviceConfig &config) {
  Preferences preferences;
  preferences.begin("devicecfg", false);
  preferences.putString("ssid", config.ssid);
  preferences.putString("wifiPass", config.wifiPassword);
  preferences.putString("deviceId", config.deviceId);
  preferences.putString("mqttHost", config.mqttHost);
  preferences.putInt("mqttPort", config.mqttPort);
  preferences.putString("mqttTopic", config.mqttTopic);
  preferences.putString("mqttUser", config.mqttUsername);
  preferences.putString("mqttPass", config.mqttPassword);
  preferences.end();
}

