#include "MIDIUSB.h"
#include <NewPing.h>

// ===== Pin LDR e LED =====
#define NUM_NOTE 5

const int LDRpin[NUM_NOTE] = {A5, A4, A3, A2, A1};
const int LEDpin[NUM_NOTE] = {2, 3, 4, 5, 6};

// ===== Sensore ultrasuoni =====
#define TRIG_PIN 10
#define ECHO_PIN 11
#define MAX_DISTANCE 15  

NewPing sonar(TRIG_PIN, ECHO_PIN, MAX_DISTANCE);

// ===== Pulsanti Ottava =====
#define BTN_DOWN 8
#define BTN_UP 9

// ===== MIDI =====
byte noteBase[NUM_NOTE] = {60, 62, 64, 65, 67}; 
bool notaInviata[NUM_NOTE] = {false, false, false, false, false};

int THRESHOLD[NUM_NOTE];
int ottavaCorrente = 0;

// ===== Ultrasuono =====
int distanza = 0;
unsigned long lastPing = 0;
const unsigned long pingInterval = 50; 

// Antirimbalzo
unsigned long lastDebounce = 0;
const unsigned long debounceDelay = 200;

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < NUM_NOTE; i++) {
    pinMode(LDRpin[i], INPUT);
    pinMode(LEDpin[i], OUTPUT);
    THRESHOLD[i] = calibraSingoloLaser(i);
  }

  pinMode(BTN_DOWN, INPUT_PULLUP);
  pinMode(BTN_UP, INPUT_PULLUP);
}

void loop() {
  // === Lettura LDR ===
  for (int i = 0; i < NUM_NOTE; i++) {
    int val = analogRead(LDRpin[i]);

    if (val < THRESHOLD[i] && !notaInviata[i]) {
      inviaNotaOn(noteBase[i] + (ottavaCorrente * 12), i);
      notaInviata[i] = true;
      digitalWrite(LEDpin[i], HIGH);
    } 
    else if (val >= THRESHOLD[i] && notaInviata[i]) {
      inviaNotaOff(noteBase[i] + (ottavaCorrente * 12), i);
      notaInviata[i] = false;
      digitalWrite(LEDpin[i], LOW);
    }
  }

  // === Ultrasuono con intervallo ===
  if (millis() - lastPing >= pingInterval) {
    gestisciUltrasuono();
    lastPing = millis();
  }

  // === Gestione Pulsanti ===
  gestisciOttava();

  // === Controllo messaggi da interfaccia ===
  midiEventPacket_t rx;
  do {
    rx = MidiUSB.read();
    if (rx.header != 0) {
      if ((rx.byte1 & 0xF0) == 0xB0) { // CC message
        byte controller = rx.byte2;
        byte value = rx.byte3;
        if (controller >= 20 && controller <= 24) {
          int index = controller - 20; // LDR 0..4
          noteBase[index] = value;
          Serial.print("Aggiornata nota LDR ");
          Serial.print(index);
          Serial.print(" -> ");
          Serial.println(value);
        }
      }
    }
  } while (rx.header != 0);

  delay(2); 
}

// ===== Calibrazione LDR =====
int calibraSingoloLaser(int index) {
  long somma = 0;
  const int letture = 100;

  Serial.print("Calibrazione LDR ");
  Serial.print(index);
  Serial.println(" (laser attivo)...");

  for (int i = 0; i < letture; i++) {
    somma += analogRead(LDRpin[index]);
    delay(5);
  }

  int media = somma / letture;
  int threshold = max(media - 100, 10);
  
  Serial.print("Threshold LDR ");
  Serial.print(index);
  Serial.print(": ");
  Serial.println(threshold);

  return threshold;
}

// ===== MIDI =====
void inviaControlChange(byte controller, byte value, byte channel = 0) {
  midiEventPacket_t cc = {0x0B, (byte)(0xB0 | channel), controller, value};
  MidiUSB.sendMIDI(cc);
  MidiUSB.flush();
}

void inviaNotaOn(byte nota, int index) {
  midiEventPacket_t noteOn = {0x09, 0x90, nota, 127};
  MidiUSB.sendMIDI(noteOn);

  inviaControlChange(30 + index, 127); // comunicazione ON con python

  MidiUSB.flush();
  Serial.print("Nota ON: ");
  Serial.print(nota);
  Serial.print(" (index ");
  Serial.print(index);
  Serial.println(")");
}

void inviaNotaOff(byte nota, int index) {
  midiEventPacket_t noteOff = {0x08, 0x80, nota, 127};
  MidiUSB.sendMIDI(noteOff);

  inviaControlChange(30 + index, 0); // comunicazione OFF con python

  MidiUSB.flush();
  Serial.print("Nota OFF: ");
  Serial.print(nota);
  Serial.print(" (index ");
  Serial.print(index);
  Serial.println(")");
}

void inviaOttava(int ottava) {
  int val = 64 + ottava;   // ottava = -3..+4 → val = 61..68
  inviaControlChange(40, val);
}

// ===== Gestione Pulsanti Ottava =====
void gestisciOttava() {
  unsigned long now = millis();

  if (now - lastDebounce > debounceDelay) {
    if (digitalRead(BTN_UP) == LOW) {
      ottavaCorrente = min(4, ottavaCorrente + 1);
      Serial.print("Ottava aumentata a: ");
      Serial.println(ottavaCorrente);
      inviaControlChange(31, ottavaCorrente + 64); // shift (+64 per evitare valori negativi)
      inviaOttava(ottavaCorrente);
      lastDebounce = now;
    }

    if (digitalRead(BTN_DOWN) == LOW) {
      ottavaCorrente = max(-3, ottavaCorrente - 1);
      Serial.print("Ottava diminuita a: ");
      Serial.println(ottavaCorrente);
      inviaControlChange(31, ottavaCorrente + 64);
      inviaOttava(ottavaCorrente);
      lastDebounce = now;
    }
  }
}

// ===== Gestione ultrasuoni con NewPing =====
void gestisciUltrasuono() {
  distanza = sonar.ping_cm();

  if (distanza == 0) distanza = MAX_DISTANCE; // valore massimo se nessuna risposta

  int valoreMIDI = map(distanza, 2, MAX_DISTANCE, 127, 0);
  valoreMIDI = constrain(valoreMIDI, 0, 127);

  inviaControlChange(91, valoreMIDI); 
}
