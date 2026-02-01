#include "ui_controller.h"
#include <math.h>

UIController::UIController(OscilloscopeEngine* engine, MeasurementEngine* meas)
    : tft(TFT_CS, TFT_DC, TFT_RST), oscilloscopeEngine(engine), measurementEngine(meas) {
    encoder = nullptr;
    lastEncoderPos = 0;
    uiMode = 0;
    selectedProfile = 0;
    buttonDownTime = 0;
    buttonPressed = false;
    nameEditBuffer[0] = '\0';
    nameEditIndex = 0;
    inNameEdit = false;
    nameLastBlinkTime = millis();
    nameBlinkOn = true;
    nameLastShortPressTime = 0;
    profileActionMode = false;
    profileActionSelected = 0;
}

void UIController::begin() {
    tft.begin();
    tft.setRotation(3);
    tft.fillScreen(ILI9341_BLACK);

    // Setup encoder and button
    encoder = new Encoder(ENCODER_A_PIN, ENCODER_B_PIN);
    lastEncoderPos = encoder->read();
    pinMode(ENCODER_BTN_PIN, INPUT_PULLUP);

    // Draw static elements once
    drawGrid();
    drawLabels();
}

void UIController::update() {
    // Only refresh the waveform area to reduce flicker and CPU load
    drawWaveform();

    // Name editor cursor blink handling
    if (uiMode == 4 && inNameEdit) {
        unsigned long now = millis();
        if (now - nameLastBlinkTime > 500) {
            nameLastBlinkTime = now;
            nameBlinkOn = !nameBlinkOn;
            // redraw only the name area
            tft.fillRect(5, 25, tft.width()-10, 20, ILI9341_BLACK);
            tft.setCursor(5, 25);
            for (int i = 0; i < PROFILE_NAME_LEN-1 && nameEditBuffer[i] != '\0'; i++) {
                if (i == nameEditIndex && nameBlinkOn) tft.setTextColor(ILI9341_YELLOW);
                else tft.setTextColor(ILI9341_WHITE);
                tft.print(nameEditBuffer[i]);
            }
        }
    }

    // Calibration wizard step-driven progress
    if (uiMode == 2 && wizardActive && measurementEngine) {
        // perform one step per update to avoid blocking
        bool done = measurementEngine->performCalibrationStep();
        int progress = measurementEngine->getCalibrationProgress();
        // Draw progress bar / percentage
        tft.fillRect(5, 70, tft.width()-10, 20, ILI9341_BLACK);
        tft.setTextColor(ILI9341_WHITE);
        tft.setCursor(5, 70);
        tft.print("Progress: "); tft.print(progress); tft.print(" %");
        // small bar
        int barW = map(progress, 0, 100, 0, tft.width()-20);
        tft.fillRect(5, 90, barW, 8, ILI9341_GREEN);
        if (done) {
            wizardActive = false;
            wizardLastResult = measurementEngine->getCalibrationFactor((VoltageRange)wizardRange);
            tft.fillRect(5, 70, tft.width()-10, 40, ILI9341_BLACK);
            tft.setCursor(5, 70);
            if (!isnan(wizardLastResult)) {
                tft.print("Calibration complete: factor="); tft.print(wizardLastResult, 6);
                tft.setCursor(5, 90);
                tft.print("Short press encoder to SAVE to profile. Long press to dismiss.");
            } else {
                tft.print("Calibration failed. Check reference.");
                tft.setCursor(5, 90);
                tft.print("Press any key to continue.");
            }
        }
    }
}


void UIController::drawGrid() {
    // Draw horizontal grid lines
    for (int i = 1; i < 4; i++) {
        tft.drawFastHLine(0, tft.height() * i / 4, tft.width(), ILI9341_DARKGREY);
    }
    // Draw vertical grid lines
    for (int i = 1; i < 4; i++) {
        tft.drawFastVLine(tft.width() * i / 4, 0, tft.height(), ILI9341_DARKGREY);
    }
}

