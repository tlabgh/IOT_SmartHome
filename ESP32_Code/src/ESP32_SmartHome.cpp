// ==========================================================
// ===============   ESP32 SMART HOME (ALL IN ONE)  =========
// ==========================================================
// -------- THƯ VIỆN CẦN DÙNG --------
#include <Arduino.h>
#include <EEPROM.h>           // EEPROM (bộ nhớ không mất khi mất điện) lưu SSID/PASS
#include <ArduinoJson.h>      // JSON (định dạng dữ liệu key-value)
#include <WiFi.h>             // WiFi cho ESP32
#include <WebServer.h>        // WebServer (máy chủ web chạy trên ESP32)
#include <Ticker.h>           // Ticker (timer định kỳ)
#include <ESP32Servo.h>       // Điều khiển Servo cho ESP32
#include <DHT.h>   // thư viện DHT (cảm biến nhiệt độ/độ ẩm)
#include <HTTPClient.h>  // HTTP client (thư viện gửi yêu cầu HTTP)
#include <Firebase_ESP_Client.h>  // Firebase cho ESP32
#include "addons/TokenHelper.h"   // Firebase token helper
#include "addons/RTDBHelper.h"    // Firebase Realtime Database helper

// Tạo WebServer chạy port 80 (HTTP)
WebServer webServer(80);
Ticker blinker;
// ==== LED PINS ====
const int led1 = 14;
const int led2 = 27;
const int led3 = 26;
const int led4 = 25;
const int led5 = 33;

// ==== TRẠNG THÁI LED ====
bool led1State = false;
bool led2State = false;
bool led3State = false;
bool led4State = false;
bool led5State = false;

// ==== SERVO ====
Servo gateServo;
const int SERVO_PIN = 32;
int servoAngle = 0;
const int SERVO_CLOSED_ANGLE = 0;
const int SERVO_OPENED_ANGLE = 180;
bool doorOpen = false;

// ==== DHT / NHIỆT ĐỘ – ĐỘ ẨM ====
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
float currentTempC = NAN;   // nhiệt độ hiện tại (°C – degree Celsius)
float currentHum   = NAN;   // độ ẩm hiện tại (% – humidity)


unsigned long lastTempRead = 0;  // lưu lần đọc nhiệt độ gần nhất (ms)
// ==========================================================
// ===============   WIFI CONFIG (GỘP TỪ wifiConfig.h)  =====
// ==========================================================

String ssid;
String password;
#define ledPin 2        // LED trạng thái WiFi
#define btnPin 0        // Nút nhấn reset WiFi (giữ 5s)
unsigned long lastTimePress = millis();
#define PUSHTIME 5000   // 5 giây
int wifiMode;           // 0: cấu hình, 1: đã kết nối, 2: mất WiFi
unsigned long blinkTime = millis();

// ===== FIREBASE CONFIG =====
#define FIREBASE_HOST "iot-smarthome-d03a9-default-rtdb.asia-southeast1.firebasedatabase.app"
#define FIREBASE_AUTH "AIzaSyByP2XPL9NUEO33aYh7p3N67IeKjVG0YUA"
#define FB_BASE_PATH  "/esp32_1"

// Firebase objects
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

// ===== STATIC IP CONFIG (Comment để dùng DHCP - Bỏ comment để dùng IP cố định) =====
// IPAddress staticIP(192, 168, 1, 100);    // IP cố định cho ESP32
// IPAddress gateway(192, 168, 1, 1);       // Gateway của router
// IPAddress subnet(255, 255, 255, 0);      // Subnet mask
// IPAddress primaryDNS(8, 8, 8, 8);        // DNS chính (Google)
// IPAddress secondaryDNS(8, 8, 4, 4);      // DNS phụ (Google)


// Trang web cấu hình WiFi (AP mode)
const char wifiConfigHtml[] PROGMEM = R"html(
  <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>SETTING WIFI INFORMATION</title>
        <style type="text/css">
          body{display: flex;justify-content: center;align-items: center;}
          button{width: 135px;height: 40px;margin-top: 10px;border-radius: 5px}
          label, span{font-size: 25px;}
          input{margin-bottom: 10px;width:275px;height: 30px;font-size: 17px;}
          select{margin-bottom: 10px;width: 280px;height: 30px;font-size: 17px;}
        </style>
    </head>
    <body>
      <div>
        <h3 style="text-align: center;">SETTING WIFI INFORMATION</h3>
        <p id="info" style="text-align: center;">Scanning wifi network...!</p>
        <label>Wifi name:</label><br>
        <select id="ssid">
          <option>Choise wifi name!</option>
        </select><br>
        <label>Password:</label><br>
        <input id="password" type="text"><br>

        <button onclick="saveWifi()" style="background-color: cyan;margin-right: 10px">SAVE</button>
        <button onclick="reStart()" style="background-color: pink;">RESTART</button>
      </div>
        <script type="text/javascript">
          window.onload=function(){
            scanWifi();
          }
          var xhttp = new XMLHttpRequest();
          function scanWifi(){
            xhttp.onreadystatechange = function(){
              if(xhttp.readyState==4&&xhttp.status==200){
                data = xhttp.responseText;
                document.getElementById("info").innerHTML = "WiFi scan completed!"
                var obj = JSON.parse(data);
                var select = document.getElementById("ssid");
                for(var i=0; i<obj.length;++i){
                  select[select.length] = new Option(obj[i],obj[i]);
                }
              }
            }
            xhttp.open("GET","/scanWifi",true);
            xhttp.send();
          }
          function saveWifi(){
            ssid = document.getElementById("ssid").value;
            pass = document.getElementById("password").value;
            xhttp.onreadystatechange = function(){
              if(xhttp.readyState==4&&xhttp.status==200){
                data = xhttp.responseText;
                alert(data);
              }
            }
            xhttp.open("GET","/saveWifi?ssid="+ssid+"&pass="+pass,true);
            xhttp.send();
          }
          function reStart(){
            xhttp.onreadystatechange = function(){
              if(xhttp.readyState==4&&xhttp.status==200){
                data = xhttp.responseText;
                alert(data);
              }
            }
            xhttp.open("GET","/reStart",true);
            xhttp.send();
          }
        </script>
    </body>
  </html>
)html";

