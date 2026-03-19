#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

static const uint8_t PEER_MAC[6] = {0xF4, 0x2D, 0xC9, 0x6A, 0x8C, 0xFC}; // <-- REPLACE with ESP32 #1 MAC
static const uint8_t CHANNEL = 6;

static const int RXD2 = 16;
static const int TXD2 = 17;
static const uint32_t UART_BAUD = 115200;

// Keep payload <= 250 bytes for ESP-NOW.
static const size_t MAX_PAYLOAD = 200;

// Ring buffer for bytes received over ESP-NOW and waiting to go out UART2.
static const size_t RX_BUF_SIZE = 2048;
volatile uint8_t rxBuf[RX_BUF_SIZE];
volatile size_t rxHead = 0;
volatile size_t rxTail = 0;

typedef struct __attribute__((packed)) {
  uint8_t msgType;     // 1 = data
  uint8_t reserved;
  uint16_t seq;
  uint16_t len;
  uint8_t payload[MAX_PAYLOAD];
} BridgePacket;

volatile uint16_t txSeq = 0;

bool ringPush(const uint8_t* data, size_t len) {
  for (size_t i = 0; i < len; i++) {
    size_t nextHead = (rxHead + 1) % RX_BUF_SIZE;
    if (nextHead == rxTail) {
      return false; // overflow
    }
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

void onDataRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len < (int)sizeof(BridgePacket) - (int)MAX_PAYLOAD) {
    return;
  }

  BridgePacket pkt;
  memcpy(&pkt, data, min((int)sizeof(pkt), len));

  if (pkt.msgType != 1) return;
  if (pkt.len > MAX_PAYLOAD) return;
  if ((size_t)len < (sizeof(BridgePacket) - MAX_PAYLOAD + pkt.len)) return;

  ringPush(pkt.payload, pkt.len);
}

void onDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  // Optional debug:
  // Serial.print("ESP-NOW send status: ");
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
  Serial2.begin(UART_BAUD, SERIAL_8N1, RXD2, TXD2);
  delay(1000);

  Serial.println();
  Serial.println("ESP-NOW <-> UART2 bridge starting");
  WiFi.mode(WIFI_STA);
  Serial.print("This board MAC: ");
  Serial.println(WiFi.macAddress());

  initEspNow();

  Serial.println("Ready");
}

void loop() {
  // UART2 -> ESP-NOW
  if (Serial2.available()) {
    BridgePacket pkt = {};
    pkt.msgType = 1;
    pkt.seq = txSeq++;

    size_t n = 0;
    while (Serial2.available() && n < MAX_PAYLOAD) {
      int c = Serial2.read();
      if (c >= 0) pkt.payload[n++] = (uint8_t)c;
    }
    pkt.len = n;

    size_t packetBytes = sizeof(pkt) - MAX_PAYLOAD + pkt.len;
    esp_err_t err = esp_now_send(PEER_MAC, (uint8_t*)&pkt, packetBytes);
    if (err != ESP_OK) {
      // Optional debug:
      // Serial.printf("esp_now_send error: %d\n", (int)err);
    }
  }

  // ESP-NOW -> UART2
  uint8_t tmp[128];
  size_t n = ringPop(tmp, sizeof(tmp));
  if (n > 0) {
    Serial2.write(tmp, n);
  }
}