void UIController::drawLabels() {
    tft.setTextColor(ILI9341_WHITE);
    tft.setTextSize(1);
    tft.setCursor(5, 5);
    tft.print("Time: 1ms/div");
    tft.setCursor(tft.width() - 60, 5);
    tft.print("V: 1V/div");
}

void UIController::showCalibrationScreen(float* factors, int count, float curFactor, float curOffset) {
    // Simple textual calibration display
    tft.fillScreen(ILI9341_BLACK);
    tft.setTextColor(ILI9341_WHITE);
    tft.setTextSize(1);
    int y = 5;
    tft.setCursor(5, y);
    tft.print("Calibration:"); y += 12;
    for (int i = 0; i < count && i < 5; i++) {
        tft.setCursor(5, y);
        tft.print("Range "); tft.print(i); tft.print(": "); tft.print(factors[i], 6);
        y += 10;
    }
    tft.setCursor(5, y); y += 12;
    tft.print("Cur offset (V): "); tft.print(curOffset, 6); y += 12;
    tft.setCursor(5, y);
    tft.print("Cur sens (V/A): "); tft.print(curFactor, 6);
}

void UIController::showCalibrationWizardStart(int range, float refVoltage) {
    // Start non-blocking calibration wizard
    uiMode = 2;
    wizardActive = true;
    wizardRange = range;
    wizardRefVoltage = refVoltage;
    wizardSamples = 50;
    wizardLastResult = NAN;

    tft.fillScreen(ILI9341_BLACK);
    tft.setTextColor(ILI9341_WHITE);
    tft.setTextSize(1);
    tft.setCursor(5, 5);
    tft.print("Calibration Wizard");
    tft.setCursor(5, 20);
    tft.print("Range: "); tft.print(range);
    tft.setCursor(5, 34);
    tft.print("Ref V: "); tft.print(refVoltage, 6);
    tft.setCursor(5, 50);
    tft.print("Starting... apply reference. Progress shown below.");

    if (measurementEngine) {
        measurementEngine->startRangeCalibration((VoltageRange)range, refVoltage, wizardSamples);
    }
}

void UIController::showProfileMenu() {
    uiMode = 1;
    tft.fillScreen(ILI9341_BLACK);
    tft.setTextSize(1);
    tft.setTextColor(ILI9341_WHITE);
    tft.setCursor(5, 5);
    tft.print("Profiles (short=load, long=save/name)");

    int y = 25;
    for (int i = 0; i < MAX_CAL_PROFILES; i++) {
        char name[PROFILE_NAME_LEN];
        if (measurementEngine->getProfileName(i, name, sizeof(name))) {
            if (i == selectedProfile) tft.setTextColor(ILI9341_YELLOW); else tft.setTextColor(ILI9341_WHITE);
            tft.setCursor(5, y);
            tft.print(i); tft.print(": "); tft.print(name);
        } else {
            if (i == selectedProfile) tft.setTextColor(ILI9341_YELLOW); else tft.setTextColor(ILI9341_WHITE);
            tft.setCursor(5, y);
            tft.print(i); tft.print(": <empty>");
        }
        y += 12;
    }
}

void UIController::enterProfileMenu() {
    selectedProfile = 0;
    profileActionMode = false;
    profileActionSelected = 0;
    showProfileMenu();
}

void UIController::exitProfileMenu() {
    uiMode = 0;
    profileActionMode = false;
    profileActionSelected = 0;
    tft.fillScreen(ILI9341_BLACK);
    drawGrid(); drawLabels();
}

void UIController::showProfileActionMenu() {
    uiMode = 1; // remain in profile context
    profileActionMode = true;
    tft.fillScreen(ILI9341_BLACK);
    tft.setTextSize(1);
    tft.setTextColor(ILI9341_WHITE);
    tft.setCursor(5, 5);
    tft.print("Profile Actions (short=select, long=confirm delete)");
    const char* actions[6] = {"Save/Overwrite","Rename","Delete","Export","Import","Cancel"};
    int y = 30;
    for (int i=0;i<6;i++) {
        if (i == profileActionSelected) tft.setTextColor(ILI9341_YELLOW); else tft.setTextColor(ILI9341_WHITE);
        tft.setCursor(5, y); tft.print(i); tft.print(": "); tft.print(actions[i]);
        y += 14;
    }
}



