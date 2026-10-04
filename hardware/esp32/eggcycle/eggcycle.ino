// Feed the Egg sensor node (ESP32 DevKit v1)
//
// Reads the egg's sensors, shuts the gas valve on a methane leak, and POSTs a JSON reading
// to the laptop receiver (src/climate/ingest.py) every minute.
//
// Arduino libraries (Library Manager): HX711 (Bogdan Necula), OneWire, DallasTemperature,
// Adafruit_VL53L0X, PZEM004Tv30 (Jakub Mandula), ArduinoJson (v7).
// Copy secrets.example.h to secrets.h and fill it in. Wiring: hardware/README.md

#include <Adafruit_VL53L0X.h>
#include <ArduinoJson.h>
#include <DallasTemperature.h>
#include <HTTPClient.h>
#include <HX711.h>
#include <OneWire.h>
#include <PZEM004Tv30.h>
#include <WiFi.h>

#include "secrets.h"

// --- Pins --------------------------------------------------------------------------------------
const int PIN_HX711_DOUT = 25;  // hopper load cell
const int PIN_HX711_SCK = 26;
const int PIN_TEMP = 4;         // DS18B20 probe inside the egg (4.7k pull-up to 3.3V)
const int PIN_PZEM_RX = 16;     // ESP32 RX2 <- PZEM TX
const int PIN_PZEM_TX = 17;     // ESP32 TX2 -> PZEM RX
const int PIN_MQ4 = 34;         // methane sensor AO via 10k/20k divider (ADC1 works with Wi-Fi on)
const int PIN_PH = 35;          // analog pH probe board (e.g. DFRobot Gravity pH V2), 3.3V
const int PIN_VALVE = 32;       // relay -> normally-closed gas solenoid (HIGH = open)
const int PIN_BUZZER = 27;
const int PIN_RESET = 33;       // push button to GND: re-open valve after a leak is fixed
const int PIN_LED = 2;          // on-board LED: on = Wi-Fi connected
// VL53L0X distance sensor above the gas bag: I2C on SDA 21 / SCL 22

// --- Calibration (measure on your build) -------------------------------------------------------
const float SCALE_FACTOR = 21500.0;  // HX711 counts per kg: weigh a known mass to set
const int BAG_EMPTY_MM = 420;        // sensor -> top of a flat, empty bag
const int BAG_FULL_MM = 120;         // sensor -> top of a full bag
const float MQ4_R0 = 10.0;           // sensor resistance (kOhm) in clean air, after 48h burn-in
const float MQ4_RL = 20.0;           // load resistor on the MQ-4 module (kOhm)
const float LEAK_ALARM_PPM = 5000;   // 10% of methane's lower explosive limit
const float PH7_MV = 1500;           // probe output in pH 7 buffer solution
const float PH4_MV = 2032;           // probe output in pH 4 buffer solution

const unsigned long SAMPLE_MS = 500;
const unsigned long REPORT_MS = 60000;
const float LOADED_KG = 0.10;  // hopper counts as loaded above this
const float EMPTY_KG = 0.03;   // ...and as tipped into the egg below this

HX711 scale;
OneWire oneWire(PIN_TEMP);
DallasTemperature tempSensor(&oneWire);
Adafruit_VL53L0X tof;
PZEM004Tv30 pzem(Serial2, PIN_PZEM_RX, PIN_PZEM_TX);

float hopperKg = 0, stableKg = 0, fedKgUnsent = 0;
float window[4];
int windowFill = 0;
bool hopperLoaded = false;
bool leakLatched = false;
float ch4Ppm = 0;
unsigned long lastSample = 0, lastReport = 0;

// --- Sensors -----------------------------------------------------------------------------------

// Records a feed when the hopper goes from loaded to empty (scraps tipped into the egg).
// Uses the last *stable* weight so pressing on the hopper while tipping doesn't count.
void updateHopper() {
  if (!scale.is_ready()) return;
  hopperKg = scale.get_units(3);
  window[windowFill++ % 4] = hopperKg;
  if (windowFill >= 4) {
    float lo = window[0], hi = window[0];
    for (float w : window) { lo = min(lo, w); hi = max(hi, w); }
    if (hi - lo < 0.02) stableKg = hopperKg;
  }
  if (!hopperLoaded && stableKg > LOADED_KG) hopperLoaded = true;
  if (hopperLoaded && hopperKg < EMPTY_KG) {
    fedKgUnsent += stableKg;
    hopperLoaded = false;
    stableKg = 0;
    lastReport = 0;  // report the feed straight away
  }
}

