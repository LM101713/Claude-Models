// Hardware configuration of the V10 display engine controller.
// Pin numbers are ESP32 GPIO numbers as printed on the ESP32-DevKitC-32E.
// See docs/ELECTRONICS.md for the wiring diagram and the full pin table.
#pragma once
#include <stdint.h>

#define FW_VERSION "1.0.0"

// --- TMC2209 stepper driver (BIGTREETECH TMC2209 V1.3, UART mode) ------------
constexpr uint8_t PIN_STEP = 26;
constexpr uint8_t PIN_DIR = 27;
constexpr uint8_t PIN_EN = 25;          // ENN, LOW = driver on (10k pull-up keeps it off at boot)
constexpr uint8_t PIN_TMC_TX = 22;      // -> 1k -> PDN_UART
constexpr uint8_t PIN_TMC_RX = 21;      // -> PDN_UART (single-wire UART)
constexpr uint8_t TMC_ADDRESS = 0;      // MS1 = MS2 = GND
constexpr float TMC_RSENSE = 0.11f;     // sense resistors on the BTT module
constexpr uint32_t TMC_BAUD = 115200;

// --- sensors and controls ------------------------------------------------------
constexpr uint8_t PIN_HALL = 33;        // DRV5033 (open drain, 10k pull-up): LOW = magnet
constexpr uint8_t PIN_POT = 32;         // 10k speed knob wiper (ADC1)
constexpr uint8_t PIN_BUTTON = 14;      // START button to GND
constexpr uint8_t PIN_BUTTON_LED = 13;  // START ring LED, via NPN (HIGH = on), PWM

// --- LED strips (via 74AHCT125 level shifter + 330R) -----------------------------
constexpr uint8_t PIN_LED_A = 18;       // bank A (cylinders 1-5)
constexpr uint8_t PIN_LED_B = 19;       // bank B (cylinders 6-10)

// --- ESP32 pulse counter unit that counts the STEP pulses (6 and 7 are free) ----
constexpr uint8_t STEP_PCNT_UNIT = 7;

// --- timing ------------------------------------------------------------------------
constexpr uint32_t LED_FRAME_MS = 5;          // 200 frames/s: 3.6 crank deg per frame at 120 RPM
constexpr uint32_t DRIVER_POLL_MS = 500;      // TMC2209 status check
constexpr uint32_t BUTTON_DEBOUNCE_MS = 30;
constexpr uint32_t LONG_PRESS_MS = 2000;
constexpr uint32_t SERVICE_HOLD_MS = 3000;    // hold START this long at power-on -> service mode
constexpr float KNOB_DEADBAND_RPM = 1.0f;     // ignore knob noise below this
constexpr float KNOB_INTERACTION_RPM = 3.0f;  // a knob move bigger than this counts as "someone is here"
constexpr float IDLE_BRIGHTNESS = 0.55f;      // LED dimming in idle mode
constexpr uint32_t NVS_SAVE_MS = 10UL * 60UL * 1000UL;   // run-hour counter save interval
