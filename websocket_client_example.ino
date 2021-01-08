i ca#include <ArduinoWebsockets.h>
#include <ESP8266WiFi.h>

#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#include <ArduinoJson.h>

#include <string>
#include <iostream>
#include <sstream>
using namespace std;


const char* ssid = "SSID"; //Enter SSID
const char* password = "PASSWORD"; //Enter Password
const char* websockets_server_host = "HOST ADDRESS"; //Enter server adress
const uint16_t websockets_server_port = 9000; // Enter server port

using namespace websockets;
WebsocketsClient client;

void displayText(String text) {
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println(text);
  display.display();
}
void setup() {
  Serial.begin(115200);
  // Connect to wifi
  WiFi.begin(ssid, password);

  // Wait some time to connect to wifi
  for (int i = 0; i < 10 && WiFi.status() != WL_CONNECTED; i++) {
    Serial.print(".");
    delay(1000);
  }

  // Check if connected to wifi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("No Wifi!");
    return;
  }

  Serial.println("Connected to Wifi, Connecting to server.");
  // try to connect to Websockets server
  bool connected = client.connect(websockets_server_host, websockets_server_port, "/info");
  if (connected) {
    Serial.println("Connecetd!");
    client.send("subscribe");
  } else {
    Serial.println("Not Connected!");
  }
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed."));
    for (;;); // Don't proceed, loop forever
  }
  display.display();
  delay(2000); // Pause for 2 seconds

  display.clearDisplay();

  display.display();
  delay(2000);
  // run callback when messages are received

  client.onMessage([&](WebsocketsMessage message) {
    Serial.println("Got Message: ");
    Serial.println(message.data());
    DynamicJsonDocument doc (1024);
    deserializeJson(doc, (String)message.data());   
    JsonObject obj = doc.as<JsonObject>();
    String text = "TKER:"+(String)((const char*)(doc["ticker"]));
    text += "\nEVNT:"+(String)((const char*)(doc["event"]));
    text += "\nQNT:"+(String)((const int)(doc["quant"]));
    text += "\nCOST:"+(String)((const double)(doc["cost"]));
    displayText((String)text);
  });
}

void loop() {
    if (client.available()) {
      client.poll();
    }
    delay(3000);
}