#include "integration_report.h"

void UIController::showSettingsMenu() {
    tft.fillScreen(ILI9341_BLACK);
    tft.setTextColor(ILI9341_WHITE);
    tft.setTextSize(1);
    tft.setCursor(5, 5);
    tft.print("Settings:");
    tft.setCursor(5, 20);
    tft.print("Post-anomaly samples: ");
    // Value will be drawn via serial/refresh - UI is primarily informational here
}

void UIController::showTestReport() {
    tft.fillScreen(ILI9341_BLACK);
    tft.setTextColor(ILI9341_WHITE);
    tft.setTextSize(1);
    tft.setCursor(5, 5);
    tft.print("Integration Test Report");
    tft.setCursor(5, 22);
    tft.print("Autorange: "); tft.print(lastIntegrationReport.autorangePassed ? "PASS" : "FAIL");
    tft.setCursor(5, 36);
    tft.print("Trigger: "); tft.print(lastIntegrationReport.triggerPassed ? "PASS" : "FAIL");
    tft.setCursor(5, 50);
    tft.print("Logging: "); tft.print(lastIntegrationReport.loggingPassed ? "PASS" : "FAIL");
    tft.setCursor(5, 64);
    tft.print("SD Export: "); tft.print(lastIntegrationReport.sdExportPassed ? "PASS" : "SKIP/FAIL");
    tft.setCursor(5, 84);
    tft.print("Summary:");
    tft.setCursor(5, 98);
    tft.print(lastIntegrationReport.summary);
}

void UIController::showOverload(bool state) {
    // Simple visual indicator at top-right of the screen
    if (state) {
        tft.fillRect(tft.width()-60, 0, 60, 16, ILI9341_RED);
        tft.setTextColor(ILI9341_WHITE);
        tft.setCursor(tft.width()-58, 2);
        tft.setTextSize(1);
        tft.print("OVERLOAD");
    } else {
        // Clear area
        tft.fillRect(tft.width()-60, 0, 60, 16, ILI9341_BLACK);
        // redraw labels that may have been overwritten
        drawLabels();
    }
}

void UIController::enterIntegrationMenu() {
    uiMode = 3;
    tft.fillScreen(ILI9341_BLACK);
    tft.setTextSize(1);
    tft.setTextColor(ILI9341_WHITE);
    tft.setCursor(5, 5);
    tft.print("Integration Test (short=run, long=run+stream)");
    tft.setCursor(5, 30);
    tft.print("Last: "); tft.print(lastIntegrationReport.summary);
}

void UIController::exitIntegrationMenu() {
    uiMode = 0;
    tft.fillScreen(ILI9341_BLACK);
    drawGrid(); drawLabels();
}

