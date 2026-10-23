// Pure logic of the Cup Lite controller: firing-order flashes, motor ramp and the button state
// machine. No Arduino calls, so firmware_cup/test/ compiles and checks it on a PC.
#pragma once
#include <math.h>
#include <stdint.h>

namespace cup {

// GM small-block numbering: odd cylinders on bank A (driver's left), even on bank B, 1 and 2 at
// the front. Firing order 1-8-7-3-6-5-4-2, one cylinder every 90 crank degrees.
constexpr uint8_t N_CYL = 8;
constexpr uint8_t FIRING_ORDER[N_CYL] = {1, 8, 7, 3, 6, 5, 4, 2};

inline uint8_t bankOf(uint8_t cyl) { return (cyl % 2) ? 0 : 1; }      // 0 = A, 1 = B
inline uint8_t slotOf(uint8_t cyl) { return (uint8_t)((cyl - 1) / 2); }  // 0 = front

// Crank angle (0..720) at which `cyl` fires.
inline float fireAngle(uint8_t cyl) {
  for (uint8_t i = 0; i < N_CYL; i++)
    if (FIRING_ORDER[i] == cyl) return 90.0f * i;
  return -1.0f;
}

inline float wrap720(float a) {
  a = fmodf(a, 720.0f);
  return a < 0.0f ? a + 720.0f : a;
}

// Brightness 0..1 of a boot `msSince` ms after its spark: 12 ms attack, ~110 ms fade, plus a
// slow ember so the boot never snaps dark at display speeds.
inline float flashLevel(float msSince) {
  if (msSince < 0.0f) return 0.0f;
  const float attack = 12.0f;
  if (msSince < attack) return msSince / attack;
  float t = msSince - attack;
  return 0.85f * expf(-t / 110.0f) + 0.15f * expf(-t / 700.0f);
}

// Level of `cyl` at crank angle `crankDeg` and crank speed `rpm` (> 0). Only the latest spark
// counts (720 deg ago at most), so at very low RPM the ember just fades out.
inline float cylinderLevel(uint8_t cyl, float crankDeg, float rpm) {
  if (rpm <= 0.01f) return 0.0f;
  float since = wrap720(crankDeg - fireAngle(cyl));       // degrees since its spark
  float ms = since / (rpm * 6.0f) * 1000.0f;              // rpm*6 = degrees per second
  return flashLevel(ms);
}

// Spark colour: white-hot at the flash, cooling to orange; level 0..1, out 0..255.
struct Rgb { uint8_t r, g, b; };
inline Rgb sparkColour(float level, float brightness) {
  if (level < 0.0f) level = 0.0f;
  if (level > 1.0f) level = 1.0f;
  float l = level * brightness;
  float g = 0.35f + 0.5f * level;             // greener (whiter) when hot
  float b = 0.05f + 0.55f * level * level;
  auto c = [](float v) { return (uint8_t)(v <= 0.0f ? 0 : v >= 1.0f ? 255 : v * 255.0f + 0.5f); };
  return Rgb{c(l), c(l * g), c(l * b)};
}

// --- motor ramp ----------------------------------------------------------------------------
// Duty moves toward `target` at full scale per rampMs, jumping over the stall band
// [0, minDuty) so the motors never sit buzzing without turning.
inline float rampDuty(float duty, float target, float dtMs, float rampMs, float minDuty) {
  float step = dtMs / rampMs;
  if (target > duty) {
    if (duty < minDuty) duty = minDuty;
    duty = duty + step > target ? target : duty + step;
  } else if (target < duty) {
    duty -= step;
    if (duty < target) duty = target;
    if (duty < minDuty && target < minDuty) duty = 0.0f;
  }
  return duty;
}

// --- button and run state -------------------------------------------------------------------
enum class Mode : uint8_t { Stopped, Show, Continuous };

struct RunState {
  Mode mode = Mode::Stopped;
  uint32_t showUntil = 0;
};

// Short press: Stopped -> Show (SHOW_MS), Show or Continuous -> Stopped.
// Long press: Continuous on/off.
inline void onPress(RunState& s, bool longPress, uint32_t now, uint32_t showMs) {
  if (longPress) {
    s.mode = (s.mode == Mode::Continuous) ? Mode::Stopped : Mode::Continuous;
  } else if (s.mode == Mode::Stopped) {
    s.mode = Mode::Show;
    s.showUntil = now + showMs;
  } else {
    s.mode = Mode::Stopped;
  }
}

inline void tick(RunState& s, uint32_t now) {
  if (s.mode == Mode::Show && (int32_t)(now - s.showUntil) >= 0) s.mode = Mode::Stopped;
}

// Debounced button with short / long press detection. Feed raw (true = pressed) every loop.
// Returns 1 for a short press (on release), 2 for a long press (as soon as it is reached).
struct Button {
  bool stable = false, last = false, longFired = false;
  uint32_t changedAt = 0, pressedAt = 0;
  int update(bool raw, uint32_t now, uint32_t debounceMs, uint32_t longMs) {
    if (raw != last) { last = raw; changedAt = now; }
    int ev = 0;
    if ((now - changedAt) >= debounceMs && raw != stable) {
      stable = raw;
      if (stable) { pressedAt = now; longFired = false; }
      else if (!longFired) ev = 1;
    }
    if (stable && !longFired && (now - pressedAt) >= longMs) { longFired = true; ev = 2; }
    return ev;
  }
};

}  // namespace cup