// Nháy LED theo thời gian t (ms)
void blinkLed(uint32_t t){
  if(millis() - blinkTime > t){
    digitalWrite(ledPin, !digitalRead(ledPin));
    blinkTime = millis();
  }
}

// Điều khiển LED trạng thái theo wifiMode & nút
void ledControl(){
  if(digitalRead(btnPin) == LOW){
    if(millis() - lastTimePress < PUSHTIME){
      blinkLed(1000);
    }else{
      blinkLed(50);
    }
  }else{
    if(wifiMode == 0){
      blinkLed(50);
    }else if(wifiMode == 1){
      blinkLed(3000);
    }else if(wifiMode == 2){
      blinkLed(300);
    }
  }
}

// Đặt góc servo tùy ý, kiểu: /gate_angle?val=90
void handleGateAngle() {
  if (!webServer.hasArg("val")) {
    webServer.send(400, "text/plain", "Missing 'val'");
    return;
  }
  int angle = webServer.arg("val").toInt();  // toInt (chuyển sang số)
  angle = constrain(angle, 0, 180);          // constrain (giới hạn) trong [0,180]

  servoAngle = angle;
  gateServo.write(servoAngle);

  // Cập nhật trạng thái cửa dựa trên góc
  // (nếu >90 coi như "mở", tùy bạn chỉnh ngưỡng)
  doorOpen = (servoAngle > 45);

  webServer.send(200, "text/plain", "OK");
}

// ==== HÀM SỰ KIỆN WIFI (tương thích core cũ & mới) ====
void WiFiEvent(
  #if defined(ARDUINO_EVENT_MAX) || defined(ARDUINO_EVENT_WIFI_READY)
    arduino_event_id_t event
  #else
    WiFiEvent_t event
  #endif
) {
  switch (event) {
    // Khi STA nhận IP thành công
    #ifdef ARDUINO_EVENT_WIFI_STA_GOT_IP
    case ARDUINO_EVENT_WIFI_STA_GOT_IP:
    #endif
    #ifdef IP_EVENT_STA_GOT_IP
    case IP_EVENT_STA_GOT_IP:
    #endif
    #ifdef SYSTEM_EVENT_STA_GOT_IP
    case SYSTEM_EVENT_STA_GOT_IP:
    #endif
      Serial.println("Connected to WiFi");
      Serial.print("IP Address: ");
      Serial.println(WiFi.localIP());
      wifiMode = 1;
      break;

    // Khi STA mất kết nối
    #ifdef ARDUINO_EVENT_WIFI_STA_DISCONNECTED
    case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
    #endif
    #ifdef WIFI_EVENT_STA_DISCONNECTED
    case WIFI_EVENT_STA_DISCONNECTED:
    #endif
    #ifdef SYSTEM_EVENT_STA_DISCONNECTED
    case SYSTEM_EVENT_STA_DISCONNECTED:
    #endif
      Serial.println("Disconnected from WiFi");
      wifiMode = 2;
      WiFi.reconnect();
      break;

    default:
      break;
  }
}

// Kết nối WiFi STA hoặc tạo AP nếu chưa có SSID
void setupWifi(){
  if(ssid != ""){
    Serial.println("Connecting to wifi...!");
    WiFi.mode(WIFI_STA);
    
    // ⚡ Chọn 1 trong 2 cách cấu hình IP:
    
    // CÁCH 1: STATIC IP - Bỏ comment 5 dòng dưới để dùng IP cố định
    // if (!WiFi.config(staticIP, gateway, subnet, primaryDNS, secondaryDNS)) {
    //   Serial.println("⚠️ Static IP configuration failed!");
    // } else {
    //   Serial.println("✅ Static IP configured: " + staticIP.toString());
    // }
    
    // CÁCH 2: DHCP - IP tự động (đang dùng)
    Serial.println("✅ Using DHCP (automatic IP)");
    
    WiFi.onEvent(WiFiEvent);
    WiFi.setAutoReconnect(true);
    WiFi.persistent(false);
    WiFi.begin(ssid.c_str(), password.c_str());
  }else{
    Serial.println("ESP32 wifi network created!");
    WiFi.mode(WIFI_AP);
    uint8_t macAddr[6];
    WiFi.softAPmacAddress(macAddr);
    String ssid_ap = "ESP32-" + String(macAddr[4],HEX) + String(macAddr[5],HEX);
    ssid_ap.toUpperCase();
    WiFi.softAP(ssid_ap.c_str());
    Serial.println("Access point name:" + ssid_ap);
    Serial.println("Web server access address:" + WiFi.softAPIP().toString());
    wifiMode = 0;
  }
}

