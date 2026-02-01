#ifndef UI_CONTROLLER_H
#define UI_CONTROLLER_H

#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <SPI.h>
#include "oscilloscope_engine.h"

// Define pins for the ILI9341 display
#define TFT_DC 9
#define TFT_CS 10
#define TFT_RST 8

class UIController {
public:
    UIController(OscilloscopeEngine* engine, MeasurementEngine* meas = nullptr);
    void begin();
    void update();

    // New UI features
    void showCalibrationScreen(float* factors, int count, float curFactor, float curOffset);
    void showCalibrationWizardStart(int range, float refVoltage);

    // Wizard state
    bool wizardActive;
    int wizardRange;
    float wizardRefVoltage;
    int wizardSamples;
    float wizardLastResult;
    void showSettingsMenu();
    void enterProfileMenu();
    void exitProfileMenu();
    void showTestReport();
    void enterIntegrationMenu();
    void exitIntegrationMenu();

    // Safety/warning displays
    void showOverload(bool state);

    // Input handling
    void handleEncoder();
    void handleTouch();

private:
    void drawGrid();
    void drawLabels();
    void drawWaveform();
    void showProfileMenu();

    Adafruit_ILI9341 tft;
    OscilloscopeEngine* oscilloscopeEngine;
    MeasurementEngine* measurementEngine;

    // Encoder/button state
    Encoder* encoder;
    long lastEncoderPos;
    int uiMode; // 0=normal,1=profile menu,2=wizard,3=integration menu,4=name edit
    int selectedProfile;
    unsigned long buttonDownTime;
    bool buttonPressed;

    // Name editing state for profile save
    char nameEditBuffer[PROFILE_NAME_LEN];
    int nameEditIndex;
    bool inNameEdit;

    // Name edit blink and interaction helpers
    unsigned long nameLastBlinkTime;
    bool nameBlinkOn;
    unsigned long nameLastShortPressTime; // for double-short-press patterns

    // Profile action submenu state
    bool profileActionMode;
    int profileActionSelected; // 0=Save/Overwrite,1=Rename,2=Delete,3=Export,4=Import,5=Cancel

    void showProfileActionMenu();
    void showNameEditor();
};

#endif // UI_CONTROLLER_H