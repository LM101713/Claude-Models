// =============================================================================
// V10 display engine - controller firmware
//
// Board:   ESP32-DevKitC-32E (ESP32-WROOM-32E)
// Driver:  TMC2209 (UART, StealthChop) -> NEMA17 -> GT2 3:1 -> crankshaft
// Sensors: DRV5033 hall switch under the front crank web (one magnet at
//          cylinder 1 TDC), 10k speed knob, START button with ring LED
// LEDs:    two WS2812B strips (one per bank, 3 LEDs over every bore)
//
// How the LEDs stay in time with the pistons
//   The ESP32's pulse-counter hardware counts every STEP pulse the driver gets
//   and wraps at one 4-stroke cycle (2 crank revolutions). That count IS the
//   crank angle. The hall magnet re-checks it once per revolution: small
//   differences are corrected silently, a big one means the motor lost steps
//   (stall / belt skip) and raises a fault. No magnet for 1.4 revolutions
//   while running = jammed or stalled.
//
// Why an ESP32 and not an Arduino Nano: a Nano has to switch interrupts off
// for ~0.9 ms every time it updates 30 WS2812B LEDs, which drops step pulses
// at the 19.2 kHz step rate needed for 120 RPM (audible jerk, LEDs drift out
// of time). The ESP32 makes both the step pulses (MCPWM) and the LED data
// (RMT) in hardware, counts the steps in hardware (PCNT) and has two cores.
//
// Operating modes
//   power on      -> HOMING: turns slowly, finds the magnet, parks cylinder 1 at TDC
//   READY         -> START short press: run at the knob speed (soft start)
//   RUN           -> knob sets 20-120 RPM; knob at the bottom = idle
//                    no interaction for 5 min -> IDLE (20 RPM, dimmer flames)
//                    no interaction for 15 min -> soft stop -> SLEEP
//                    START short press -> soft stop -> READY
//                    START long press (2 s) -> soft stop -> SLEEP
//   SLEEP         -> motor off, LEDs off, START ring breathes; START wakes it
//   FAULT         -> motor stopped and off, all LEDs blink a red code (below),
//                    START ring flashes; START clears the fault and re-homes
//   SERVICE       -> hold START while switching on: LED test, homing + park
//                    at cylinder 1 TDC for inspection; long press flips the
//                    motor direction (saved)
//   BURN-IN       -> hold START while switching on with the knob at maximum,
//                    or type "burnin 48" on the USB serial console
//
// Fault codes (number of red blinks)
//   1  hall magnet not found while homing (sensor, magnet or wiring)
//   2  lost steps: magnet seen more than 8 deg away from where it should be
//   3  no rotation: no magnet for 1.4 revolutions while running (jam / belt)
//   4  stepper driver not responding or reporting an error (heat, short)
//   5  supply problem: driver saw undervoltage or a reset
//
// Serial console: 115200 baud, type "help".
// =============================================================================
#include <Arduino.h>
#include <Preferences.h>
#include <FastAccelStepper.h>
#include <TMCStepper.h>
#include <Adafruit_NeoPixel.h>
#include <esp_task_wdt.h>

#include "config.h"
#include "engine_geometry.h"
#include "engine_logic.h"

using namespace v10;