// Cấu hình WebServer WiFi config + LED HTTP API
void setupWebServer(){
  // Trang cấu hình WiFi
  webServer.on("/", [](){
    webServer.send(200, "text/html", wifiConfigHtml);
  });

  // Scan WiFi
  webServer.on("/scanWifi", [](){
    Serial.println("Scanning wifi network...!");
    int wifi_nets = WiFi.scanNetworks(true, true);
    const unsigned long t = millis();
    while (wifi_nets < 0 && millis() - t < 10000){
      delay(20);
      wifi_nets = WiFi.scanComplete();
    }
    DynamicJsonDocument doc(200);
    for(int i = 0; i < wifi_nets; ++i){
      Serial.println(WiFi.SSID(i));
      doc.add(WiFi.SSID(i));
    }
    String wifiList;
    serializeJson(doc, wifiList);
    Serial.println("Wifi list: " + wifiList);
    webServer.send(200, "application/json", wifiList);
  });

  // Lưu WiFi vào EEPROM
  webServer.on("/saveWifi", [](){
    String ssid_temp = webServer.arg("ssid");
    String password_temp = webServer.arg("pass");
    Serial.println("SSID:" + ssid_temp);
    Serial.println("PASS:" + password_temp);
    EEPROM.writeString(0, ssid_temp);
    EEPROM.writeString(32, password_temp);
    EEPROM.commit();
    webServer.send(200, "text/plain", "Wifi has been saved!");
  });

  // Restart ESP32
  webServer.on("/reStart", [](){
    webServer.send(200, "text/plain", "Esp32 is restarting!");
    delay(3000);
    ESP.restart();
  });

  // ----- ROUTE điều khiển LED (HTTP GET) -----
  // PHÒNG KHÁCH
  webServer.on("/on1",  [](){
    digitalWrite(led1, HIGH);
    led1State = true;
    webServer.send(200,"text/plain","LED1 ON");
  });
  webServer.on("/off1", [](){
    digitalWrite(led1, LOW);
    led1State = false;
    webServer.send(200,"text/plain","LED1 OFF");
  });

  // PHÒNG NGỦ
  webServer.on("/on2",  [](){
    digitalWrite(led2, HIGH);
    led2State = true;
    webServer.send(200,"text/plain","LED2 ON");
  });
  webServer.on("/off2", [](){
    digitalWrite(led2, LOW);
    led2State = false;
    webServer.send(200,"text/plain","LED2 OFF");
  });

  // NHÀ BẾP
  webServer.on("/on3",  [](){
    digitalWrite(led3, HIGH);
    led3State = true;
    webServer.send(200,"text/plain","LED3 ON");
  });
  webServer.on("/off3", [](){
    digitalWrite(led3, LOW);
    led3State = false;
    webServer.send(200,"text/plain","LED3 OFF");
  });

  // NHÀ VỆ SINH
  webServer.on("/on4",  [](){
    digitalWrite(led4, HIGH);
    led4State = true;
    webServer.send(200,"text/plain","LED4 ON");
  });
  webServer.on("/off4", [](){
    digitalWrite(led4, LOW);
    led4State = false;
    webServer.send(200,"text/plain","LED4 OFF");
  });

  // PHÒNG LÀM VIỆC
  webServer.on("/on5",  [](){
    digitalWrite(led5, HIGH);
    led5State = true;
    webServer.send(200, "text/plain", "LED5 ON");
  });
  webServer.on("/off5", [](){
    digitalWrite(led5, LOW);
    led5State = false;
    webServer.send(200, "text/plain", "LED5 OFF");
  });

  webServer.begin();
}

// Xử lý nút nhấn để xóa EEPROM cấu hình WiFi
void checkButton(){
  if(digitalRead(btnPin) == LOW){
    Serial.println("Press and hold for 5 seconds to reset to default!");
    if(millis() - lastTimePress > PUSHTIME){
      for(int i = 0; i < 100; i++){
        EEPROM.write(i, 0);
      }
      EEPROM.commit();
      Serial.println("EEPROM memory erased!");
      delay(2000);
      ESP.restart();
    }
    delay(1000);
  }else{
    lastTimePress = millis();
  }
}

// Lớp Config quản lý WiFi + WebServer
class Config {
public:
  void begin(){
    pinMode(ledPin, OUTPUT);
    pinMode(btnPin, INPUT_PULLUP);
    blinker.attach_ms(50, ledControl);
    EEPROM.begin(100);

    char ssid_temp[32], password_temp[64];
    EEPROM.readString(0, ssid_temp, sizeof(ssid_temp));
    EEPROM.readString(32, password_temp, sizeof(password_temp));
    ssid = String(ssid_temp);
    password = String(password_temp);
    if(ssid != ""){
      Serial.println("Wifi name:" + ssid);
      Serial.println("Password:" + password);
    }
    setupWifi();
    setupWebServer();
  }

  void run(){
    checkButton();
    webServer.handleClient();  // xử lý HTTP request
  }
} wifiConfig;


// ==========================================================
// ===============   DASHBOARD HTML (SMART HOME)  ===========
// ==========================================================

