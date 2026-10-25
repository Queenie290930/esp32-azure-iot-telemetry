#pragma once

#include <PubSubClient.h>
#include "device_config.h"

bool connectToWifi(const DeviceConfig &config);
bool connectToMqtt(PubSubClient &mqttClient, const DeviceConfig &config);