void UIController::handleEncoder() {
    if (!encoder) return;
    long pos = encoder->read();
    long delta = pos - lastEncoderPos;
    if (delta != 0) {
        lastEncoderPos = pos;
        if (uiMode == 1 && !profileActionMode) {
            // profile menu navigation
            selectedProfile = (selectedProfile + (int)delta) % MAX_CAL_PROFILES;
            if (selectedProfile < 0) selectedProfile += MAX_CAL_PROFILES;
            showProfileMenu();
        } else if (uiMode == 1 && profileActionMode) {
            // action menu navigation
            profileActionSelected = (profileActionSelected + (int)delta) % 6;
            if (profileActionSelected < 0) profileActionSelected += 6;
            showProfileActionMenu();
        } else if (uiMode == 3) {
            // Integration menu navigation (simple single option for now)
            // could expand later
        } else if (uiMode == 4 && inNameEdit) {
            // name edit mode: rotate char at current edit position
            int idx = nameEditIndex;
            if (idx < 0 || idx >= PROFILE_NAME_LEN-1) idx = 0;
            char c = nameEditBuffer[idx];
            if (c == '\0') c = 'A';
            // change by one step in ASCII per encoder step sign
            if (delta > 0) c++; else c--;
            if (c < 32) c = 32; if (c > 126) c = 126;
            nameEditBuffer[idx] = c;
            // redraw name with highlighted current char
            tft.fillRect(5, 25, tft.width()-10, 20, ILI9341_BLACK);
            tft.setCursor(5, 25);
            for (int i = 0; i < PROFILE_NAME_LEN-1 && nameEditBuffer[i] != '\0'; i++) {
                if (i == nameEditIndex) tft.setTextColor(ILI9341_YELLOW);
                else tft.setTextColor(ILI9341_WHITE);
                tft.print(nameEditBuffer[i]);
            }
        }
    }

    // Button handling
    int btn = digitalRead(ENCODER_BTN_PIN);
    if (btn == LOW && !buttonPressed) {
        buttonPressed = true;
        buttonDownTime = millis();
    } else if (btn == HIGH && buttonPressed) {
        unsigned long dt = millis() - buttonDownTime;
        buttonPressed = false;
        if (dt < 800) {
            // short press -> select/load or action
            if (uiMode == 1 && !profileActionMode) {
                // Load profile
                char name[PROFILE_NAME_LEN];
                if (measurementEngine->getProfileName(selectedProfile, name, sizeof(name))) {
                    measurementEngine->loadProfile(selectedProfile);
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5);
                    tft.print("Loaded profile: "); tft.print(name);
                    Serial.print("[UI] Loaded profile: "); Serial.println(name);
                } else {
                    // empty slot -> instruct user to long-press to save current calibration with name
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5);
                    tft.print("Empty slot. Long-press to save current calibration (then enter name)");
                }
            } else if (uiMode == 1 && profileActionMode) {
                // Execute selected action (short press = choose / execute)
                if (profileActionSelected == 0) {
                    // Save/Overwrite -> enter name editor prefilled
                    uiMode = 4; inNameEdit = true;
                    if (!measurementEngine->getProfileName(selectedProfile, nameEditBuffer, sizeof(nameEditBuffer))) {
                        snprintf(nameEditBuffer, sizeof(nameEditBuffer), "P%d", selectedProfile+1);
                    }
                    nameEditIndex = 0;
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5); tft.print("Enter profile name:");
                    tft.setCursor(5, 25); tft.print(nameEditBuffer);
                } else if (profileActionSelected == 1) {
                    // Rename -> prefill and enter name editor
                    if (measurementEngine->getProfileName(selectedProfile, nameEditBuffer, sizeof(nameEditBuffer))) {
                        uiMode = 4; inNameEdit = true; nameEditIndex = 0;
                        tft.fillScreen(ILI9341_BLACK);
                        tft.setCursor(5, 5); tft.print("Rename profile:");
                        tft.setCursor(5, 25); tft.print(nameEditBuffer);
                    } else {
                        tft.fillScreen(ILI9341_BLACK);
                        tft.setCursor(5, 5); tft.print("No profile to rename");
                        delay(800);
                        showProfileMenu();
                    }
                } else if (profileActionSelected == 2) {
                    // Delete -> require a long press to confirm; show prompt
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5); tft.print("Long-press to CONFIRM DELETE");
                } else if (profileActionSelected == 3) {
                    // Export
                    char fname[32]; snprintf(fname, sizeof(fname), "profile_%d.csv", selectedProfile);
                    bool ok = measurementEngine->exportProfileToSD(selectedProfile, fname);
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5);
                    if (ok) tft.print("Exported to "), tft.print(fname);
                    else tft.print("Export failed");
                    delay(900);
                    showProfileMenu();
                } else if (profileActionSelected == 4) {
                    // Import
                    char fname[32]; snprintf(fname, sizeof(fname), "profile_%d.csv", selectedProfile);
                    bool ok = measurementEngine->importProfileFromSD(selectedProfile, fname);
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5);
                    if (ok) tft.print("Imported from "), tft.print(fname);
                    else tft.print("Import failed");
                    delay(900);
                    showProfileMenu();
                } else {
                    // Cancel
                    profileActionMode = false; profileActionSelected = 0; showProfileMenu();
                }
            } else if (uiMode == 3) {
                // Run integration test (short press)
                Serial.println("[UI] Running integration test (no CSV)");
                runIntegrationTest(false);
                tft.fillScreen(ILI9341_BLACK);
                showTestReport();
            } else if (uiMode == 2) {
                // In wizard mode, short press: if calibration finished offer to save
                if (!wizardActive && !isnan(wizardLastResult)) {
                    // Enter name editor prefilled
                    uiMode = 4; inNameEdit = true; nameEditIndex = 0;
                    snprintf(nameEditBuffer, sizeof(nameEditBuffer), "WZ_%d", wizardRange);
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5); tft.print("Save wizard result to profile:");
                    tft.setCursor(5, 25); tft.print(nameEditBuffer);
                } else {
                    Serial.println("[WIZ] Short-press ignored while wizard is running");
                }
            } else if (uiMode == 4 && inNameEdit) {
                // In name edit mode, short press moves cursor to next character or deletes on double-press
                unsigned long now = millis();
                if (now - nameLastShortPressTime < 400) {
                    // double short-press within 400ms -> delete previous char
                    if (nameEditIndex > 0) {
                        // shift left
                        int i = nameEditIndex - 1;
                        for (; i < PROFILE_NAME_LEN-2; i++) nameEditBuffer[i] = nameEditBuffer[i+1];
                        nameEditBuffer[PROFILE_NAME_LEN-2] = '\0';
                        if (nameEditIndex > 0) nameEditIndex--;
                    }
                } else {
                    nameEditIndex = (nameEditIndex + 1) % (PROFILE_NAME_LEN - 1);
                    if (nameEditBuffer[nameEditIndex] == '\0') nameEditBuffer[nameEditIndex] = 'A';
                }
                nameLastShortPressTime = now;
                // redraw name with highlight
                tft.fillRect(5, 25, tft.width()-10, 20, ILI9341_BLACK);
                tft.setCursor(5, 25);
                for (int i = 0; i < PROFILE_NAME_LEN-1 && nameEditBuffer[i] != '\0'; i++) {
                    if (i == nameEditIndex) tft.setTextColor(ILI9341_YELLOW);
                    else tft.setTextColor(ILI9341_WHITE);
                    tft.print(nameEditBuffer[i]);
                }
                Serial.println("[UI] Name cursor moved");
            }
        } else {
            // long press -> save current to profile or advanced action
            if (uiMode == 1 && !profileActionMode) {
                // if slot is occupied, show action menu; else enter name edit mode for saving
                char tmp[PROFILE_NAME_LEN];
                if (measurementEngine->getProfileName(selectedProfile, tmp, sizeof(tmp))) {
                    profileActionMode = true; profileActionSelected = 0; showProfileActionMenu();
                } else {
                    // empty slot -> direct name editor
                    uiMode = 4; // name edit mode
                    snprintf(nameEditBuffer, sizeof(nameEditBuffer), "P%d", selectedProfile+1);
                    nameEditIndex = 0;
                    inNameEdit = true;
                    // Show edit UI
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5);
                    tft.print("Enter profile name:");
                    tft.setCursor(5, 25);
                    tft.print(nameEditBuffer);
                    Serial.println("[UI] Entering name edit mode; rotate encoder to modify chars then short-press to save, long-press to cancel");
                }
            } else if (uiMode == 3) {
                // Integration menu long press: run and stream CSV
                Serial.println("[UI] Running integration test with CSV streaming");
                runIntegrationTest(true);
                tft.fillScreen(ILI9341_BLACK);
                showTestReport();
            } else if (uiMode == 4 && inNameEdit) {
                // Save profile with the edited name
                bool ok = measurementEngine->saveProfile(selectedProfile, nameEditBuffer);
                tft.fillScreen(ILI9341_BLACK);
                tft.setCursor(5, 5);
                if (ok) {
                    tft.print("Saved profile: "); tft.print(nameEditBuffer);
                    Serial.print("[UI] Saved profile: "); Serial.println(nameEditBuffer);
                } else {
                    tft.print("Save failed");
                    Serial.println("[UI] Save failed");
                }
                inNameEdit = false;
                uiMode = 1;
                showProfileMenu();
            } else if (uiMode == 1 && profileActionMode) {
                // In action mode, long-press confirms Delete when Delete is selected
                if (profileActionSelected == 2) {
                    bool ok = measurementEngine->deleteProfile(selectedProfile);
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5);
                    if (ok) tft.print("Profile deleted"); else tft.print("Delete failed");
                    delay(700);
                    profileActionMode = false; profileActionSelected = 0; showProfileMenu();
                } else {
                    // other actions don't require long-press confirm here
                    profileActionMode = false; profileActionSelected = 0; showProfileMenu();
                }
            } else if (uiMode == 2) {
                // Long-press in wizard mode: cancel if running or dismiss result
                if (wizardActive) {
                    measurementEngine->cancelRangeCalibration();
                    wizardActive = false;
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5);
                    tft.print("Calibration cancelled");
                    delay(700);
                    showProfileMenu();
                } else {
                    // Dismiss wizard result
                    wizardLastResult = NAN;
                    tft.fillScreen(ILI9341_BLACK);
                    tft.setCursor(5, 5);
                    tft.print("Wizard dismissed");
                    delay(600);
                    showProfileMenu();
                }
            }
        }
    }
}