// -----------------------------------------------------------------------------
// objects
// -----------------------------------------------------------------------------
FastAccelStepperEngine stepEngine;
FastAccelStepper* stepper = nullptr;
TMC2209Stepper driver(&Serial2, TMC_RSENSE, TMC_ADDRESS);
Adafruit_NeoPixel stripA(geo::LEDS_PER_STRIP, PIN_LED_A, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel stripB(geo::LEDS_PER_STRIP, PIN_LED_B, NEO_GRB + NEO_KHZ800);
Preferences prefs;

enum class Mode : uint8_t { Homing, Ready, Run, Idle, Stopping, Sleep, Fault, Service, BurnIn };
enum Fault : uint8_t { F_NONE = 0, F_HALL = 1, F_SYNC = 2, F_STALL = 3, F_DRIVER = 4, F_POWER = 5 };

const char* modeName(Mode m) {
  switch (m) {
    case Mode::Homing: return "HOMING";
    case Mode::Ready: return "READY";
    case Mode::Run: return "RUN";
    case Mode::Idle: return "IDLE";
    case Mode::Stopping: return "STOPPING";
    case Mode::Sleep: return "SLEEP";
    case Mode::Fault: return "FAULT";
    case Mode::Service: return "SERVICE";
    case Mode::BurnIn: return "BURN-IN";
  }
  return "?";
}

// -----------------------------------------------------------------------------
// persistent settings (NVS)
// -----------------------------------------------------------------------------
struct Settings {
  bool dirInvert = false;          // flips the motor direction (service mode / "dir")
  int16_t trimSteps = 0;           // hall timing trim ("trim <deg>")
  uint16_t autoSleepMin = geo::AUTO_SLEEP_MIN;   // 0 = never sleep
  uint32_t runMinutes = 0;         // service-hour counter
  uint32_t faults = 0;             // lifetime fault count
} settings;

void loadSettings() {
  prefs.begin("v10", true);
  settings.dirInvert = prefs.getBool("dir", false);
  settings.trimSteps = prefs.getShort("trim", 0);
  settings.autoSleepMin = prefs.getUShort("sleep", geo::AUTO_SLEEP_MIN);
  settings.runMinutes = prefs.getULong("runmin", 0);
  settings.faults = prefs.getULong("faults", 0);
  prefs.end();
}

void saveSettings() {
  prefs.begin("v10", false);
  prefs.putBool("dir", settings.dirInvert);
  prefs.putShort("trim", settings.trimSteps);
  prefs.putUShort("sleep", settings.autoSleepMin);
  prefs.putULong("runmin", settings.runMinutes);
  prefs.putULong("faults", settings.faults);
  prefs.end();
}

// -----------------------------------------------------------------------------
// state
// -----------------------------------------------------------------------------
Mode mode = Mode::Homing;
Mode afterStop = Mode::Ready;      // where STOPPING ends up
Fault fault = F_NONE;
bool parkAfterHoming = true;       // power-on homing parks at cylinder 1 TDC
bool parking = false;
bool parked = false;               // standing at cylinder 1 TDC after homing
bool startAfterHoming = false;     // START pressed while homing: run as soon as parked

bool synced = false;               // crank phase known?
uint32_t tdc = 0;                  // cycle-counter value at cylinder 1 firing TDC
uint32_t lastCount = 0;            // cycle counter at the last loop
uint32_t stepsSinceMagnet = 0;     // steps run since the last good magnet pass
uint32_t magnetPasses = 0;
int32_t worstSyncError = 0;        // steps, since boot / burn-in start

float knobRpm = geo::RPM_IDLE;     // filtered knob reading
float knobFilt = 0.0f;
bool knobAtIdle = true;
float lastInteractionRpm = -100.0f;
uint32_t lastInteractionMs = 0;
float targetRpm = 0.0f;

uint32_t runAccumMs = 0;           // running time not yet added to settings.runMinutes
uint32_t lastNvsSaveMs = 0;

// burn-in
uint32_t burnInStartMs = 0;
uint32_t burnInDurationMs = 0;
uint32_t burnInLastLogMs = 0;
bool burnInPassed = false;
bool burnInDone = false;

// -----------------------------------------------------------------------------
// hall sensor interrupt: stamp every edge with the hardware step count
// -----------------------------------------------------------------------------
struct HallEdge {
  int16_t count;
  uint8_t level;
};
volatile HallEdge hallBuf[16];
volatile uint8_t hallHead = 0;
uint8_t hallTail = 0;
bool magnetOn = false;
uint32_t magnetOnCount = 0;
bool pendingOff = false;           // magnet-left edge waiting to be confirmed
uint32_t pendingOffCount = 0;
constexpr uint32_t HALL_GLITCH_STEPS = geo::STEPS_PER_REV / 360;   // 1 crank degree

void ARDUINO_ISR_ATTR onHallEdge() {
  int16_t c = stepper ? stepper->readPulseCounter() : 0;
  uint8_t h = hallHead;
  hallBuf[h].count = c;
  hallBuf[h].level = (uint8_t)digitalRead(PIN_HALL);
  hallHead = (uint8_t)((h + 1) & 15);
}

uint32_t cycleCount() { return wrapCycle(stepper->readPulseCounter()); }

// -----------------------------------------------------------------------------
// START button ring LED (PWM)
// -----------------------------------------------------------------------------
constexpr uint8_t RING_LEDC_CH = 0;
void ringInit() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(PIN_BUTTON_LED, 1000, 10);
#else
  ledcSetup(RING_LEDC_CH, 1000, 10);
  ledcAttachPin(PIN_BUTTON_LED, RING_LEDC_CH);
#endif
}
void ringWrite(float level) {   // 0..1
  if (level < 0) level = 0;
  if (level > 1) level = 1;
  uint32_t duty = (uint32_t)(level * level * 1023.0f);   // perceptual
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(PIN_BUTTON_LED, duty);
#else
  ledcWrite(RING_LEDC_CH, duty);
#endif
}
float breathe(uint32_t now, float periodS, float lo, float hi) {
  float t = (now % (uint32_t)(periodS * 1000.0f)) / (periodS * 1000.0f);
  return lo + (hi - lo) * 0.5f * (1.0f - cosf(2.0f * PI * t));
}

// -----------------------------------------------------------------------------
// motor
// -----------------------------------------------------------------------------
bool driverConfigured = false;

