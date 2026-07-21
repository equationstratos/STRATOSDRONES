// STRATOS LoRa ground dongle — transparent fc_lorap <-> USB-serial bridge.
//
// Forwards raw fc_lorap frames between the SX1262 radio and the PC. It never
// parses fc_lorap: the PC side (stratospy.lora) frames/deframes. On USB each
// frame is wrapped [0x7E][len][frame]; on air it is sent verbatim.
//
// Board: Heltec WiFi LoRa 32 V3 (ESP32-S3 + SX1262). RadioLib >= 6.
// EU868 profile — MUST match hardware/pcb_tinyhoop/sx1262.c and
// stratospy.lora: 869.525 MHz, SF7, BW 250 kHz, CR 4/5, preamble 8, CRC on.
//
// Honesty: compiles against RadioLib; NOT flashed/flown in this repo. Verify
// the SX1262 pins for your exact board and your regional band + duty-cycle
// limits before transmitting.
// SPDX-License-Identifier: MIT
#include <RadioLib.h>

// ---- Heltec WiFi LoRa 32 V3 SX1262 pin map (VERIFY for your board) ----
#define LORA_NSS   8
#define LORA_DIO1  14
#define LORA_RST   12
#define LORA_BUSY  13
#define LORA_SCK   9
#define LORA_MOSI  10
#define LORA_MISO  11

#define BAND        869.525   // MHz (EU868 10% duty sub-band). 915.0 for FCC.
#define SF          7
#define BW          250.0     // kHz
#define CR          5         // 4/5
#define SYNC_SOF    0x7E
#define SERIAL_BAUD 921600

SX1262 radio = new Module(LORA_NSS, LORA_DIO1, LORA_RST, LORA_BUSY);

static volatile bool rxFlag = false;
void onDio1() { rxFlag = true; }

void setup() {
  Serial.begin(SERIAL_BAUD);
  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_NSS);
  int st = radio.begin(BAND, BW, SF, CR, RADIOLIB_SX126X_SYNC_WORD_PRIVATE,
                       14 /* dBm */, 8 /* preamble */);
  if (st != RADIOLIB_ERR_NONE) {
    // blink/report — the PC will see no traffic
    while (true) { Serial.printf("radio.begin failed: %d\n", st); delay(1000); }
  }
  radio.setDio1Action(onDio1);
  radio.startReceive();
}

// read one [0x7E][len][frame] packet from USB, blocking up to a few ms
static int readSerialFrame(uint8_t *out) {
  if (Serial.read() != SYNC_SOF) return 0;          // hunt for SOF
  unsigned long t0 = millis();
  while (Serial.available() < 1 && millis() - t0 < 20) {}
  int len = Serial.read();
  if (len <= 0 || len > 64) return 0;
  int got = 0;
  while (got < len && millis() - t0 < 40) {
    if (Serial.available()) out[got++] = Serial.read();
  }
  return got == len ? len : 0;
}

void loop() {
  // PC -> air
  if (Serial.available()) {
    uint8_t frame[64];
    int n = readSerialFrame(frame);
    if (n > 0) {
      radio.transmit(frame, n);
      radio.startReceive();
    }
  }
  // air -> PC
  if (rxFlag) {
    rxFlag = false;
    uint8_t frame[64];
    int n = radio.getPacketLength();
    if (n > 0 && n <= 64 && radio.readData(frame, n) == RADIOLIB_ERR_NONE) {
      Serial.write(SYNC_SOF);
      Serial.write((uint8_t)n);
      Serial.write(frame, n);
    }
    radio.startReceive();
  }
}
