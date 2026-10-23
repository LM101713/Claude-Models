#pragma once
#include <stdint.h>
#define NEO_GRB 0x52
#define NEO_KHZ800 0x0000
class Adafruit_NeoPixel { public: Adafruit_NeoPixel(uint16_t n, int16_t pin, uint16_t type); void begin(); void show(); void clear();
  void setPixelColor(uint16_t n, uint8_t r, uint8_t g, uint8_t b); };
