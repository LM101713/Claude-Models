// Hardware configuration of the Cup Lite display engine controller (docs/CUP_LITE.md).
// Board: Seeed Studio XIAO ESP32-C3. Pin numbers are ESP32-C3 GPIO numbers; the XIAO pad name is
// in the comment. GPIO 2, 8 and 9 are strapping pins and are left free.
#pragma once
#include <stdint.h>

#define FW_VERSION "cup-lite 0.1.0"

// --- DRV8833 dual H-bridge: motor A = crank pulley (front), motor B = flywheel (rear) --------
constexpr uint8_t PIN_AIN1 = 6;          // D4
constexpr uint8_t PIN_AIN2 = 7;          // D5
constexpr uint8_t PIN_BIN1 = 21;         // D6
constexpr uint8_t PIN_BIN2 = 20;         // D7
constexpr uint32_t MOTOR_PWM_HZ = 20000; // above hearing: no PWM whine from the N20s
constexpr uint8_t MOTOR_PWM_BITS = 10;

// --- WS2812B pixels, one 4-pixel chain per bank, via 74AHCT125 (3.3 V -> 5 V) + 330 R ------
constexpr uint8_t PIN_LED_A = 4;         // D2, bank A = right bank seen from the front = odd cylinders 1 3 5 7
constexpr uint8_t PIN_LED_B = 5;         // D3, bank B = left bank = even cylinders 2 4 6 8
constexpr uint8_t PIXELS_PER_BANK = 4;
// Pixel index along each chain -> cylinder slot from the front (0 = front). The chain enters each
// head at the deck hole near the rear (x = -40 mm) and the lead is run to the FRONT boot first,
// so index 0 is the front cylinder. Change this if a harness is built the other way round.
constexpr uint8_t CHAIN_TO_SLOT[PIXELS_PER_BANK] = {0, 1, 2, 3};

// --- controls -----------------------------------------------------------------------------
constexpr uint8_t PIN_BUTTON = 10;       // D10, momentary to GND, internal pull-up
constexpr uint8_t PIN_BUTTON_LED = 3;    // D1, ring LED via 2N3904 (HIGH = on)

// --- behaviour ----------------------------------------------------------------------------
constexpr uint32_t SHOW_MS = 2UL * 60UL * 1000UL;   // a short press runs a 2-minute show
constexpr uint32_t LONG_PRESS_MS = 1500;            // a long press toggles continuous running
constexpr uint32_t TEST_HOLD_MS = 3000;             // hold at power-on: LED and motor test
constexpr uint32_t DEBOUNCE_MS = 30;
constexpr uint32_t RAMP_MS = 2500;                  // soft start and soft stop
constexpr uint32_t FRAME_MS = 10;                   // 100 LED frames per second
// N20 speed: crank RPM at 100 % duty on 5 V. Measure one motor and set this; the firing LEDs
// follow it (open loop, there is no crank sensor and no visible piston to disagree with).
constexpr float RPM_AT_FULL = 45.0f;
constexpr float RUN_DUTY = 0.80f;                   // show speed, about 36 RPM
constexpr float MIN_DUTY = 0.25f;                   // below this an N20 may stall: ramp jumps past it
constexpr float IDLE_GLOW = 0.04f;                  // boots glow faintly when stopped (0 = off)
constexpr float LED_BRIGHTNESS = 0.85f;             // 8 pixels, well inside a 5 V 3 A supply