bool configureDriver() {
  // the TMC2209 needs its 12 V supply before it answers on the UART
  for (int attempt = 0; attempt < 6; attempt++) {
    driver.begin();
    if (driver.test_connection() == 0) {
      driver.GSTAT(0b111);              // clear reset / error flags
      driver.toff(4);
      driver.blank_time(24);
      driver.I_scale_analog(false);     // current from the UART setting, not VREF
      driver.internal_Rsense(false);
      driver.mstep_reg_select(true);
      driver.microsteps(geo::MICROSTEPS);
      driver.intpol(true);              // 256-step interpolation: silky smooth
      driver.rms_current(geo::MOTOR_RUN_MA, geo::MOTOR_HOLD_FRACTION);
      driver.iholddelay(8);
      driver.TPOWERDOWN(20);
      driver.en_spreadCycle(false);     // StealthChop: silent
      driver.pwm_autoscale(true);
      driver.pwm_autograd(true);
      driver.TPWMTHRS(0);               // stay in StealthChop at every speed
      driver.TCOOLTHRS(0);
      driver.SGTHRS(0);
      driverConfigured = true;
      return true;
    }
    delay(150);
  }
  driverConfigured = false;
  return false;
}

void motorSetRpm(float rpm) {
  targetRpm = rpm;
  uint32_t mhz = (uint32_t)(rpmToStepHz(rpm) * 1000.0f);
  stepper->setSpeedInMilliHz(mhz);
  if (stepper->isRunning()) {
    stepper->applySpeedAcceleration();
  } else {
    stepper->runForward();
  }
}

void motorEnable(bool on) {
  if (on) {
    stepper->enableOutputs();
  } else {
    stepper->disableOutputs();
  }
}

float currentRpm() {
  int32_t mhz = stepper->getCurrentSpeedInMilliHz();
  return stepHzToRpm(fabsf((float)mhz) / 1000.0f);
}

// -----------------------------------------------------------------------------
// LEDs
// -----------------------------------------------------------------------------
void ledsOff() {
  stripA.clear();
  stripB.clear();
  stripA.show();
  stripB.show();
}

void setCylinderPixels(Adafruit_NeoPixel& s, const uint8_t* cyl, const uint8_t* pos, uint32_t phase, float brightness) {
  for (int k = 0; k < geo::LEDS_PER_STRIP; k++) {
    float lv = ledLevel(phase, cyl[k], pos[k]);
    Rgb c = flashColour(lv, brightness);
    s.setPixelColor(k, c.r, c.g, c.b);
  }
}

void renderFiring(float brightness) {
  float b = brightness * geo::LED_MAX_BRIGHTNESS / 255.0f;
  uint32_t phase = cycleAhead(tdc, cycleCount());
  setCylinderPixels(stripA, geo::LED_CYL_A, geo::LED_POS_A, phase, b);
  setCylinderPixels(stripB, geo::LED_CYL_B, geo::LED_POS_B, phase, b);
  stripA.show();
  stripB.show();
}

void renderAll(uint8_t r, uint8_t g, uint8_t b) {
  for (int k = 0; k < geo::LEDS_PER_STRIP; k++) {
    stripA.setPixelColor(k, r, g, b);
    stripB.setPixelColor(k, r, g, b);
  }
  stripA.show();
  stripB.show();
}

// N red blinks, pause, repeat
void renderFaultCode(uint32_t now, uint8_t code) {
  const uint32_t on = 250, off = 250, pause = 1500;
  uint32_t period = code * (on + off) + pause;
  uint32_t t = now % period;
  bool lit = t < code * (on + off) && (t % (on + off)) < on;
  uint8_t v = lit ? (uint8_t)(geo::LED_MAX_BRIGHTNESS / 2) : 0;
  renderAll(v, 0, 0);
}

// one cylinder after another in firing order, then red, green, blue
void ledTest() {
  ledsOff();
  for (int i = 0; i < geo::N_CYL; i++) {
    int cyl = geo::FIRING_ORDER[i];
    stripA.clear();
    stripB.clear();
    for (int k = 0; k < geo::LEDS_PER_STRIP; k++) {
      if (geo::LED_CYL_A[k] == cyl) stripA.setPixelColor(k, 120, 120, 120);
      if (geo::LED_CYL_B[k] == cyl) stripB.setPixelColor(k, 120, 120, 120);
    }
    stripA.show();
    stripB.show();
    delay(400);
    esp_task_wdt_reset();
  }
  const uint8_t cols[3][3] = {{120, 0, 0}, {0, 120, 0}, {0, 0, 120}};
  for (auto& c : cols) {
    renderAll(c[0], c[1], c[2]);
    delay(700);
    esp_task_wdt_reset();
  }
  ledsOff();
}

// -----------------------------------------------------------------------------
// faults
// -----------------------------------------------------------------------------
void raiseFault(Fault f, const char* why) {
  if (mode == Mode::Fault) return;
  stepper->forceStop();
  motorEnable(false);
  fault = f;
  mode = Mode::Fault;
  synced = false;
  settings.faults++;
  saveSettings();
  Serial.printf("FAULT %d: %s\n", (int)f, why);
  if (burnInDurationMs) {
    burnInDone = true;
    burnInPassed = false;
  }
}