float readTempC() {
  tempSensor.requestTemperatures();
  float t = tempSensor.getTempCByIndex(0);
  return t == DEVICE_DISCONNECTED_C ? NAN : t;
}

// Two-point calibration: dip the probe in pH 7 and pH 4 buffer, note the mV, set PH7_MV / PH4_MV.
// Healthy slurry is about pH 6.8-7.6; below 6.5 the egg is turning sour (and starts to smell).
float readPh() {
  long mv = 0;
  for (int i = 0; i < 10; i++) mv += analogReadMilliVolts(PIN_PH);
  float slope = (7.0 - 4.0) / (PH7_MV - PH4_MV);
  return 7.0 + slope * (mv / 10.0 - PH7_MV);
}

float readBagPct() {
  VL53L0X_RangingMeasurementData_t m;
  tof.rangingTest(&m, false);
  if (m.RangeStatus == 4) return NAN;  // out of range
  float pct = 100.0 * (BAG_EMPTY_MM - m.RangeMilliMeter) / (BAG_EMPTY_MM - BAG_FULL_MM);
  return constrain(pct, 0, 100);
}

// Rough ppm from the MQ-4 datasheet curve. Indicative only: fit a certified gas alarm too.
float readCh4Ppm() {
  float vOut = analogReadMilliVolts(PIN_MQ4) / 1000.0 * 1.5;  // undo the 10k/20k divider
  if (vOut < 0.05) return 0;
  float rs = MQ4_RL * (5.0 - vOut) / vOut;
  return 1012.7 * pow(rs / MQ4_R0, -2.786);
}

// Fail-safe: valve only opens while powered and no leak is latched.
void updateSafety() {
  ch4Ppm = readCh4Ppm();
  if (ch4Ppm >= LEAK_ALARM_PPM && !leakLatched) {
    leakLatched = true;
    lastReport = 0;  // alert the app now
  }
  if (leakLatched && digitalRead(PIN_RESET) == LOW && ch4Ppm < LEAK_ALARM_PPM / 2) {
    leakLatched = false;
  }
  digitalWrite(PIN_VALVE, leakLatched ? LOW : HIGH);
  digitalWrite(PIN_BUZZER, leakLatched && (millis() / 250) % 2);
}

// --- Network -----------------------------------------------------------------------------------

void ensureWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  for (int i = 0; i < 20 && WiFi.status() != WL_CONNECTED; i++) delay(250);
  digitalWrite(PIN_LED, WiFi.status() == WL_CONNECTED);
}

bool sendReading() {
  JsonDocument doc;
  doc["device"] = DEVICE_ID;
  doc["temp_c"] = readTempC();
  doc["ph"] = readPh();
  doc["hopper_kg"] = hopperKg;
  doc["fed_kg"] = fedKgUnsent;
  doc["bag_pct"] = readBagPct();
  doc["gen_w"] = pzem.power();     // NaN if the generator side is unpowered
  doc["gen_kwh"] = pzem.energy();  // lifetime kWh, stored inside the PZEM
  doc["ch4_ppm"] = ch4Ppm;
  doc["valve_open"] = !leakLatched;
  for (JsonPair kv : doc.as<JsonObject>()) {  // JSON has no NaN: a dead sensor sends null
    if (kv.value().is<float>() && isnan(kv.value().as<float>())) kv.value().set(nullptr);
  }
  String body;
  serializeJson(doc, body);

  ensureWifi();
  if (WiFi.status() != WL_CONNECTED) return false;
  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Egg-Key", EGG_API_KEY);
  int status = http.POST(body);
  http.end();
  Serial.printf("POST %d %s\n", status, body.c_str());
  return status == 200;
}

// --- Main --------------------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  pinMode(PIN_VALVE, OUTPUT);
  digitalWrite(PIN_VALVE, LOW);  // closed until the first safety check
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_RESET, INPUT_PULLUP);
  analogSetPinAttenuation(PIN_MQ4, ADC_11db);
  analogSetPinAttenuation(PIN_PH, ADC_11db);

  scale.begin(PIN_HX711_DOUT, PIN_HX711_SCK);
  scale.set_scale(SCALE_FACTOR);
  scale.tare();  // start with the hopper empty
  tempSensor.begin();
  if (!tof.begin()) Serial.println("VL53L0X not found: check I2C wiring");

  ensureWifi();
}

void loop() {
  unsigned long now = millis();
  if (now - lastSample >= SAMPLE_MS) {
    lastSample = now;
    updateSafety();
    updateHopper();
  }
  if (lastReport == 0 || now - lastReport >= REPORT_MS) {
    lastReport = now;
    if (sendReading()) fedKgUnsent = 0;  // keep feeds until the server has them
  }
}
