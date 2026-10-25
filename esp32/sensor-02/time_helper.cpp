#include <time.h>
#include "time_helper.h"

const char *timezone = "CET-1CEST,M3.5.0/2,M10.5.0/3";

void syncTime() {
  configTzTime(timezone, "pool.ntp.org", "time.nist.gov");

  struct tm timeInfo;
  if (getLocalTime(&timeInfo, 10000)) {
    Serial.println("Time synchronized.");
  } else {
    Serial.println("Time sync failed.");
  }
}

String getCurrentTime() {
  struct tm timeInfo;
  if (!getLocalTime(&timeInfo, 1000)) {
    return "unknown";
  }

  char timeString[9];
  strftime(timeString, sizeof(timeString), "%H:%M:%S", &timeInfo);
  return String(timeString);
}