// -----------------------------------------------------------------------------
// mode changes
// -----------------------------------------------------------------------------
void startHoming(bool park) {
  if (!driverConfigured && !configureDriver()) {
    raiseFault(F_DRIVER, "driver does not answer on UART (no 12 V?)");
    return;
  }
  synced = false;
  magnetOn = false;
  pendingOff = false;
  stepsSinceMagnet = 0;
  lastCount = cycleCount();
  parkAfterHoming = park;
  parking = false;
  parked = false;
  motorEnable(true);
  mode = Mode::Homing;
  motorSetRpm(geo::RPM_HOMING);
  Serial.println("homing...");
}

void startRun() {
  lastInteractionMs = millis();
  lastInteractionRpm = knobRpm;
  parked = false;
  if (!synced) {               // after sleep: run, and the LEDs join at the first magnet pass
    stepsSinceMagnet = 0;
    magnetOn = false;
    pendingOff = false;
    lastCount = cycleCount();
  }
  motorEnable(true);
  mode = Mode::Run;
  motorSetRpm(knobRpm);
}

void startStop(Mode then) {
  afterStop = then;
  mode = Mode::Stopping;
  stepper->stopMove();
}

void enterSleep() {
  motorEnable(false);
  synced = false;              // the crank may be turned by hand while the motor is off
  mode = Mode::Sleep;
  ledsOff();
  Serial.println("sleep");
}

// -----------------------------------------------------------------------------
// hall edge processing (main loop)
// -----------------------------------------------------------------------------
void onMagnetPass(uint32_t center) {
  magnetPasses++;
  stepsSinceMagnet = 0;
  if (!synced) {
    tdc = tdcFromMagnet(center, settings.trimSteps);
    synced = true;
    Serial.println("synchronised to the crank");
    if ((mode == Mode::Homing || mode == Mode::Service) && parkAfterHoming && !parking) {
      // park exactly at cylinder 1 TDC, at least half a turn ahead so the
      // ramp never has to reverse. Absolute target: a relative move would be
      // counted from the end of the step queue, not from here.
      int32_t pos = stepper->getCurrentPosition();
      uint32_t ahead = cycleAhead(cycleCount(), tdc) % geo::STEPS_PER_REV;
      if (ahead < geo::STEPS_PER_REV / 2) ahead += geo::STEPS_PER_REV;
      stepper->moveTo(pos + (int32_t)ahead);
      parking = true;
    }
    return;
  }
  SyncResult r = checkSync(tdc, center, settings.trimSteps);
  int32_t e = r.error < 0 ? -r.error : r.error;
  if (e > worstSyncError) worstSyncError = e;
  if (r.verdict == SyncVerdict::Fault) {
    char msg[80];
    snprintf(msg, sizeof msg, "lost steps: magnet %.1f deg off", stepsToCrankDeg(r.error));
    raiseFault(F_SYNC, msg);
    return;
  }
  tdc = r.newTdc;
}

// A "magnet left" edge only counts once the crank has turned another degree
// without the magnet coming back; a short drop-out inside a pulse (electrical
// noise) is ignored instead of splitting the pulse in two.
void processHall() {
  while (hallTail != hallHead) {
    HallEdge e;
    e.count = hallBuf[hallTail].count;
    e.level = hallBuf[hallTail].level;
    hallTail = (uint8_t)((hallTail + 1) & 15);
    uint32_t c = wrapCycle(e.count);
    if (e.level == LOW) {                   // magnet present
      if (pendingOff && cycleAhead(pendingOffCount, c) < HALL_GLITCH_STEPS) {
        pendingOff = false;                 // drop-out: still the same pulse
      } else if (!magnetOn) {
        magnetOn = true;
        magnetOnCount = c;
      }
    } else if (magnetOn) {                  // magnet gone (to be confirmed)
      pendingOff = true;
      pendingOffCount = c;
    }
  }
  if (pendingOff && cycleAhead(pendingOffCount, cycleCount()) >= HALL_GLITCH_STEPS) {
    pendingOff = false;
    magnetOn = false;
    MagnetPass p = magnetPass(magnetOnCount, pendingOffCount);
    if (p.valid) onMagnetPass(p.center);
  }
}

void trackSteps() {
  uint32_t now = cycleCount();
  stepsSinceMagnet += cycleAhead(lastCount, now);
  lastCount = now;
  bool moving = mode == Mode::Homing || mode == Mode::Run || mode == Mode::Idle ||
                mode == Mode::Stopping || mode == Mode::BurnIn || mode == Mode::Service;
  if (moving && stepsSinceMagnet > geo::NO_HALL_STEPS) {
    if (!synced) {
      raiseFault(F_HALL, "no magnet found in 1.4 revolutions");
    } else {
      raiseFault(F_STALL, "no magnet for 1.4 revolutions - jammed or stalled");
    }
  }
}

// -----------------------------------------------------------------------------
// driver health
// -----------------------------------------------------------------------------
uint8_t driverReadFails = 0;
uint32_t lastDriverPollMs = 0;
uint32_t lastDrvStatus = 0;

