// Pure engine logic: crank phase, hall-sensor synchronisation and the firing
// flash. No Arduino or ESP32 calls in here, so firmware/test/ can compile and
// test it on a PC (see firmware/test/test_engine_logic.cpp).
//
// Units: "steps" are motor microsteps as counted by the ESP32 pulse counter,
// which wraps at geo::STEPS_PER_CYCLE (= one 720 degree 4-stroke cycle).
#pragma once
#include <stdint.h>
#include <math.h>

#include "engine_geometry.h"

namespace v10 {

// --- modular arithmetic on the cycle counter --------------------------------
inline uint32_t wrapCycle(int32_t s) {
  int32_t m = s % (int32_t)geo::STEPS_PER_CYCLE;
  return (uint32_t)(m < 0 ? m + (int32_t)geo::STEPS_PER_CYCLE : m);
}

// difference a - b, wrapped into one crank revolution [-REV/2, +REV/2)
inline int32_t revDiff(uint32_t a, uint32_t b) {
  int32_t d = ((int32_t)a - (int32_t)b) % (int32_t)geo::STEPS_PER_REV;
  if (d < 0) d += geo::STEPS_PER_REV;
  if (d >= (int32_t)geo::STEPS_PER_REV / 2) d -= geo::STEPS_PER_REV;
  return d;
}

// forward distance from 'from' to 'to' on the cycle counter (0 .. CYCLE-1)
inline uint32_t cycleAhead(uint32_t from, uint32_t to) { return wrapCycle((int32_t)to - (int32_t)from); }

inline float stepsToCrankDeg(int32_t s) { return s * 360.0f / (float)geo::STEPS_PER_REV; }
inline int32_t crankDegToSteps(float d) { return (int32_t)lroundf(d * (float)geo::STEPS_PER_REV / 360.0f); }

// crank RPM <-> motor step rate (steps per second)
inline float rpmToStepHz(float rpm) { return rpm * (float)geo::STEPS_PER_REV / 60.0f; }
inline float stepHzToRpm(float hz) { return hz * 60.0f / (float)geo::STEPS_PER_REV; }

// --- hall sensor ---------------------------------------------------------------
// The magnet in the crank web passes the sensor once per crank revolution,
// geo::HALL_PHASE_STEPS after cylinder 1 TDC (taken from the CAD by the
// generator). The sensor switches ON a little
// before the magnet centre and OFF a little after it, so the middle of the
// two edges is the magnet centre whatever the sensor's sensitivity or the air
// gap - no per-unit calibration.
struct MagnetPass {
  bool valid;
  uint32_t center;   // cycle counter at the magnet centre
  uint32_t width;    // steps between the ON and OFF edges
};

inline MagnetPass magnetPass(uint32_t onCount, uint32_t offCount) {
  MagnetPass p{false, 0, cycleAhead(onCount, offCount)};
  if (p.width < geo::HALL_MIN_WIDTH || p.width > geo::HALL_MAX_WIDTH) return p;   // noise or a stall
  p.valid = true;
  p.center = wrapCycle((int32_t)onCount + (int32_t)(p.width / 2));
  return p;
}

// What a magnet pass means for the step-count synchronisation.
enum class SyncVerdict : uint8_t { Corrected, Fault };

struct SyncResult {
  SyncVerdict verdict;
  int32_t error;      // measured - expected, steps (one revolution wrap)
  uint32_t newTdc;    // updated cylinder-1 firing TDC on the cycle counter
};

// tdc = cycle-counter value of cylinder 1 firing TDC. The magnet passes once
// per revolution, HALL_PHASE_STEPS after either TDC of cylinder 1; both are valid.
inline SyncResult checkSync(uint32_t tdc, uint32_t magnetCenter, int32_t trimSteps) {
  uint32_t expected = wrapCycle((int32_t)tdc + (int32_t)geo::HALL_PHASE_STEPS + trimSteps);
  int32_t err = revDiff(magnetCenter, expected);
  SyncResult r{SyncVerdict::Corrected, err, tdc};
  if (err > geo::SYNC_FAULT_STEPS || err < -geo::SYNC_FAULT_STEPS) {
    r.verdict = SyncVerdict::Fault;
    return r;
  }
  // small errors (step timing, belt stretch) are simply absorbed: the LED
  // timing follows the real crank, the motor keeps its own count
  r.newTdc = wrapCycle((int32_t)tdc + err);
  return r;
}

// First magnet pass after homing defines cylinder 1 firing TDC (which of
// cylinder 1's two TDCs is called "firing" is arbitrary for a display; the
// firmware then keeps it consistent for the rest of the run).
inline uint32_t tdcFromMagnet(uint32_t magnetCenter, int32_t trimSteps) {
  return wrapCycle((int32_t)magnetCenter - (int32_t)geo::HALL_PHASE_STEPS - trimSteps);
}

// --- firing flash ----------------------------------------------------------------
// Light of one cylinder as a function of crank steps since its firing TDC:
// a fast flash at ignition that fades over the power stroke, from white-hot
// through yellow to orange-red, like the glow of the combustion. Defined in
// crank degrees (not time) so it always follows the piston.
struct Rgb { uint8_t r, g, b; };

inline float flashLevel(uint32_t sinceFire) {
  if (sinceFire >= geo::FLASH_STEPS) return 0.0f;
  float x = (float)sinceFire / (float)geo::FLASH_STEPS;      // 0..1 over the flash
  const float attack = 0.04f;
  float a = x < attack ? x / attack : 1.0f;
  float decay = expf(-3.2f * (x < attack ? 0.0f : (x - attack) / (1.0f - attack)));
  float tail = 1.0f - x;                                     // forces exactly 0 at the end
  return a * decay * tail;
}

// colour temperature follows the level: hot white at the peak, red at the tail
inline Rgb flashColour(float level, float brightness) {
  if (level <= 0.0f) return Rgb{0, 0, 0};
  float l = level * brightness;                 // 0..1 (brightness = mode dimming)
  float r = 1.0f;
  float g = 0.12f + 0.68f * level;              // orange -> yellow-white
  float b = level > 0.7f ? (level - 0.7f) * 1.6f : 0.0f;
  return Rgb{(uint8_t)lroundf(255.0f * r * l), (uint8_t)lroundf(255.0f * g * l * l),
             (uint8_t)lroundf(255.0f * b * l)};
}

// level for one LED of a cylinder: the bore-centre LED leads, the two side
// LEDs follow a few degrees later and slightly weaker (the flame spreads)
inline float ledLevel(uint32_t cyclePhase, int cyl, uint8_t posInGroup) {
  if (posInGroup == 255 || cyl < 1) return 0.0f;             // unused pixel of a chained strip
  uint32_t since = cycleAhead(geo::FIRE_STEP[cyl - 1], cyclePhase);
  if (posInGroup == 1 || posInGroup == 3) return flashLevel(since);   // chamber centre and plug boot: at TDC
  const uint32_t lag = geo::STEPS_PER_REV / 90;              // 4 crank degrees
  if (since < lag) return 0.0f;
  return 0.8f * flashLevel(since - lag);
}

}  // namespace v10
