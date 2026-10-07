// Host-side tests of the firmware's engine logic (no ESP32 needed):
//
//     g++ -std=c++17 -O2 -Wall -Wextra -I ../v10_engine test_engine_logic.cpp -o t && ./t
//
// tools/run_firmware_tests.py builds and runs this automatically.
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <algorithm>

#include "engine_logic.h"

using namespace v10;

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

// 1. every cylinder fires once per cycle, in the firing order, 72 deg apart
static void testFiringOrder() {
  std::vector<std::pair<uint32_t, int>> peaks;
  for (int cyl = 1; cyl <= geo::N_CYL; cyl++) {
    // the bore-centre LED starts glowing exactly at the cylinder's firing step
    uint32_t first = geo::STEPS_PER_CYCLE;
    for (uint32_t ph = 0; ph < geo::STEPS_PER_CYCLE; ph++) {
      float now = ledLevel(ph, cyl, 1);
      float before = ledLevel(wrapCycle((int32_t)ph - 1), cyl, 1);
      if (now > 0.0f && before == 0.0f) {
        CHECK(first == geo::STEPS_PER_CYCLE, "cylinder %d lights up twice per cycle", cyl);
        first = ph;
      }
    }
    CHECK(first < geo::STEPS_PER_CYCLE, "cylinder %d never lights", cyl);
    CHECK(wrapCycle((int32_t)first - 1) == geo::FIRE_STEP[cyl - 1] || first == geo::FIRE_STEP[cyl - 1],
          "cylinder %d lights at %u, fires at %u", cyl, first, geo::FIRE_STEP[cyl - 1]);
    peaks.push_back({geo::FIRE_STEP[cyl - 1], cyl});
  }
  std::sort(peaks.begin(), peaks.end());
  for (int i = 0; i < geo::N_CYL; i++) {
    CHECK(peaks[i].second == geo::FIRING_ORDER[i], "position %d in the cycle is cylinder %d, firing order says %d", i,
          peaks[i].second, geo::FIRING_ORDER[i]);
    uint32_t gap = cycleAhead(peaks[i].first, peaks[(i + 1) % geo::N_CYL].first);
    CHECK(gap == geo::STEPS_PER_CYCLE / geo::N_CYL, "uneven firing gap %u after cylinder %d", gap, peaks[i].second);
  }
  CHECK(peaks[0].second == 1 && peaks[0].first == 0, "cylinder 1 must fire at the start of the cycle");
}

// 2. LED map: three head LEDs per cylinder (rear, centre, front), each strip holds one
//    bank's cylinders in rear-to-front order; a chained boot strip (pos 3) may follow,
//    with unused pixels marked 255 and cylinder 0.
static void testLedMap() {
  int count[geo::N_CYL + 1] = {0};
  int boots[geo::N_CYL + 1] = {0};
  const int half = geo::N_CYL / 2;
  for (int k = 0; k < geo::LEDS_PER_STRIP; k++) {
    const uint8_t pa = geo::LED_POS_A[k], pb = geo::LED_POS_B[k];
    if (k < geo::HEAD_LEDS) {
      CHECK(geo::LED_CYL_A[k] >= 1 && geo::LED_CYL_A[k] <= geo::N_CYL, "strip A LED %d -> cylinder %d", k, geo::LED_CYL_A[k]);
      CHECK(geo::LED_CYL_B[k] >= 1 && geo::LED_CYL_B[k] <= geo::N_CYL, "strip B LED %d -> cylinder %d", k, geo::LED_CYL_B[k]);
      CHECK(pa == k % geo::LEDS_PER_CYL && pb == k % geo::LEDS_PER_CYL, "LED %d group position", k);
      count[geo::LED_CYL_A[k]]++;
      count[geo::LED_CYL_B[k]]++;
    } else {
      CHECK((pa == 3 && geo::LED_CYL_A[k] >= 1) || (pa == 255 && geo::LED_CYL_A[k] == 0), "boot pixel A %d", k);
      CHECK((pb == 3 && geo::LED_CYL_B[k] >= 1) || (pb == 255 && geo::LED_CYL_B[k] == 0), "boot pixel B %d", k);
      if (pa == 3) boots[geo::LED_CYL_A[k]]++;
      if (pb == 3) boots[geo::LED_CYL_B[k]]++;
    }
  }
  for (int c = 1; c <= geo::N_CYL; c++) CHECK(count[c] == geo::LEDS_PER_CYL, "cylinder %d has %d LEDs", c, count[c]);
  if (geo::LEDS_PER_STRIP > geo::HEAD_LEDS)
    for (int c = 1; c <= geo::N_CYL; c++) CHECK(boots[c] == 1, "cylinder %d has %d boot LEDs", c, boots[c]);
  // the two strips hold disjoint banks, half the cylinders each
  int onA[geo::N_CYL + 1] = {0};
  for (int k = 0; k < geo::HEAD_LEDS; k++) onA[geo::LED_CYL_A[k]] = 1;
  int nA = 0;
  for (int c = 1; c <= geo::N_CYL; c++) nA += onA[c];
  CHECK(nA == half, "strip A holds %d cylinders", nA);
  for (int k = 0; k < geo::HEAD_LEDS; k++) CHECK(!onA[geo::LED_CYL_B[k]], "cylinder %d on both strips", geo::LED_CYL_B[k]);
  // data enters at the rear: the first head LED belongs to a rear cylinder, the last to a front one
  CHECK(geo::LED_CYL_A[0] != geo::LED_CYL_A[geo::HEAD_LEDS - 1], "strip A order");
}