void pollDriver(uint32_t now) {
  if (now - lastDriverPollMs < DRIVER_POLL_MS) return;
  lastDriverPollMs = now;
  if (mode == Mode::Sleep || mode == Mode::Fault || !driverConfigured) return;
  uint32_t st = driver.DRV_STATUS();
  uint8_t gs = driver.GSTAT();
  if (st == 0xFFFFFFFF || (st == 0 && gs == 0 && driver.test_connection() != 0)) {
    if (++driverReadFails >= 3) {
      driverConfigured = false;
      raiseFault(F_DRIVER, "driver stopped answering");
    }
    return;
  }
  driverReadFails = 0;
  lastDrvStatus = st;
  const bool ot = st & (1UL << 1);
  const bool shortCircuit = st & ((1UL << 2) | (1UL << 3) | (1UL << 4) | (1UL << 5));
  if (ot || shortCircuit) {
    raiseFault(F_DRIVER, ot ? "driver over-temperature" : "motor short circuit");
    return;
  }
  if (gs & 0b101) {                         // reset or charge-pump undervoltage
    driverConfigured = false;
    raiseFault(F_POWER, (gs & 1) ? "driver was reset (supply dip)" : "supply undervoltage");
  }
}

// -----------------------------------------------------------------------------
// knob and button
// -----------------------------------------------------------------------------
void readKnob() {
  static uint32_t last = 0;
  uint32_t now = millis();
  if (now - last < 20) return;
  last = now;
  float mv = (float)analogReadMilliVolts(PIN_POT);
  float f = (mv - 120.0f) / (3000.0f - 120.0f);          // ESP32 ADC is flat in the last 0.1 V
  if (f < 0) f = 0;
  if (f > 1) f = 1;
  knobFilt += 0.15f * (f - knobFilt);
  const float idleZone = 0.04f;                          // bottom 4 % of the knob = idle
  knobAtIdle = knobFilt < idleZone;
  float rpm = knobAtIdle ? geo::RPM_IDLE
                         : geo::RPM_MIN + (knobFilt - idleZone) / (1.0f - idleZone) * (geo::RPM_MAX - geo::RPM_MIN);
  if (fabsf(rpm - knobRpm) >= KNOB_DEADBAND_RPM || (knobAtIdle && knobRpm != geo::RPM_IDLE)) knobRpm = rpm;
  if (fabsf(knobRpm - lastInteractionRpm) >= KNOB_INTERACTION_RPM) {
    lastInteractionRpm = knobRpm;
    lastInteractionMs = now;
  }
}

enum class Press : uint8_t { None, Short, Long };
bool btnDown = false;
bool btnLongFired = false;
uint32_t btnChangeMs = 0;
uint32_t btnDownMs = 0;

Press readButton() {
  uint32_t now = millis();
  bool down = digitalRead(PIN_BUTTON) == LOW;
  if (down != btnDown && now - btnChangeMs > BUTTON_DEBOUNCE_MS) {
    btnChangeMs = now;
    btnDown = down;
    if (down) {
      btnDownMs = now;
      btnLongFired = false;
      lastInteractionMs = now;
    } else if (!btnLongFired) {
      return Press::Short;
    }
  }
  if (btnDown && !btnLongFired && now - btnDownMs > LONG_PRESS_MS) {
    btnLongFired = true;
    return Press::Long;
  }
  return Press::None;
}

// -----------------------------------------------------------------------------
// burn-in profile (repeats every 60 minutes)
// -----------------------------------------------------------------------------
//  0-10 min 120 RPM | 10-20 20 RPM | 20-40 sweep 20->120->20 | 40-58 70 RPM | 58-60 stopped
float burnInRpm(uint32_t msIntoHour, bool& stopped) {
  float m = msIntoHour / 60000.0f;
  stopped = false;
  if (m < 10) return geo::RPM_MAX;
  if (m < 20) return geo::RPM_MIN;
  if (m < 30) return geo::RPM_MIN + (m - 20) / 10.0f * (geo::RPM_MAX - geo::RPM_MIN);
  if (m < 40) return geo::RPM_MAX - (m - 30) / 10.0f * (geo::RPM_MAX - geo::RPM_MIN);
  if (m < 58) return 70.0f;
  stopped = true;
  return 0.0f;
}

void startBurnIn(float hours) {
  burnInDurationMs = (uint32_t)(hours * 3600000.0f);
  burnInStartMs = millis();
  burnInLastLogMs = 0;
  burnInDone = false;
  burnInPassed = false;
  worstSyncError = 0;
  magnetPasses = 0;
  Serial.printf("BURN-IN start: %.1f h\n", hours);
  Serial.println("min,rpm,magnet_passes,worst_sync_deg,drv_status,faults,min_free_heap,state");
  if (!synced) startHoming(false);
  mode = Mode::BurnIn;
}

