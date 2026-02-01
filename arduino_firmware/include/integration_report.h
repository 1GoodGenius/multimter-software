#ifndef INTEGRATION_REPORT_H
#define INTEGRATION_REPORT_H

#include <Arduino.h>

struct IntegrationReport {
  bool autorangePassed;
  bool triggerPassed;
  bool loggingPassed;
  bool sdExportPassed;
  char summary[128];
};

extern IntegrationReport lastIntegrationReport;

void runIntegrationTest(bool streamCSV = false);

#endif // INTEGRATION_REPORT_H