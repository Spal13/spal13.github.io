#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

static const uint8_t PEER_MAC[6] = {0xE0, 0x8C, 0xFE, 0x59, 0x43, 0xE8}; // REPLACE
static const uint8_t CHANNEL = 6;

static const size_t MAX_PAYLOAD = 200;
static const size_t RX_BUF_SIZE = 2048;

volatile uint8_t rxBuf[RX_BUF_SIZE];
volatile size_t rxHead = 0;
volatile size_t rxTail = 0;

typedef struct __attribute__((packed)) {
  uint8_t msgType;
  uint8_t reserved;
  uint16_t seq;
  uint16_t len;
  uint8_t payload[MAX_PAYLOAD];
} BridgePacket;

volatile uint16_t txSeq = 0;

bool ringPush(const uint8_t* data, size_t len) {
  for (size_t i = 0; i < len; i++) {
    size_t nextHead = (rxHead + 1) % RX_BUF_SIZE;
    if (nextHead == rxTail) return false;
    rxBuf[rxHead] = data[i];
    rxHead = nextHead;
  }
  return true;
}

size_t ringPop(uint8_t* out, size_t maxLen) {
  size_t count = 0;
  while (count < maxLen && rxTail != rxHead) {
    out[count++] = rxBuf[rxTail];
    rxTail = (rxTail + 1) % RX_BUF_SIZE;
  }
  return count;
}

// New-style recv callback for Arduino-ESP32 3.x
void onDataRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len < (int)(sizeof(BridgePacket) - MAX_PAYLOAD)) return;

  BridgePacket pkt;
  memcpy(&pkt, data, min((int)sizeof(pkt), len));

  if (pkt.msgType != 1) return;
  if (pkt.len > MAX_PAYLOAD) return;
  if ((size_t)len < (sizeof(BridgePacket) - MAX_PAYLOAD + pkt.len)) return;

  ringPush(pkt.payload, pkt.len);
}

// New-style send callback for Arduino-ESP32 3.x
void onDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  // Optional debug:
  // Serial.print("Send status: ");
  // Serial.println(status == ESP_NOW_SEND_SUCCESS ? "OK" : "FAIL");
}

void initEspNow() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true, true);

  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(CHANNEL, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);

  if (esp_now_init() != ESP_OK) {
    Serial.println("esp_now_init() failed");
    while (true) delay(1000);
  }

  esp_now_register_recv_cb(onDataRecv);
  esp_now_register_send_cb(onDataSent);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, PEER_MAC, 6);
  peerInfo.channel = CHANNEL;
  peerInfo.ifidx = WIFI_IF_STA;
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("esp_now_add_peer() failed");
    while (true) delay(1000);
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("USB Serial <-> ESP-NOW bridge starting");
  WiFi.mode(WIFI_STA);
  Serial.print("This board MAC: ");
  Serial.println(WiFi.macAddress());

  initEspNow();

  Serial.println("Ready");
}

void loop() {
  // USB Serial -> ESP-NOW
  if (Serial.available()) {
    BridgePacket pkt = {};
    pkt.msgType = 1;
    pkt.seq = txSeq++;

    size_t n = 0;
    while (Serial.available() && n < MAX_PAYLOAD) {
      int c = Serial.read();
      if (c >= 0) pkt.payload[n++] = (uint8_t)c;
    }
    pkt.len = n;

    size_t packetBytes = sizeof(pkt) - MAX_PAYLOAD + pkt.len;
    esp_err_t err = esp_now_send(PEER_MAC, (uint8_t*)&pkt, packetBytes);
    if (err != ESP_OK) {
      // Serial.printf("esp_now_send error: %d\n", (int)err);
    }
  }

  // ESP-NOW -> USB Serial
  uint8_t tmp[128];
  size_t n = ringPop(tmp, sizeof(tmp));
  if (n > 0) {
    Serial.write(tmp, n);
  }
}