void burnInStep(uint32_t now) {
  uint32_t el = now - burnInStartMs;
  if (el >= burnInDurationMs) {
    stepper->stopMove();
    if (!stepper->isRunning()) {
      motorEnable(false);
      burnInDone = true;
      burnInPassed = (fault == F_NONE);
      Serial.printf("BURN-IN %s: %lu magnet passes, worst sync error %.2f deg\n",
                    burnInPassed ? "PASSED" : "FAILED", (unsigned long)magnetPasses,
                    stepsToCrankDeg(worstSyncError));
      burnInDurationMs = 0;
      mode = Mode::Ready;
    }
    return;
  }
  bool stopped;
  float rpm = burnInRpm(el % 3600000UL, stopped);
  if (stopped) {
    if (stepper->isRunning()) stepper->stopMove();
    else stepper->setCurrentPosition(0);         // standstill: rebase the 32-bit position
  } else if (fabsf(rpm - targetRpm) > 0.5f || !stepper->isRunning()) {
    motorSetRpm(rpm);
  }
  if (now - burnInLastLogMs >= 60000UL || burnInLastLogMs == 0) {
    burnInLastLogMs = now;
    Serial.printf("%lu,%.1f,%lu,%.2f,0x%08lX,%lu,%lu,%s\n", (unsigned long)(el / 60000UL), currentRpm(),
                  (unsigned long)magnetPasses, stepsToCrankDeg(worstSyncError), (unsigned long)lastDrvStatus,
                  (unsigned long)settings.faults, (unsigned long)ESP.getMinFreeHeap(), synced ? "synced" : "syncing");
  }
}

// -----------------------------------------------------------------------------
// serial console
// -----------------------------------------------------------------------------
void printStatus() {
  Serial.printf("V10 firmware %s | mode %s | fault %d\n", FW_VERSION, modeName(mode), (int)fault);
  Serial.printf("rpm %.1f (target %.1f, knob %.1f) | synced %s | magnet passes %lu | worst sync %.2f deg\n",
                currentRpm(), targetRpm, knobRpm, synced ? "yes" : "no", (unsigned long)magnetPasses,
                stepsToCrankDeg(worstSyncError));
  Serial.printf("run hours %.1f | lifetime faults %lu | dir %s | trim %.2f deg | auto-sleep %u min\n",
                settings.runMinutes / 60.0f, (unsigned long)settings.faults, settings.dirInvert ? "inverted" : "normal",
                stepsToCrankDeg(settings.trimSteps), settings.autoSleepMin);
  Serial.printf("driver %s | DRV_STATUS 0x%08lX\n", driverConfigured ? "ok" : "not configured",
                (unsigned long)lastDrvStatus);
}

void handleCommand(String line) {
  line.trim();
  if (line.length() == 0) return;
  int sp = line.indexOf(' ');
  String cmd = sp < 0 ? line : line.substring(0, sp);
  String arg = sp < 0 ? String() : line.substring(sp + 1);
  cmd.toLowerCase();
  if (cmd == "help") {
    Serial.println("status | run <rpm> | stop | sleep | wake | home | burnin <hours> | ledtest");
    Serial.println("dir (flip motor direction) | trim <deg> | autosleep <min, 0=off> | clear | version");
  } else if (cmd == "status") {
    printStatus();
  } else if (cmd == "version") {
    Serial.println(FW_VERSION);
  } else if (cmd == "run") {
    float r = arg.toFloat();
    if (r >= geo::RPM_MIN && r <= geo::RPM_MAX) {
      knobRpm = r;
      lastInteractionRpm = r;
      if (mode == Mode::Ready || mode == Mode::Sleep) startRun();
      else motorSetRpm(r);
    } else {
      Serial.printf("rpm must be %.0f-%.0f\n", geo::RPM_MIN, geo::RPM_MAX);
    }
  } else if (cmd == "stop") {
    burnInDurationMs = 0;
    startStop(Mode::Ready);
  } else if (cmd == "sleep") {
    startStop(Mode::Sleep);
  } else if (cmd == "wake" || cmd == "home") {
    fault = F_NONE;
    startHoming(true);
  } else if (cmd == "burnin") {
    float h = arg.toFloat();
    startBurnIn(h > 0 ? h : 48.0f);
  } else if (cmd == "ledtest") {
    if (stepper->isRunning()) Serial.println("stop the engine first");
    else ledTest();
  } else if (cmd == "dir") {
    settings.dirInvert = !settings.dirInvert;
    saveSettings();
    Serial.println("direction flipped and saved - restarting");
    delay(200);
    ESP.restart();
  } else if (cmd == "trim") {
    settings.trimSteps = (int16_t)crankDegToSteps(arg.toFloat());
    saveSettings();
    Serial.printf("trim %.2f deg saved\n", stepsToCrankDeg(settings.trimSteps));
  } else if (cmd == "autosleep") {
    settings.autoSleepMin = (uint16_t)arg.toInt();
    saveSettings();
    Serial.printf("auto-sleep %u min saved\n", settings.autoSleepMin);
  } else if (cmd == "clear") {
    fault = F_NONE;
    startHoming(true);
  } else {
    Serial.println("unknown command - type help");
  }
}