const char DASHBOARD_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Smart Home IoT - PTIT</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f4f6;
      color: #111827;
      margin: 0;
      overflow-x: hidden;
    }

    .page {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    .page-inner {
      width: 100%;
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 12px 24px;
      box-sizing: border-box;
    }

    /* ===== HEADER TRÊN ===== */
    .top-header {
      background: #ffffff;
      border-bottom: 3px solid #e5e7eb;
      padding: 10px 16px;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 16px;
    }

    .top-logo {
      height: 54px;
      width: auto;
    }

    .top-text {
      text-align: left;
    }

    .school-name {
      font-size: 1rem;
      font-weight: 700;
      color: #1f2937;
      text-transform: uppercase;
    }

    .project-name {
      font-size: 1rem;
      font-weight: 700;
      color: #b91c1c;
      text-transform: uppercase;
      margin-top: 2px;
    }

    .sub-line {
      font-size: 0.8rem;
      color: #4b5563;
      margin-top: 4px;
    }

    /* ===== LAYOUT DƯỚI ===== */
    .layout {
      flex: 1;
      display: flex;
      min-height: 0;
    }

    .sidebar {
      width: 220px;
      background: #ffffff;
      border-right: 1px solid #e5e7eb;
      padding: 16px 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .nav-title {
      font-size: 0.8rem;
      letter-spacing: 0.08em;
      color: #6b7280;
      text-transform: uppercase;
      margin-bottom: 4px;
    }

    .nav-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 10px;
      border-radius: 999px;
      border: none;
      background: transparent;
      cursor: pointer;
      font-size: 0.9rem;
      color: #111827;
      text-align: left;
      transition: background 0.15s ease, transform 0.1s ease;
    }

    .nav-icon {
      width: 28px;
      height: 28px;
      border-radius: 999px;
      background: #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.1rem;
    }

    .nav-item:hover {
      background: #e5e7eb;
      transform: translateX(2px);
    }

    .nav-item.active {
      background: #16a34a;
      color: #ffffff;
    }

    .nav-item.active .nav-icon {
      background: #ffffff;
      color: #16a34a;
    }

    .sidebar-footer {
      margin-top: auto;
      font-size: 0.75rem;
      color: #6b7280;
    }

    .sidebar-footer strong {
      color: #111827;
    }

    /* ===== CONTENT ===== */
    .content {
      flex: 1;
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .content-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }

    .content-title {
      font-size: 1.3rem;
      font-weight: 600;
      color: #111827;
    }

    .content-subtitle {
      font-size: 0.85rem;
      color: #6b7280;
      margin-top: 2px;
    }

    .badge {
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.8rem;
      background: #e5e7eb;
      color: #111827;
    }
    .badge.online { color: #16a34a; }
    .badge.offline { color: #b91c1c; }

    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-top: 6px;
    }

    .card {
      background: #ffffff;
      border-radius: 14px;
      padding: 14px 16px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.06);
      border: 1px solid #e5e7eb;
    }

    .card-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      font-size: 0.9rem;
      color: #4b5563;
      font-weight: 500;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      background: #f3f4f6;
      font-size: 0.75rem;
      color: #6b7280;
    }

    .dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #22c55e;
    }

    .card-main {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 8px;
      color: #111827;
    }

    .card-desc {
      font-size: 0.8rem;
      color: #6b7280;
    }

    /* Icon nhỏ trong title */
    .card-title-icon {
      margin-right: 6px;
      font-size: 1.1rem;
      vertical-align: -2px;
    }

    /* Danh sách trạng thái từng đèn trên Dashboard */
    .light-list {
      list-style: none;
      margin: 6px 0 0 0;
      padding: 0;
    }

    .light-item {
      display: flex;
      align-items: center;
      font-size: 0.85rem;
      color: #4b5563;
      margin-top: 2px;
    }

    .light-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #9ca3af; /* xám = tắt */
      margin-right: 6px;
    }

    .light-item.on .light-dot {
      background: #16a34a; /* xanh = bật */
    }

    .light-room {
      min-width: 120px;
      font-weight: 500;
      text-transform: uppercase;
      font-size: 0.78rem;
      color: #111827;
      margin-right: 6px;
    }

    /* Icon cho nhiệt độ & độ ẩm */
    .sensor-emoji {
      font-size: 1.2rem;
      margin-right: 4px;
      vertical-align: -2px;
    }

    .btn-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }

    .btn {
      flex: 1;
      min-width: 90px;
      padding: 8px 10px;
      border-radius: 999px;
      border: none;
      font-size: 0.85rem;
      cursor: pointer;
      background: #e5e7eb;
      color: #111827;
      transition: background 0.15s ease, transform 0.1s ease, box-shadow 0.15s ease;
    }

    .btn-primary {
      background: #16a34a;
      color: #f9fafb;
      font-weight: 600;
      box-shadow: 0 8px 18px rgba(22,163,74,0.35);
    }

    .btn-danger {
      background: #dc2626;
      color: #fee2e2;
      font-weight: 600;
      box-shadow: 0 8px 18px rgba(220,38,38,0.35);
    }

    .btn:active {
      transform: scale(0.97);
      box-shadow: none;
    }

    .sensor-value {
      font-size: 1.7rem;
      font-weight: 700;
      color: #111827;
    }

    .sensor-unit {
      font-size: 0.9rem;
      color: #6b7280;
      margin-left: 4px;
    }

    .hidden {
      display: none;
    }

    .switch-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 10px;
    }

    .switch {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 0.85rem;
      cursor: pointer;
      user-select: none;
    }

    .switch-label {
      min-width: 60px;
    }

    .switch-track {
      width: 44px;
      height: 22px;
      border-radius: 999px;
      background: #e5e7eb;
      position: relative;
      transition: background 0.15s ease;
    }

    .switch-thumb {
      position: absolute;
      top: 2px;
      left: 2px;
      width: 18px;
      height: 18px;
      border-radius: 999px;
      background: #ffffff;
      box-shadow: 0 1px 4px rgba(0,0,0,0.3);
      transition: transform 0.15s ease;
    }

    .switch.on .switch-track {
      background: #16a34a;
    }

    .switch.on .switch-thumb {
      transform: translateX(22px);
    }

    .view-title {
      font-size: 1.1rem;
      font-weight: 600;
      margin: 4px 0 10px;
    }

    @media (max-width: 768px) {
      .layout {
        flex-direction: column;
      }
      .sidebar {
        width: 100%;
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
      }
      .sidebar-footer {
        display: none;
      }
      .nav-title {
        display: none;
      }
      .nav-list {
        flex-direction: row;
        gap: 4px;
      }
      .nav-item {
        font-size: 0.8rem;
        padding: 6px 8px;
      }
      .content {
        padding: 12px;
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <header class="top-header">
      <img
        src="https://upload.wikimedia.org/wikipedia/commons/1/13/Logo_PTIT_University.png"
        alt="PTIT Logo"
        class="top-logo"
      />
      <div class="top-text">
        <div class="school-name">HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG CƠ SỞ TP.HỒ CHÍ MINH</div>
        <div class="project-name">SMART HOME IoT</div>
        <div class="sub-line">Bảng điều khiển thiết bị thông minh dùng ESP32</div>
      </div>
    </header>

    <div class="layout">
      <!-- SIDEBAR -->
      <aside class="sidebar">
        <div>
          <div class="nav-title">Điều hướng</div>
          <div class="nav-list">
            <button class="nav-item active" onclick="showView('dashboard')">
              <div class="nav-icon">🏠</div>
              <span>Dashboard</span>
            </button>
            <button class="nav-item" onclick="showView('door')">
              <div class="nav-icon">🚪</div>
              <span>Cửa ra vào</span>
            </button>
            <button class="nav-item" onclick="showView('lights')">
              <div class="nav-icon">💡</div>
              <span>Đèn chiếu sáng</span>
            </button>
            <button class="nav-item" onclick="showView('sensor')">
              <div class="nav-icon">📡</div>
              <span>Cảm biến</span>
            </button>
          </div>
        </div>

        <div class="sidebar-footer">
          <div><strong>WiFi:</strong> local network</div>
          <div>Presented by 😄</div>
        </div>
      </aside>

      <!-- CONTENT -->
      <main class="content">
        <div class="content-header">
          <div>
            <div class="content-title">Smart Home Dashboard</div>
            <div class="content-subtitle">Giám sát & điều khiển thiết bị</div>
          </div>
          <div>
            <span id="wifi-badge" class="badge offline">WiFi: checking...</span>
          </div>
        </div>

        <!-- VIEW: DASHBOARD -->
        <section id="view-dashboard" class="view">
          <div class="cards-grid">
            <!-- Cửa -->
            <div class="card">
              <div class="card-title">
                <span><span class="card-title-icon">🚪</span>Cửa ra vào</span>
                <span class="pill" id="door-state-pill">Đang đóng</span>
              </div>
              <div class="card-main" id="door-state-text-dashboard">
                Cửa đang đóng
              </div>
              <div class="card-desc">
                Xem nhanh trạng thái cửa (mở / đóng). Điều khiển tại tab "Cửa ra vào".
              </div>
            </div>

            <!-- Đèn -->
            <div class="card">
              <div class="card-title">
                <span><span class="card-title-icon">💡</span>Đèn chiếu sáng</span>
                <span class="pill">5 kênh LED</span>
              </div>
              <div class="card-main" id="lights-summary">
                ...
              </div>
              <div class="card-desc">
                <ul class="light-list">
                  <li class="light-item" id="light-item-1">
                    <span class="light-dot"></span>
                    <span class="light-room">PHÒNG KHÁCH</span>
                    <span id="light-status-1">--</span>
                  </li>
                  <li class="light-item" id="light-item-2">
                    <span class="light-dot"></span>
                    <span class="light-room">PHÒNG NGỦ</span>
                    <span id="light-status-2">--</span>
                  </li>
                  <li class="light-item" id="light-item-3">
                    <span class="light-dot"></span>
                    <span class="light-room">NHÀ BẾP</span>
                    <span id="light-status-3">--</span>
                  </li>
                  <li class="light-item" id="light-item-4">
                    <span class="light-dot"></span>
                    <span class="light-room">NHÀ VỆ SINH</span>
                    <span id="light-status-4">--</span>
                  </li>
                  <li class="light-item" id="light-item-5">
                    <span class="light-dot"></span>
                    <span class="light-room">PHÒNG LÀM VIỆC</span>
                    <span id="light-status-5">--</span>
                  </li>
                </ul>
              </div>
            </div>

            <!-- Cảm biến nhiệt độ / độ ẩm -->
            <div class="card">
              <div class="card-title">
                <span><span class="card-title-icon">🌡</span>Cảm biến nhiệt độ / độ ẩm</span>
                <span class="pill">DHT11</span>
              </div>
              <div class="card-main">
                <span class="sensor-emoji">🌡</span>
                <span id="temp-val-dashboard" class="sensor-value">--</span>
                <span class="sensor-unit">°C</span>

                <span style="margin-left:20px;"></span>

                <span class="sensor-emoji">💧</span>
                <span id="hum-val-dashboard" class="sensor-value">--</span>
                <span class="sensor-unit">%</span>
              </div>
              <div class="card-desc" id="sensor-desc-dashboard">
                Đang đọc dữ liệu...
              </div>
            </div>

            <!-- Hệ thống -->
            <div class="card">
              <div class="card-title">
                <span>Hệ thống</span>
                <span class="pill">ESP32</span>
              </div>
              <div class="card-main" id="sys-status">Đang cập nhật...</div>
              <div class="card-desc" id="sys-extra">IP: đang đọc...</div>
            </div>
          </div>
        </section>

        <!-- VIEW: CỬA RA VÀO -->
        <section id="view-door" class="view hidden">
          <h2 class="view-title">Cửa ra vào</h2>
          <div class="card">
            <div class="card-title">
              <span>Điều khiển cửa</span>
              <span class="pill">
                Trạng thái: <span id="door-state-text">Đang đóng</span>
              </span>
            </div>

            <div class="card-main">
              Mở/đóng cửa bằng servo.
            </div>
            <div class="card-desc">
              Sử dụng nút hoặc kéo thanh trượt để đặt góc (0°–180°).
            </div>

            <!-- Nút mở / đóng nhanh -->
            <div class="btn-row" style="margin-top:8px;">
              <button class="btn btn-primary" onclick="gateOpen()">Mở cửa</button>
              <button class="btn btn-danger" onclick="gateClose()">Đóng cửa</button>
            </div>

            <!-- Thanh trượt góc servo -->
            <div style="margin-top:16px;">
              <label for="servo-slider" class="card-desc">
                Góc servo hiện tại:
                <strong><span id="servo-angle-text">0</span>°</strong>
              </label>
              <input
                id="servo-slider"
                type="range"
                min="0"
                max="180"
                value="0"
                oninput="onServoSliderChange(this.value)"
                style="width:100%; margin-top:8px;"
              />
              <div style="margin-top:4px; font-size:0.85rem;">
                Góc đang chọn: <span id="servo-slider-value">0</span>°
              </div>
            </div>
          </div>
        </section>

        <!-- VIEW: ĐÈN CHIẾU SÁNG -->
        <section id="view-lights" class="view hidden">
          <h2 class="view-title">Đèn chiếu sáng</h2>
          <div class="card">
            <div class="card-title">
              <span>Điều khiển đèn</span>
              <span class="pill">5 kênh LED</span>
            </div>
            <div class="card-main">
              Nút gạt bật/tắt đèn.
            </div>
            <div class="switch-row">
              <div class="switch" data-led="1" onclick="toggleLed(this)">
                <span class="switch-label">PHÒNG KHÁCH</span>
                <div class="switch-track"><div class="switch-thumb"></div></div>
              </div>
              <div class="switch" data-led="2" onclick="toggleLed(this)">
                <span class="switch-label">PHÒNG NGỦ</span>
                <div class="switch-track"><div class="switch-thumb"></div></div>
              </div>
              <div class="switch" data-led="3" onclick="toggleLed(this)">
                <span class="switch-label">NHÀ BẾP</span>
                <div class="switch-track"><div class="switch-thumb"></div></div>
              </div>
              <div class="switch" data-led="4" onclick="toggleLed(this)">
                <span class="switch-label">NHÀ VỆ SINH</span>
                <div class="switch-track"><div class="switch-thumb"></div></div>
              </div>
              <div class="switch" data-led="5" onclick="toggleLed(this)">
                <span class="switch-label">PHÒNG LÀM VIỆC</span>
                <div class="switch-track"><div class="switch-thumb"></div></div>
              </div>
            </div>
          </div>
        </section>

        <!-- VIEW: CẢM BIẾN -->
        <section id="view-sensor" class="view hidden">
          <h2 class="view-title">Cảm biến</h2>
          <div class="card">
            <div class="card-title">
              <span>Nhiệt độ & độ ẩm</span>
              <span class="pill">DHT11</span>
            </div>
            <div class="card-main">
              <div style="margin-bottom:8px;">
                <span class="sensor-emoji">🌡</span>
                <span id="temp-val-detail" class="sensor-value">--</span>
                <span class="sensor-unit">°C</span>
              </div>
              <div>
                <span class="sensor-emoji">💧</span>
                <span id="hum-val-detail" class="sensor-value">--</span>
                <span class="sensor-unit">%</span>
              </div>
            </div>
            <div class="card-desc" id="sensor-desc-detail">
              Đang đọc dữ liệu...
            </div>
          </div>
        </section>

      </main>
    </div>
  </div>

  <script>
    function showView(name) {
      var views = document.querySelectorAll(".view");
      for (var i = 0; i < views.length; i++) {
        views[i].style.display = "none";
      }
      var v = document.getElementById("view-" + name);
      if (v) v.style.display = "block";

      var items = document.querySelectorAll(".nav-item");
      for (var j = 0; j < items.length; j++) {
        items[j].classList.remove("active");
      }
      var current = null;
      for (var k = 0; k < items.length; k++) {
        var onclick = items[k].getAttribute("onclick") || "";
        if (onclick.indexOf("'" + name + "'") !== -1) {
          current = items[k];
          break;
        }
      }
      if (current) current.classList.add("active");
    }

    function led(idx, state) {
      var url = "";
      if (idx == 1) url = state ? "/on1" : "/off1";
      else if (idx == 2) url = state ? "/on2" : "/off2";
      else if (idx == 3) url = state ? "/on3" : "/off3";
      else if (idx == 4) url = state ? "/on4" : "/off4";
      else if (idx == 5) url = state ? "/on5" : "/off5";
      if (!url) return;
      fetch(url).catch(function(e){ console.log(e); });
    }

    function toggleLed(el) {
      var idx = parseInt(el.getAttribute("data-led"));
      if (!idx) return;
      var isOn = el.classList.contains("on");
      var newState = isOn ? 0 : 1;
      led(idx, newState);
    }

    function gateOpen() {
      fetch("/gate_open")
        .then(function(){
          var t = document.getElementById("door-state-text");
          if (t) t.innerText = "Đang mở";
        })
        .catch(function(e){ console.log(e); });
    }

    function gateClose() {
      fetch("/gate_close")
        .then(function(){
          var t = document.getElementById("door-state-text");
          if (t) t.innerText = "Đang đóng";
        })
        .catch(function(e){ console.log(e); });
    }

    function onServoSliderChange(val) {
      // cập nhật số bên cạnh thanh trượt
      var sliderVal = document.getElementById("servo-slider-value");
      if (sliderVal) sliderVal.innerText = val;

      // gửi lệnh lên ESP32
      fetch("/gate_angle?val=" + encodeURIComponent(val))
        .catch(function(e){ console.log(e); });
    }

    async function refreshStatus() {
      try {
        const res = await fetch("/api/status");
        if (!res.ok) throw new Error("Status HTTP error");
        const data = await res.json();

        // ----- WiFi badge -----
        const wifiBadge = document.getElementById("wifi-badge");
        if (wifiBadge) {
          if (data.wifi == 1) {
            wifiBadge.classList.remove("offline");
            wifiBadge.classList.add("online");
            wifiBadge.innerText = "WiFi: Online";
          } else {
            wifiBadge.classList.remove("online");
            wifiBadge.classList.add("offline");
            wifiBadge.innerText = "WiFi: Offline";
          }
        }

        // ----- Cửa -----
        const doorOpen = data.door_open == 1;
        const doorTextDash = document.getElementById("door-state-text-dashboard");
        const doorPill = document.getElementById("door-state-pill");
        const doorStateText = doorOpen ? "Đang mở" : "Đang đóng";

        if (doorTextDash) doorTextDash.innerText = "Cửa " + (doorOpen ? "đang mở" : "đang đóng");
        if (doorPill) doorPill.innerText = doorStateText;

        const doorText = document.getElementById("door-state-text");
        if (doorText) doorText.innerText = doorStateText;

        // ----- Servo angle (góc cửa) -----
        var angle = (data.servo_angle != null) ? data.servo_angle : 0;
        var angleText = document.getElementById("servo-angle-text");
        var slider = document.getElementById("servo-slider");
        var sliderValue = document.getElementById("servo-slider-value");

        if (angleText) angleText.innerText = angle;
        if (slider) slider.value = angle;
        if (sliderValue) sliderValue.innerText = angle;

        // ----- LED trạng thái tổng quát -----
        const leds = [data.led1, data.led2, data.led3, data.led4, data.led5];
        const onCount = leds.filter(function(x){ return x == 1; }).length;
        const lightsSummary = document.getElementById("lights-summary");
        if (lightsSummary) {
          lightsSummary.innerText = onCount === 0
            ? "Tất cả đèn đang tắt"
            : onCount + " đèn đang bật";
        }

        // Cập nhật switch theo state thật
        const switches = document.querySelectorAll(".switch");
        switches.forEach(function(sw){
          const idx = parseInt(sw.getAttribute("data-led"));
          if (!idx) return;
          const st = leds[idx - 1];
          if (st == 1) sw.classList.add("on");
          else sw.classList.remove("on");
        });

        // ----- Trạng thái chi tiết từng đèn trên Dashboard -----
        for (var i = 0; i < leds.length; i++) {
          var st = leds[i];
          var item = document.getElementById("light-item-" + (i + 1));
          var textEl = document.getElementById("light-status-" + (i + 1));
          if (item) {
            if (st == 1) item.classList.add("on");
            else item.classList.remove("on");
          }
          if (textEl) {
            textEl.innerText = (st == 1) ? "Đang bật" : "Đang tắt";
          }
        }

        // ----- Nhiệt độ + độ ẩm -----
        const t = data.temp_c;
        const h = data.hum;

        const tempDash = document.getElementById("temp-val-dashboard");
        const humDash = document.getElementById("hum-val-dashboard");
        const tempDetail = document.getElementById("temp-val-detail");
        const humDetail = document.getElementById("hum-val-detail");

        if (tempDash)   tempDash.innerText   = (t != null) ? t.toFixed(1) : "--";
        if (tempDetail) tempDetail.innerText = (t != null) ? t.toFixed(1) : "--";
        if (humDash)    humDash.innerText    = (h != null) ? h.toFixed(1) : "--";
        if (humDetail)  humDetail.innerText  = (h != null) ? h.toFixed(1) : "--";

        const sensorDescDash = document.getElementById("sensor-desc-dashboard");
        const sensorDescDetail = document.getElementById("sensor-desc-detail");
        const ok = (t != null) && (h != null);
        const msg = ok ? "Nhiệt độ & độ ẩm hiện tại." : "Không đọc được dữ liệu DHT11.";
        if (sensorDescDash) sensorDescDash.innerText = msg;
        if (sensorDescDetail) sensorDescDetail.innerText = msg;

        // ----- Hệ thống -----
        const statusText = data.wifi ? "Hệ thống hoạt động" : "WiFi chưa kết nối";
        const ipText = "IP: " + (data.ip || "N/A");
        const sysStatus = document.getElementById("sys-status");
        const sysExtra = document.getElementById("sys-extra");
        if (sysStatus) sysStatus.innerText = statusText;
        if (sysExtra)  sysExtra.innerText  = ipText;

      } catch (e) {
        console.log(e);
      }
    }

    setInterval(refreshStatus, 2000);
    refreshStatus();
    // đảm bảo lúc load lên đang ở dashboard
    showView('dashboard');
  </script>
</body>
</html>
)rawliteral";

float readTemperatureC() {
  float t = dht.readTemperature();   // đọc nhiệt độ (°C – degree Celsius)
  if (isnan(t)) return NAN;
  return t;
}

float readHumidity() {
  float h = dht.readHumidity();      // đọc độ ẩm (% – humidity)
  if (isnan(h)) return NAN;
  return h;
}

// Cập nhật cả nhiệt độ lẫn độ ẩm định kỳ
void updateTemperature() {
  float t = readTemperatureC();
  float h = readHumidity();

  if (!isnan(t)) {
    currentTempC = t;
  }
  if (!isnan(h)) {
    currentHum = h;
  }

  Serial.printf("DHT11 -> Temp: %.1f C, Hum: %.1f %%\n", currentTempC, currentHum);
}

// ====== FIREBASE FUNCTIONS ======
void initFirebase() {
  Serial.println("Initializing Firebase...");
  
  // Cấu hình Firebase
  config.host = FIREBASE_HOST;
  config.signer.tokens.legacy_token = FIREBASE_AUTH;
  
  // Khởi tạo Firebase
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  
  Serial.println("Firebase initialized!");
}

void syncStateToFirebase() {
  if (!Firebase.ready()) return;
  
  // Tạo JSON object
  FirebaseJson json;
  json.set("led1", led1State ? 1 : 0);
  json.set("led2", led2State ? 1 : 0);
  json.set("led3", led3State ? 1 : 0);
  json.set("led4", led4State ? 1 : 0);
  json.set("led5", led5State ? 1 : 0);
  json.set("door_open", doorOpen ? 1 : 0);
  json.set("servo_angle", servoAngle);
  
  // Thêm sensor data
  if (!isnan(currentTempC)) {
    json.set("temp_c", currentTempC);
  }
  if (!isnan(currentHum)) {
    json.set("hum", currentHum);
  }
  
  // Thêm trạng thái WiFi và IP để web biết ESP32 online
  json.set("wifi", 1);
  json.set("ip", WiFi.localIP().toString());
  
  // Gửi lên Firebase
  if (Firebase.RTDB.updateNode(&fbdo, FB_BASE_PATH, &json)) {
    Serial.println("✅ Synced to Firebase");
  } else {
    Serial.println("❌ Firebase sync failed: " + fbdo.errorReason());
  }
}

void checkFirebaseCommands() {
  if (!Firebase.ready()) return;
  
  // Đọc lệnh từ Firebase /esp32_1/cmd
  String cmdPath = String(FB_BASE_PATH) + "/cmd";
  
  if (Firebase.RTDB.getJSON(&fbdo, cmdPath)) {
    FirebaseJson &json = fbdo.jsonObject();
    FirebaseJsonData jsonData;
    
    // Kiểm tra lệnh LED
    for (int i = 1; i <= 5; i++) {
      String ledKey = "led" + String(i);
      if (json.get(jsonData, ledKey)) {
        int value = jsonData.intValue;
        switch(i) {
          case 1: digitalWrite(led1, value); led1State = value; break;
          case 2: digitalWrite(led2, value); led2State = value; break;
          case 3: digitalWrite(led3, value); led3State = value; break;
          case 4: digitalWrite(led4, value); led4State = value; break;
          case 5: digitalWrite(led5, value); led5State = value; break;
        }
        Serial.printf("LED%d = %d\n", i, value);
      }
    }
    
    // Kiểm tra lệnh servo/door
    if (json.get(jsonData, "servo_angle")) {
      servoAngle = jsonData.intValue;
      gateServo.write(servoAngle);
      doorOpen = (servoAngle >= (SERVO_OPENED_ANGLE / 2));
      Serial.printf("Servo angle = %d\n", servoAngle);
    }
    
    // Xóa lệnh sau khi xử lý
    Firebase.RTDB.deleteNode(&fbdo, cmdPath);
    
    // Sync lại trạng thái
    syncStateToFirebase();
  }
}



// ====== ROUTE CHO DASHBOARD ======

// Trả về HTML dashboard
void handleDashboardPage() {
  webServer.send_P(200, "text/html", DASHBOARD_HTML);
}

// Trả về JSON trạng thái (WiFi, IP, cửa, nhiệt, 5 đèn)
void handleStatusApi() {
  float t = currentTempC;
  float h = currentHum;
  int wifi_ok = (WiFi.status() == WL_CONNECTED) ? 1 : 0;
  String ipStr = WiFi.localIP().toString();

  String json = "{";
  json += "\"wifi\":" + String(wifi_ok) + ",";
  json += "\"ip\":\"" + ipStr + "\",";
  json += "\"door_open\":" + String(doorOpen ? 1 : 0) + ",";
  json += "\"servo_angle\":" + String(servoAngle) + ",";   // thêm góc servo
  json += "\"led1\":" + String(led1State ? 1 : 0) + ",";
  json += "\"led2\":" + String(led2State ? 1 : 0) + ",";
  json += "\"led3\":" + String(led3State ? 1 : 0) + ",";
  json += "\"led4\":" + String(led4State ? 1 : 0) + ",";
  json += "\"led5\":" + String(led5State ? 1 : 0) + ",";

  if (!isnan(t)) json += "\"temp_c\":" + String(t, 1) + ",";
  else           json += "\"temp_c\":null,";

  if (!isnan(h)) json += "\"hum\":" + String(h, 1);
  else           json += "\"hum\":null";

  json += "}";

  webServer.send(200, "application/json", json);
}

// Điều khiển cửa bằng web
void handleGateOpen() {
  servoAngle = SERVO_OPENED_ANGLE;
  gateServo.write(servoAngle);
  doorOpen = true;
  webServer.send(200, "text/plain", "Gate opened");
}

void handleGateClose() {
  servoAngle = SERVO_CLOSED_ANGLE;
  gateServo.write(servoAngle);
  doorOpen = false;
  webServer.send(200, "text/plain", "Gate closed");
}

// ==========================================================
// ======================== SETUP ===========================
// ==========================================================
void setup() {
  Serial.begin(115200);
  wifiConfig.begin();

  // route web
  webServer.on("/dashboard", handleDashboardPage);
  webServer.on("/api/status", handleStatusApi);
  webServer.on("/gate_open", handleGateOpen);
  webServer.on("/gate_close", handleGateClose);
  webServer.on("/gate_angle", handleGateAngle);

  pinMode(led1,OUTPUT);
  pinMode(led2,OUTPUT);
  pinMode(led3,OUTPUT);
  pinMode(led4,OUTPUT);
  pinMode(led5,OUTPUT);

  dht.begin();

  gateServo.setPeriodHertz(50);
  gateServo.attach(SERVO_PIN,500,2400);
  gateServo.write(SERVO_CLOSED_ANGLE);

  // khởi tạo lần đọc nhiệt độ đầu tiên
  lastTempRead = millis();

  Serial.println("ESP32 Server started!");
}
// ==========================================================
// ========================= LOOP ===========================
// ==========================================================
void loop() {
  // WiFi config + web local
  wifiConfig.run();

  // In IP đúng một lần và khởi tạo Firebase
  static bool ipShown = false;
  if (!ipShown && WiFi.status() == WL_CONNECTED) {
    Serial.print("ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
    ipShown = true;
    
    // Khởi tạo Firebase sau khi kết nối WiFi
    initFirebase();
  }

  // Đọc nhiệt độ / độ ẩm (DHT11) mỗi 2 giây
  if (millis() - lastTempRead >= 2000) {
    lastTempRead = millis();
    updateTemperature();
  }

  // --- Firebase sync (đồng bộ Firebase) ---
  static unsigned long lastStatePush = 0;
  static unsigned long lastCmdPull   = 0;
  unsigned long now = millis();

  // 1) 5 giây đẩy trạng thái lên Firebase 1 lần
  if (now - lastStatePush >= 5000) {
    lastStatePush = now;
    syncStateToFirebase();
  }

  // 2) 1 giây đọc lệnh Firebase 1 lần
  if (now - lastCmdPull >= 1000) {
    lastCmdPull = now;
    checkFirebaseCommands();
  }
}