// 3. flash envelope: 0..1, starts at 0, peaks early, fades to exactly 0
static void testFlash() {
  float peak = 0.0f;
  uint32_t peakAt = 0;
  for (uint32_t s = 0; s <= geo::FLASH_STEPS + 10; s++) {
    float l = flashLevel(s);
    CHECK(l >= 0.0f && l <= 1.0f, "level %f at %u", l, s);
    if (l > peak) {
      peak = l;
      peakAt = s;
    }
  }
  CHECK(flashLevel(0) == 0.0f, "flash must start dark");
  CHECK(flashLevel(geo::FLASH_STEPS) == 0.0f, "flash must end dark");
  CHECK(peak > 0.9f, "peak %f too dim", peak);
  CHECK(peakAt < geo::FLASH_STEPS / 10, "peak at %u is not a flash", peakAt);
  for (uint32_t s = peakAt + 1; s < geo::FLASH_STEPS; s++)
    CHECK(flashLevel(s) <= flashLevel(s - 1) + 1e-6f, "flash brightens again at %u", s);
  Rgb off = flashColour(0.0f, 1.0f);
  CHECK(off.r == 0 && off.g == 0 && off.b == 0, "zero level must be black");
  Rgb hot = flashColour(1.0f, 1.0f), dim = flashColour(1.0f, 0.5f);
  CHECK(hot.r == 255 && dim.r < hot.r, "brightness scaling");
  Rgb late = flashColour(0.2f, 1.0f);
  CHECK(late.g < late.r / 2 && late.b == 0, "fading flame must turn red (r=%u g=%u b=%u)", late.r, late.g, late.b);
}

// 4. hall sensor: centre between the edges, also across the counter wrap
static void testMagnetPass() {
  MagnetPass p = magnetPass(1000, 1600);
  CHECK(p.valid && p.center == 1300 && p.width == 600, "simple pass");
  p = magnetPass(geo::STEPS_PER_CYCLE - 200, 400);          // wraps through 0
  CHECK(p.valid && p.center == 100 && p.width == 600, "wrapped pass: centre %u width %u", p.center, p.width);
  p = magnetPass(500, 510);
  CHECK(!p.valid, "a 10-step blip must be rejected");
  p = magnetPass(500, 500 + geo::HALL_MAX_WIDTH + 1);
  CHECK(!p.valid, "a too-long pulse (stalled on the magnet) must be rejected");
}