void UIController::handleTouch() {
    // Basic touch handling could be implemented here; left as future work
}

void UIController::drawWaveform() {
    int count = 0;
    int startIndex = 0;
    WaveformSample* data = oscilloscopeEngine->getWaveformData(count, startIndex);
    int bufferSize = oscilloscopeEngine->getBufferSize();

    if (data == nullptr || count <= 1 || bufferSize <= 0) {
        return;
    }

    // Clear only the waveform area to reduce flicker
    int top = tft.height() / 6;
    int height = tft.height() * 4 / 6;
    tft.fillRect(0, top, tft.width(), height, ILI9341_BLACK);

    // Find min/max for scaling
    float minV = data[startIndex % bufferSize].value;
    float maxV = minV;
    for (int i = 0; i < count; i++) {
        int idx = (startIndex + i) % bufferSize;
        float v = data[idx].value;
        if (v < minV) minV = v;
        if (v > maxV) maxV = v;
    }

    if (fabs(maxV - minV) < 1e-6f) {
        maxV = minV + 0.001f; // avoid division by zero
    }

    // Compute simple measurements: Vpp and RMS on displayed window
    float sumSq = 0.0f;
    for (int i = 0; i < count; i++) {
        int idx = (startIndex + i) % bufferSize;
        float v = data[idx].value;
        sumSq += v * v;
    }
    float rms = sqrt(sumSq / (float)count);
    float vpp = maxV - minV;
    // Draw overlays
    tft.setTextColor(ILI9341_WHITE);
    tft.setTextSize(1);
    tft.setCursor(5, tft.height() - 20);
    tft.print("Vpp:"); tft.print(vpp, 3);
    tft.setCursor(60, tft.height() - 20);
    tft.print("RMS:"); tft.print(rms, 3);

    // Decimate/aggregate per-pixel using min/max to preserve peaks while reducing draw ops
    int w = tft.width();
    for (int x = 0; x < w; x++) {
        int startSample = (x * count) / w;
        int endSample = ((x + 1) * count) / w;
        if (endSample <= startSample) endSample = startSample + 1;
        float minVx = 1e30f, maxVx = -1e30f;
        for (int s = startSample; s < endSample; s++) {
            int idx = (startIndex + s) % bufferSize;
            float v = data[idx].value;
            if (v < minVx) minVx = v;
            if (v > maxVx) maxVx = v;
        }
        if (minVx > maxVx) continue;
        int y1 = top + (int)((1.0f - (minVx - minV) / (maxV - minV)) * (float)height);
        int y2 = top + (int)((1.0f - (maxVx - minV) / (maxV - minV)) * (float)height);
        if (y1 == y2) tft.drawPixel(x, y1, ILI9341_YELLOW);
        else tft.drawFastVLine(x, y2, y1 - y2 + 1, ILI9341_YELLOW);
    }
}