void readSerial() {
  static String buf;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      handleCommand(buf);
      buf = "";
    } else if (buf.length() < 64) {
      buf += c;
    }
  }
}

// -----------------------------------------------------------------------------
// setup
// -----------------------------------------------------------------------------
void setupWatchdog() {
#if ESP_IDF_VERSION_MAJOR >= 5
  esp_task_wdt_config_t cfg = {.timeout_ms = 5000, .idle_core_mask = 0, .trigger_panic = true};
  esp_task_wdt_reconfigure(&cfg);
#else
  esp_task_wdt_init(5, true);
#endif
  esp_task_wdt_add(NULL);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_HALL, INPUT_PULLUP);       // + external 10k pull-up
  analogSetPinAttenuation(PIN_POT, ADC_11db);
  ringInit();
  ringWrite(0.0f);
  stripA.begin();
  stripB.begin();
  ledsOff();
  loadSettings();
  Serial.printf("\nV10 display engine, firmware %s\n", FW_VERSION);

  // stepper: hardware step generation + a hardware counter on the STEP pin
  stepEngine.init();
  stepper = stepEngine.stepperConnectToPin(PIN_STEP);
  if (!stepper) {
    Serial.println("stepper init failed");
    while (true) {
      renderFaultCode(millis(), F_DRIVER);
      delay(20);
    }
  }
  stepper->setDirectionPin(PIN_DIR, !settings.dirInvert);
  stepper->setEnablePin(PIN_EN, true);
  stepper->setAutoEnable(false);
  stepper->setAcceleration((int32_t)rpmToStepHz(geo::ACCEL_RPM_S));
  stepper->setLinearAcceleration(geo::STEPS_PER_REV / 10);     // jerk-free start: 36 crank deg
  stepper->attachToPulseCounter(STEP_PCNT_UNIT, -(int16_t)geo::STEPS_PER_CYCLE, (int16_t)geo::STEPS_PER_CYCLE);
  motorEnable(false);

  Serial2.begin(TMC_BAUD, SERIAL_8N1, PIN_TMC_RX, PIN_TMC_TX);
  delay(200);
  bool drvOk = configureDriver();

  attachInterrupt(digitalPinToInterrupt(PIN_HALL), onHallEdge, CHANGE);
  setupWatchdog();

  // power-on gestures: hold START -> service mode; hold START with the knob
  // at maximum -> 48 h burn-in
  uint32_t t0 = millis();
  bool held = digitalRead(PIN_BUTTON) == LOW;
  while (held && millis() - t0 < SERVICE_HOLD_MS) {
    ringWrite(((millis() / 150) % 2) ? 1.0f : 0.0f);
    held = digitalRead(PIN_BUTTON) == LOW;
    esp_task_wdt_reset();
    delay(10);
  }
  ringWrite(0.0f);
  for (int i = 0; i < 20; i++) {       // settle the knob filter
    readKnob();
    delay(21);
  }
  lastInteractionMs = millis();

  if (!drvOk) {
    raiseFault(F_DRIVER, "driver does not answer on UART (no 12 V?)");
    return;
  }
  if (held) {
    while (digitalRead(PIN_BUTTON) == LOW) {   // wait for release
      esp_task_wdt_reset();
      delay(10);
    }
    btnDown = false;
    if (knobFilt > 0.95f) {
      startBurnIn(48.0f);
    } else {
      mode = Mode::Service;
      Serial.println("SERVICE MODE: LED test, then homing to cylinder 1 TDC");
      ledTest();
      startHoming(true);
      mode = Mode::Service;
    }
    return;
  }
  startHoming(true);
}

