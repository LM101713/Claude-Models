// Cup Lite display engine controller (Seeed XIAO ESP32-C3, Arduino-ESP32 2.0.x).
//
// Two N20 gear motors on a DRV8833 turn the crank pulley and the flywheel; eight WS2812B pixels
// inside the heads flash the plug boots in firing order at the speed the crank is turning.
// One button: short press = 2-minute show (press again to stop), long press = run continuously.
// Hold the button while plugging in = test (each boot in firing order, then both motors 3 s).
// See docs/CUP_LITE.md for the wiring.
#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

#include "config.h"
#include "cup_logic.h"

using namespace cup;

static Adafruit_NeoPixel bankA(PIXELS_PER_BANK, PIN_LED_A, NEO_GRB + NEO_KHZ800);
static Adafruit_NeoPixel bankB(PIXELS_PER_BANK, PIN_LED_B, NEO_GRB + NEO_KHZ800);
static Adafruit_NeoPixel* banks[2] = {&bankA, &bankB};

// LEDC channels: 0/1 = motor A IN1/IN2, 2/3 = motor B IN1/IN2, 4 = button ring LED
static void pwmInit() {
  const uint8_t pins[4] = {PIN_AIN1, PIN_AIN2, PIN_BIN1, PIN_BIN2};
  for (uint8_t ch = 0; ch < 4; ch++) {
    ledcSetup(ch, MOTOR_PWM_HZ, MOTOR_PWM_BITS);
    ledcAttachPin(pins[ch], ch);
    ledcWrite(ch, 0);
  }
  ledcSetup(4, 1000, 8);
  ledcAttachPin(PIN_BUTTON_LED, 4);
}

// DRV8833 "slow decay" forward drive: IN1 = PWM, IN2 = low. Both motors turn the same way as
// seen from their own output end; if one turns backwards, swap its two motor leads.
static void setMotors(float duty) {
  const uint32_t top = (1u << MOTOR_PWM_BITS) - 1;
  uint32_t v = (uint32_t)(duty * top + 0.5f);
  ledcWrite(0, v);
  ledcWrite(1, 0);
  ledcWrite(2, v);
  ledcWrite(3, 0);
}

static void showBoots(float crankDeg, float rpm, float glow) {
  for (uint8_t cyl = 1; cyl <= N_CYL; cyl++) {
    float lvl = rpm > 0.5f ? cylinderLevel(cyl, crankDeg, rpm) : 0.0f;
    if (lvl < glow) lvl = glow;
    Rgb c = sparkColour(lvl, LED_BRIGHTNESS);
    uint8_t slot = slotOf(cyl);
    for (uint8_t i = 0; i < PIXELS_PER_BANK; i++)
      if (CHAIN_TO_SLOT[i] == slot) banks[bankOf(cyl)]->setPixelColor(i, c.r, c.g, c.b);
  }
  bankA.show();
  bankB.show();
}

static void selfTest() {
  Serial.println("test: boots in firing order");
  for (uint8_t k = 0; k < N_CYL; k++) {
    uint8_t cyl = FIRING_ORDER[k];
    bankA.clear();
    bankB.clear();
    uint8_t slot = slotOf(cyl);
    for (uint8_t i = 0; i < PIXELS_PER_BANK; i++)
      if (CHAIN_TO_SLOT[i] == slot) banks[bankOf(cyl)]->setPixelColor(i, 255, 200, 120);
    bankA.show();
    bankB.show();
    Serial.printf("  cylinder %u (bank %c, slot %u from the front)\n", cyl, bankOf(cyl) ? 'B' : 'A', slot + 1);
    delay(600);
  }
  bankA.clear();
  bankB.clear();
  bankA.show();
  bankB.show();
  Serial.println("test: motors 3 s");
  setMotors(RUN_DUTY);
  delay(3000);
  setMotors(0.0f);
}

static RunState run;
static Button button;
static float duty = 0.0f, crankDeg = 0.0f;
static uint32_t lastFrame = 0;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pwmInit();
  setMotors(0.0f);
  bankA.begin();
  bankB.begin();
  Serial.printf("Cup Lite controller %s\n", FW_VERSION);
  uint32_t t0 = millis();
  while (digitalRead(PIN_BUTTON) == LOW && millis() - t0 < TEST_HOLD_MS) delay(10);
  if (digitalRead(PIN_BUTTON) == LOW) {
    selfTest();
    while (digitalRead(PIN_BUTTON) == LOW) delay(10);   // do not count the held press
  }
  lastFrame = millis();
}

void loop() {
  uint32_t now = millis();
  int ev = button.update(digitalRead(PIN_BUTTON) == LOW, now, DEBOUNCE_MS, LONG_PRESS_MS);
  if (ev) {
    onPress(run, ev == 2, now, SHOW_MS);
    Serial.printf("button %s -> mode %u\n", ev == 2 ? "long" : "short", (unsigned)run.mode);
  }
  tick(run, now);

  uint32_t dt = now - lastFrame;
  if (dt < FRAME_MS) return;
  lastFrame = now;

  float target = run.mode == Mode::Stopped ? 0.0f : RUN_DUTY;
  duty = rampDuty(duty, target, (float)dt, (float)RAMP_MS, MIN_DUTY);
  setMotors(duty);

  float rpm = duty * RPM_AT_FULL;                       // open loop: N20 speed ~ duty
  crankDeg = wrap720(crankDeg + rpm * 6.0f * dt / 1000.0f);
  showBoots(crankDeg, rpm, IDLE_GLOW);

  // ring LED: steady while running, slow breathe when stopped so people know to press it
  uint8_t ring = run.mode != Mode::Stopped ? 255 : (uint8_t)(40 + 40 * (1 + sinf(now / 600.0f)));
  ledcWrite(4, ring);
}