// 5. synchronisation: small errors corrected, both TDCs of cylinder 1 accepted, big error = fault
static void testSync() {
  const uint32_t tdc = 5000;
  const int32_t H = (int32_t)geo::HALL_PHASE_STEPS;           // magnet passes H steps after TDC
  auto mag = [&](int32_t steps) { return wrapCycle((int32_t)tdc + H + steps); };
  SyncResult r = checkSync(tdc, mag(0), 0);
  CHECK(r.verdict == SyncVerdict::Corrected && r.error == 0 && r.newTdc == tdc, "exact pass");
  r = checkSync(tdc, mag((int32_t)geo::STEPS_PER_REV), 0);     // the other TDC of cylinder 1
  CHECK(r.verdict == SyncVerdict::Corrected && r.error == 0 && r.newTdc == tdc, "second TDC of the cycle");
  r = checkSync(tdc, mag(40), 0);
  CHECK(r.verdict == SyncVerdict::Corrected && r.error == 40 && r.newTdc == tdc + 40, "small lag corrected");
  r = checkSync(tdc, mag(-40), 0);
  CHECK(r.verdict == SyncVerdict::Corrected && r.error == -40 && r.newTdc == tdc - 40, "small lead corrected");
  r = checkSync(tdc, mag(geo::SYNC_FAULT_STEPS + 1), 0);
  CHECK(r.verdict == SyncVerdict::Fault, "lost steps must be a fault");
  r = checkSync(10, wrapCycle(10 + H - 30), 0);               // across the wrap
  CHECK(r.verdict == SyncVerdict::Corrected && r.error == -30 && r.newTdc == wrapCycle(10 - 30), "wrap: err %d", r.error);
  // magnet -> TDC -> expected magnet is a round trip, with and without trim
  for (int32_t trim : {0, 27, -27}) {
    uint32_t t = tdcFromMagnet(1000, trim);
    CHECK(checkSync(t, 1000, trim).error == 0, "trim %d round trip", trim);
    CHECK(cycleAhead(t, 1000) == wrapCycle(H + trim), "magnet sits HALL_PHASE_STEPS (+trim) after TDC");
  }
  CHECK(geo::HALL_PHASE_STEPS < geo::STEPS_PER_REV, "hall phase within one revolution");
}

// 6. a simulated run: the crank slowly slips behind the motor (belt stretch),
// then skips 12 deg at once - only the skip may raise a fault
static void testSimulatedRun() {
  uint32_t tdc = tdcFromMagnet(777, 0);
  int32_t slip = 0;
  bool faulted = false;
  for (int rev = 1; rev < 400 && !faulted; rev++) {
    slip += (rev % 50 == 0) ? 2 : 0;                          // 2 steps every 50 revs
    if (rev == 300) slip += crankDegToSteps(12.0f);           // a sudden skip
    uint32_t magnet = wrapCycle(777 + rev * (int32_t)geo::STEPS_PER_REV + slip);
    SyncResult r = checkSync(tdc, magnet, 0);
    if (r.verdict == SyncVerdict::Fault) {
      faulted = true;
      CHECK(rev == 300, "fault at revolution %d instead of the skip at 300", rev);
    } else {
      tdc = r.newTdc;
      slip = 0;                                               // the firmware follows the real crank
      // after a correction the next expected magnet is where the crank really is
    }
  }
  CHECK(faulted, "the 12 deg skip was not detected");
}

// 7. conversions
static void testUnits() {
  CHECK(geo::STEPS_PER_REV == geo::MOTOR_FULL_STEPS * geo::MICROSTEPS * geo::DRIVE_RATIO, "steps per rev");
  CHECK((int)lroundf(rpmToStepHz(120.0f)) == 19200, "120 RPM = %f Hz", rpmToStepHz(120.0f));
  CHECK((int)lroundf(stepHzToRpm(3200.0f)) == 20, "3200 Hz = 20 RPM");
  CHECK(crankDegToSteps(360.0f) == (int32_t)geo::STEPS_PER_REV, "deg->steps");
  CHECK(geo::NO_HALL_STEPS > geo::STEPS_PER_REV && geo::NO_HALL_STEPS < 2 * geo::STEPS_PER_REV, "stall window");
  CHECK(geo::SYNC_CORRECT_STEPS < geo::SYNC_FAULT_STEPS, "sync thresholds");
  CHECK(geo::STEPS_PER_CYCLE <= 32767, "the ESP32 pulse counter is 16 bit");
}

int main() {
  testFiringOrder();
  testLedMap();
  testFlash();
  testMagnetPass();
  testSync();
  testSimulatedRun();
  testUnits();
  if (failures) {
    std::printf("%d check(s) FAILED\n", failures);
    return 1;
  }
  std::printf("all firmware logic tests passed\n");
  return 0;
}
