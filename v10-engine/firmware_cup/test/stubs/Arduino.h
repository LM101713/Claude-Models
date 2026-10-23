// compile-check stub of the Arduino-ESP32 2.0.x API used by firmware_cup (not for running)
#pragma once
#include <stdint.h>
#include <math.h>
#include <stdio.h>
#define HIGH 1
#define LOW 0
#define INPUT_PULLUP 5
uint32_t millis();
void delay(uint32_t);
void pinMode(uint8_t, uint8_t);
int digitalRead(uint8_t);
double ledcSetup(uint8_t ch, double freq, uint8_t bits);
void ledcAttachPin(uint8_t pin, uint8_t ch);
void ledcWrite(uint8_t ch, uint32_t duty);
struct HWCDC { void begin(unsigned long); size_t println(const char*); size_t printf(const char*, ...) __attribute__((format(printf, 2, 3))); };
extern HWCDC Serial;
