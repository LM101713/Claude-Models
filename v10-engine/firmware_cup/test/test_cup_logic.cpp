// Host-side tests of the Cup Lite controller logic (no ESP32 needed):
//
//     g++ -std=c++17 -O2 -Wall -Wextra -I ../src test_cup_logic.cpp -o t && ./t
#include <cstdio>
#include <vector>

#include "cup_logic.h"

using namespace cup;

static int failures = 0;
#define CHECK(cond, ...)                                  \
  do {                                                    \
    if (!(cond)) {                                        \
      std::printf("FAIL %s:%d: ", __FILE__, __LINE__);    \
      std::printf(__VA_ARGS__);                           \
      std::printf("\n");                                  \
      failures++;                                         \
    }                                                     \
  } while (0)

// 1. walking the crank through two revolutions, the boots peak in the firing order, 90 deg apart
static void testFiringOrder() {
  const float rpm = 36.0f;
  std::vector<int> order;
  float prev[N_CYL + 1] = {};
  for (float a = 0.0f; a < 720.0f; a += 0.5f) {
    for (uint8_t c = 1; c <= N_CYL; c++) {
      float l = cylinderLevel(c, a, rpm);
      if (l > 0.9f && prev[c] <= 0.9f) order.push_back(c);
      prev[c] = l;
    }
  }
  CHECK(order.size() == N_CYL, "expected 8 flashes per cycle, got %zu", order.size());
  for (size_t i = 0; i < order.size() && i < N_CYL; i++)
    CHECK(order[i] == FIRING_ORDER[i], "flash %zu is cylinder %d, expected %d", i, order[i], FIRING_ORDER[i]);
  for (uint8_t i = 0; i < N_CYL; i++)
    CHECK(fireAngle(FIRING_ORDER[i]) == 90.0f * i, "cylinder %d fires at %.1f", FIRING_ORDER[i], fireAngle(FIRING_ORDER[i]));
}

// 2. GM numbering: odd on bank A, even on bank B, 1/2 at the front, 7/8 at the rear
static void testBanks() {
  for (uint8_t c = 1; c <= N_CYL; c++) {
    CHECK(bankOf(c) == ((c % 2) ? 0 : 1), "cylinder %d on the wrong bank", c);
    CHECK(slotOf(c) == (c - 1) / 2, "cylinder %d in slot %d", c, slotOf(c));
  }
  CHECK(slotOf(1) == 0 && slotOf(2) == 0 && slotOf(7) == 3 && slotOf(8) == 3, "front/rear slots");
}

// 3. flash shape: rises to full, decays, never negative, stopped crank is dark
static void testFlash() {
  CHECK(flashLevel(-1.0f) == 0.0f, "before the spark");
  CHECK(flashLevel(12.0f) > 0.99f, "peak at 12 ms is %.3f", flashLevel(12.0f));
  CHECK(flashLevel(300.0f) < 0.25f, "still bright at 300 ms: %.3f", flashLevel(300.0f));
  for (float t = 19.0f; t < 3000.0f; t += 7.0f)
    CHECK(flashLevel(t) < flashLevel(t - 7.0f) + 1e-6f, "not monotonic after the peak at %.0f ms", t);
  CHECK(cylinderLevel(1, 0.0f, 0.0f) == 0.0f, "lit while stopped");
  Rgb hot = sparkColour(1.0f, 1.0f), warm = sparkColour(0.2f, 1.0f);
  CHECK(hot.r == 255 && hot.g > warm.g, "colour should cool from white to orange");
}

// 4. ramp: jumps the stall band, reaches the target in about RAMP_MS, stops to exactly 0
static void testRamp() {
  float d = 0.0f;
  d = rampDuty(d, 0.8f, 10.0f, 2500.0f, 0.25f);
  CHECK(d >= 0.25f, "first step %.3f should jump past the stall band", d);
  int steps = 1;
  while (d < 0.8f && steps < 1000) { d = rampDuty(d, 0.8f, 10.0f, 2500.0f, 0.25f); steps++; }
  CHECK(steps * 10 <= 1500, "ramp up took %d ms", steps * 10);
  while (d > 0.0f && steps < 3000) { d = rampDuty(d, 0.0f, 10.0f, 2500.0f, 0.25f); steps++; }
  CHECK(d == 0.0f, "ramp down ended at %.3f", d);
}

// 5. button: debounce, short vs long press, show times out
static void testButton() {
  Button b;
  RunState s;
  uint32_t t = 0;
  int ev = 0;
  // bouncy short press of 200 ms
  for (int i = 0; i < 5; i++) { ev |= b.update(i % 2 == 0, t, 30, 1500); t += 3; }
  for (; t < 215; t += 5) ev |= b.update(true, t, 30, 1500);
  CHECK(ev == 0, "event before release: %d", ev);
  int rel = 0;
  for (; t < 300; t += 5) rel |= b.update(false, t, 30, 1500);
  CHECK(rel == 1, "short press gave %d", rel);
  onPress(s, false, t, 120000);
  CHECK(s.mode == Mode::Show, "short press should start a show");
  tick(s, t + 119000);
  CHECK(s.mode == Mode::Show, "show ended early");
  tick(s, t + 120001);
  CHECK(s.mode == Mode::Stopped, "show did not end");
  // long press
  int lp = 0;
  uint32_t t0 = t;
  for (; t < t0 + 1600; t += 5) lp |= b.update(true, t, 30, 1500);
  CHECK(lp == 2, "long press gave %d", lp);
  int after = 0;
  for (; t < t0 + 1700; t += 5) after |= b.update(false, t, 30, 1500);
  CHECK(after == 0, "release after a long press gave %d", after);
  onPress(s, true, t, 120000);
  CHECK(s.mode == Mode::Continuous, "long press should run continuously");
  tick(s, t + 10u * 3600u * 1000u);
  CHECK(s.mode == Mode::Continuous, "continuous mode timed out");
  onPress(s, false, t, 120000);
  CHECK(s.mode == Mode::Stopped, "short press should stop");
}

int main() {
  testFiringOrder();
  testBanks();
  testFlash();
  testRamp();
  testButton();
  if (failures) {
    std::printf("%d check(s) failed\n", failures);
    return 1;
  }
  std::printf("all Cup Lite logic tests pass\n");
  return 0;
}