// -----------------------------------------------------------------------------
// loop
// -----------------------------------------------------------------------------
void loop() {
  esp_task_wdt_reset();
  uint32_t now = millis();
  readSerial();
  readKnob();
  processHall();
  trackSteps();
  pollDriver(now);
  Press press = readButton();

  // run-hour counter
  static uint32_t lastLoopMs = now;
  if (stepper->isRunning()) runAccumMs += now - lastLoopMs;
  lastLoopMs = now;
  if (runAccumMs >= 60000UL) {
    settings.runMinutes += runAccumMs / 60000UL;
    runAccumMs %= 60000UL;
  }
  static uint32_t savedMinutes = settings.runMinutes;
  if (now - lastNvsSaveMs > NVS_SAVE_MS) {
    lastNvsSaveMs = now;
    if (settings.runMinutes != savedMinutes) {
      savedMinutes = settings.runMinutes;
      saveSettings();
    }
  }

  switch (mode) {
    case Mode::Homing:
    case Mode::Service:
      if (mode == Mode::Homing && press != Press::None) startAfterHoming = true;
      if (parking && !stepper->isRunning()) {
        parking = false;
        parked = true;
        stepper->setCurrentPosition(0);          // standstill: rebase the 32-bit position
        Serial.println("parked at cylinder 1 TDC");
        if (mode == Mode::Homing) {
          mode = Mode::Ready;
          lastInteractionMs = now;
          if (startAfterHoming) {
            startAfterHoming = false;
            startRun();
          }
        }
      }
      if (mode == Mode::Service && press == Press::Long) {
        settings.dirInvert = !settings.dirInvert;
        saveSettings();
        Serial.println("direction flipped and saved - restarting");
        for (int i = 0; i < 4; i++) {
          ringWrite(i % 2 ? 0.0f : 1.0f);
          delay(150);
        }
        ESP.restart();
      }
      if (mode == Mode::Service && press == Press::Short && !stepper->isRunning()) {
        ledTest();
        startHoming(true);
        mode = Mode::Service;
      }
      break;

    case Mode::Ready:
      if (press != Press::None && burnInDone) {   // first press only clears the burn-in result
        burnInDone = false;
        break;
      }
      if (press == Press::Short) startRun();
      else if (press == Press::Long) enterSleep();
      else if (settings.autoSleepMin && now - lastInteractionMs > settings.autoSleepMin * 60000UL) enterSleep();
      break;

    case Mode::Run:
    case Mode::Idle: {
      uint32_t quiet = now - lastInteractionMs;
      if (press == Press::Short) {
        startStop(Mode::Ready);
        break;
      }
      if (press == Press::Long) {
        startStop(Mode::Sleep);
        break;
      }
      if (settings.autoSleepMin && quiet > settings.autoSleepMin * 60000UL) {
        Serial.println("no interaction - going to sleep");
        startStop(Mode::Sleep);
        break;
      }
      bool autoIdle = geo::AUTO_IDLE_MIN && quiet > geo::AUTO_IDLE_MIN * 60000UL;
      mode = (autoIdle || knobAtIdle) ? Mode::Idle : Mode::Run;
      float want = mode == Mode::Idle ? geo::RPM_IDLE : knobRpm;
      if (fabsf(want - targetRpm) > 0.05f) motorSetRpm(want);
      break;
    }

    case Mode::Stopping:
      if (!stepper->isRunning()) {
        stepper->setCurrentPosition(0);          // standstill: rebase the 32-bit position
        if (afterStop == Mode::Sleep) {
          enterSleep();
        } else {
          mode = Mode::Ready;
          lastInteractionMs = now;
        }
        saveSettings();
      }
      break;

    case Mode::Sleep:
      if (press != Press::None) startRun();
      break;

    case Mode::Fault:
      if (press != Press::None) {
        Serial.println("fault cleared - re-homing");
        fault = F_NONE;
        if (!driverConfigured) configureDriver();
        startHoming(true);
      }
      break;

    case Mode::BurnIn:
      if (burnInDone) break;
      if (press == Press::Short) {
        Serial.println("burn-in aborted by START");
        burnInDurationMs = 0;
        startStop(Mode::Ready);
        break;
      }
      if (synced || stepper->isRunning()) burnInStep(now);
      break;
  }

  // ---- outputs: LEDs and the START ring, 200 frames per second -------------
  static uint32_t lastFrame = 0;
  if (now - lastFrame >= LED_FRAME_MS) {
    lastFrame = now;
    switch (mode) {
      case Mode::Run:
      case Mode::Stopping:
      case Mode::BurnIn:
      case Mode::Homing:
      case Mode::Service:
        if (mode == Mode::Service && parked) {
          // inspection: cylinder 1 (front left) lit steady - its piston must be at the top
          stripA.clear();
          stripB.clear();
          for (int k = 0; k < geo::LEDS_PER_STRIP; k++)
            if (geo::LED_CYL_A[k] == 1) stripA.setPixelColor(k, 90, 90, 90);
          stripA.show();
          stripB.show();
        } else if (synced) {
          renderFiring(1.0f);
        } else {
          ledsOff();
        }
        ringWrite(mode == Mode::Homing || (mode == Mode::BurnIn && !synced) ? breathe(now, 0.6f, 0.0f, 1.0f) : 1.0f);
        break;
      case Mode::Idle:
        if (synced) renderFiring(IDLE_BRIGHTNESS);
        else ledsOff();
        ringWrite(1.0f);
        break;
      case Mode::Ready:
        if (burnInDone) {
          if (burnInPassed) renderAll(0, geo::LED_MAX_BRIGHTNESS / 3, 0);   // steady green: passed
          else renderFaultCode(now, fault ? fault : F_STALL);
        } else {
          ledsOff();
        }
        ringWrite(breathe(now, 3.0f, 0.15f, 1.0f));
        break;
      case Mode::Sleep:
        ringWrite(breathe(now, 6.0f, 0.0f, 0.25f));
        break;
      case Mode::Fault:
        renderFaultCode(now, fault);
        ringWrite(((now / 120) % 2) ? 1.0f : 0.0f);
        break;
    }
  }
}
