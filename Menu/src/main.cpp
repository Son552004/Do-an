#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <Keypad.h>
#include <WiFiManager.h>
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <qrcode.h>
#include <WiFi.h>

// Khai báo prototype của các hàm
void displayQRCode();
void updateDisplay();
void sendOrder();
void connectToWiFi();
void checkResetButton();

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 128
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

// Cấu hình bàn phím ma trận 4x4
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

byte rowPins[ROWS] = {32, 33, 25, 26};
byte colPins[COLS] = {27, 14, 12, 13};

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);
Adafruit_SH1107 display = Adafruit_SH1107(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Cấu trúc lưu trữ thông tin món ăn
struct OrderItem {
  String dish;
  String size;
  String quantity;
};

// Vector lưu trữ các món trong đơn hàng
const int MAX_ITEMS = 10;
OrderItem orderItems[MAX_ITEMS];
int currentItemIndex = 0;

// Hàm kiểm tra và gộp món trùng
int findMatchingItem(const String& dish, const String& size) {
  for(int i = 0; i <= currentItemIndex; i++) {
    if(orderItems[i].dish == dish && orderItems[i].size == size) {
      return i;
    }
  }
  return -1;
}

// Biến trạng thái menu
enum MenuState {
  SELECT_DISH,
  SELECT_SIZE,
  SELECT_QUANTITY,
  CONFIRM_ORDER,
  SHOW_QR_CODE,
  ADD_MORE_ITEMS  // Thêm trạng thái mới
};

MenuState currentState = SELECT_DISH;
String selectedDish = "";
String selectedSize = "";
String selectedQuantity = "";
String orderDetails = "";
String tempNumber = "";  // Thêm biến để lưu số tạm thời

// Biến lưu trữ mã QR chuỗi nhận từ server
String qrCodeString = "";
bool hasQrCode = false;

// Tạo web server
AsyncWebServer server(80);

// Cấu hình WiFi
const char* SERVER_URL = "http://192.168.1.104:5000/order"; // Cập nhật IP của máy tính

// Biến lưu trữ trạng thái WiFi
bool wifiConnected = false;
WiFiManager wifiManager;

// Cấu hình IP tĩnh
IPAddress local_IP(192, 168, 1, 50);      // Địa chỉ IP tĩnh mong muốn
IPAddress gateway(192, 168, 1, 1);        // Gateway của mạng
IPAddress subnet(255, 255, 255, 0);       // Subnet mask
IPAddress primaryDNS(8, 8, 8, 8);         // DNS chính (tùy chọn)
IPAddress secondaryDNS(8, 8, 4, 4);       // DNS phụ (tùy chọn)

// Chân nút boot
const int BOOT_BUTTON = 0;

// Hàm kiểm tra nút boot
void checkResetButton() {
  if (digitalRead(BOOT_BUTTON) == LOW) {
    Serial.println("Nhan nut boot - Reset WiFi");
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("Reset WiFi...");
    display.display();
    delay(1000);
    
    // Xóa cấu hình WiFi đã lưu
    wifiManager.resetSettings();
    
    // Khởi động lại ESP32
    ESP.restart();
  }
}

// Hàm kết nối WiFi
void connectToWiFi() {
  // Cấu hình WiFiManager
  wifiManager.setConfigPortalTimeout(180); // Timeout 3 phút
  wifiManager.setMinimumSignalQuality(30); // Chất lượng tín hiệu tối thiểu
  
  // Hiển thị thông báo đang kết nối
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Dang ket noi WiFi...");
  display.display();
  
  // Thử kết nối WiFi
  if(!wifiManager.autoConnect("ESP32_Config")) {
    Serial.println("Khong the ket noi WiFi");
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("Ket noi WiFi that bai!");
    display.println("Khoi dong lai...");
    display.display();
    delay(2000);
    ESP.restart();
  }
  
  wifiConnected = true;
  Serial.println("Ket noi WiFi thanh cong!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Ket noi WiFi OK");
  display.println("IP: " + WiFi.localIP().toString());
  display.display();
  delay(2000);
}

// Hàm hiển thị QR code
void displayQRCode() {
  if (!hasQrCode) {
    Serial.println("Khong co chuoi QR de hien thi!");
    return;
  }
  Serial.print("Tao QR code cho chuoi: ");
  Serial.println(qrCodeString);
  QRCode qrcode;
  uint8_t qrcodeData[qrcode_getBufferSize(4)];
  qrcode_initText(&qrcode, qrcodeData, 4, 0, qrCodeString.c_str());
  int maxSize = min(SCREEN_WIDTH, SCREEN_HEIGHT) - 2;
  int scale = maxSize / qrcode.size;
  scale = min(scale, 4);
  int qrSize = qrcode.size * scale;
  int xOffset = (SCREEN_WIDTH - qrSize) / 2;
  int yOffset = (SCREEN_HEIGHT - qrSize) / 2;
  display.clearDisplay();
  display.drawRect(xOffset - 1, yOffset - 1, qrSize + 2, qrSize + 2, SH110X_WHITE);
  for (uint8_t y = 0; y < qrcode.size; y++) {
    for (uint8_t x = 0; x < qrcode.size; x++) {
      if (qrcode_getModule(&qrcode, x, y)) {
        display.fillRect(
          xOffset + x * scale, 
          yOffset + y * scale, 
          scale, 
          scale, 
          SH110X_WHITE
        );
      }
    }
  }
  display.display();
  Serial.println("Da hien thi QR code");
}

// Hàm hiển thị menu
void updateDisplay() {
  display.clearDisplay();
  display.setCursor(0,0);
  
  switch(currentState) {
    case SELECT_DISH:
      display.println("Chon mon an (1-99)");
      display.println("Nhan A de xac nhan");
      display.println("Mon da chon: " + selectedDish);
      break;
      
    case SELECT_SIZE:
      display.println("Chon size (1-3)");
      display.println("Nhan A de xac nhan");
      display.println("Size da chon: " + selectedSize);
      break;
      
    case SELECT_QUANTITY:
      display.println("Chon so luong (1-3)");
      display.println("Nhan A de xac nhan");
      display.println("So luong: " + selectedQuantity);
      break;
      
    case ADD_MORE_ITEMS:
      display.println("Them mon khac?");
      display.println("A: Them mon");
      display.println("B: Xac nhan don");
      display.println("C: Huy don");
      break;
      
    case CONFIRM_ORDER:
      display.println("Chi tiet don hang:");
      for(int i = 0; i <= currentItemIndex; i++) {
        display.print("Mon ");
        display.print(orderItems[i].dish);
        display.print(" Size ");
        display.print(orderItems[i].size);
        display.print(" SL ");
        display.println(orderItems[i].quantity);
      }
      display.println("Nhan A de gui");
      display.println("Nhan B de huy");
      break;
      
    case SHOW_QR_CODE:
      display.println("QR Code da hien thi");
      display.println("Nhan C de quay lai menu");
      break;
  }
  
  display.display();
}

// Hàm gửi đơn hàng qua WiFi
void sendOrder() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    StaticJsonDocument<1024> doc;
    JsonArray items = doc.createNestedArray("items");
    for(int i = 0; i <= currentItemIndex; i++) {
      if(orderItems[i].dish != "" && orderItems[i].size != "" && orderItems[i].quantity != "") {
        JsonObject item = items.createNestedObject();
        item["dish"] = orderItems[i].dish;
        item["size"] = orderItems[i].size;
        item["quantity"] = orderItems[i].quantity;
      }
    }
    String jsonString;
    serializeJson(doc, jsonString);
    
    Serial.println("\n=== Thong tin gui don hang ===");
    Serial.println("URL: " + String(SERVER_URL));
    Serial.println("JSON: " + jsonString);
    Serial.println("WiFi RSSI: " + String(WiFi.RSSI()));
    Serial.println("IP ESP32: " + WiFi.localIP().toString());
    Serial.println("===========================\n");
    
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    
    // Tăng thời gian timeout lên 30 giây
    http.setTimeout(30000);
    
    int httpCode = http.POST(jsonString);
    
    if (httpCode > 0) {
      String response = http.getString();
      Serial.println("Phan hoi tu server:");
      Serial.println(response);
      
      StaticJsonDocument<1024> responseDoc;
      DeserializationError error = deserializeJson(responseDoc, response);
      
      if (!error) {
        if (responseDoc["status"] == "success") {
          if (responseDoc.containsKey("qr_code") && responseDoc["qr_code"].is<String>()) {
            qrCodeString = responseDoc["qr_code"].as<String>();
            Serial.println("Nhan duoc chuoi QR:");
            Serial.println(qrCodeString);
            
            if (qrCodeString.length() > 10) {
              hasQrCode = true;
              currentState = SHOW_QR_CODE;
              display.clearDisplay();
              display.setCursor(0,0);
              display.println("Dang tao QR code...");
              display.display();
              delay(1000);
            } else {
              Serial.println("Chuoi QR khong hop le (qua ngan)");
              display.clearDisplay();
              display.setCursor(0,0);
              display.println("Loi: QR khong hop le");
              display.println("Thu lai sau...");
              display.display();
              delay(2000);
              currentState = SELECT_DISH;
            }
          } else {
            Serial.println("Khong tim thay chuoi QR trong response");
            display.clearDisplay();
            display.setCursor(0,0);
            display.println("Loi: Khong co QR");
            display.println("Thu lai sau...");
            display.display();
            delay(2000);
            currentState = SELECT_DISH;
          }
        } else {
          Serial.println("\n=== Thong tin loi ===");
          Serial.println("Status: " + String(responseDoc["status"].as<const char*>()));
          Serial.println("Message: " + String(responseDoc["message"].as<const char*>()));
          Serial.println("=====================\n");
          display.clearDisplay();
          display.setCursor(0,0);
          display.println("Loi gui don hang!");
          display.println(responseDoc["message"].as<const char*>());
          display.println("Thu lai sau...");
          display.display();
          delay(2000);
          currentState = SELECT_DISH;
        }
      } else {
        Serial.println("Loi parse JSON: " + String(error.c_str()));
        display.clearDisplay();
        display.setCursor(0,0);
        display.println("Loi nhan du lieu!");
        display.println(error.c_str());
        display.println("Thu lai sau...");
        display.display();
        delay(2000);
        currentState = SELECT_DISH;
      }
    } else {
      Serial.println("\n=== Thong tin loi ===");
      Serial.println("HTTP Code: " + String(httpCode));
      Serial.println("Error: " + http.errorToString(httpCode));
      Serial.println("URL: " + String(SERVER_URL));
      Serial.println("WiFi RSSI: " + String(WiFi.RSSI()));
      Serial.println("IP ESP32: " + WiFi.localIP().toString());
      Serial.println("=====================\n");
      display.clearDisplay();
      display.setCursor(0,0);
      display.println("Loi gui don hang!");
      display.println("HTTP Code: " + String(httpCode));
      display.println("IP ESP32: " + WiFi.localIP().toString());
      display.println("Thu lai sau...");
      display.display();
      delay(2000);
      currentState = SELECT_DISH;
    }
    http.end();
  } else {
    Serial.println("Khong ket noi duoc WiFi");
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("Mat ket noi WiFi!");
    display.println("Dang ket noi lai...");
    display.display();
    connectToWiFi();
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  
  // Cấu hình chân nút boot
  pinMode(BOOT_BUTTON, INPUT_PULLUP);
  
  // Khởi tạo màn hình
  if(!display.begin(SCREEN_ADDRESS)) {
    Serial.println(F("Khoi tao SH1107 that bai"));
    for(;;);
  }
  
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  
  // Hiển thị thông báo khởi động
  display.setCursor(0,0);
  display.println("Dang khoi dong...");
  display.display();
  
  // Kết nối WiFi
  connectToWiFi();
  
  // Cấu hình web server
  server.on("/order", HTTP_POST, [](AsyncWebServerRequest *request){
    request->send(200, "text/plain", "Order received");
  });
  
  server.begin();
  
  updateDisplay();
}

void loop() {
  // Kiểm tra nút boot
  checkResetButton();
  
  char key = keypad.getKey();
  
  if (key) {
    switch(currentState) {
      case SELECT_DISH:
        if (key >= '1' && key <= '9') {
          tempNumber += key;
          if (tempNumber.length() <= 2) {  // Cho phép nhập tối đa 2 chữ số
            selectedDish = tempNumber;
            updateDisplay();
          }
        } else if (key == 'A' && selectedDish != "") {
          tempNumber = "";  // Reset biến tạm
          currentState = SELECT_SIZE;
          updateDisplay();
        } else if (key == 'B') {  // Thêm phím B để xóa số
          tempNumber = "";
          selectedDish = "";
          updateDisplay();
        }
        break;
        
      case SELECT_SIZE:
        if (key >= '1' && key <= '3') {
          selectedSize = String(key);
          updateDisplay();
        } else if (key == 'A' && selectedSize != "") {
          currentState = SELECT_QUANTITY;
          updateDisplay();
        }
        break;
        
      case SELECT_QUANTITY:
        if (key >= '1' && key <= '3') {
          selectedQuantity = String(key);
          updateDisplay();
        } else if (key == 'A' && selectedQuantity != "") {
          // Kiểm tra món trùng
          int matchingIndex = findMatchingItem(selectedDish, selectedSize);
          
          if(matchingIndex != -1) {
            // Nếu tìm thấy món trùng, cộng thêm số lượng
            int newQuantity = orderItems[matchingIndex].quantity.toInt() + selectedQuantity.toInt();
            if(newQuantity > 9) newQuantity = 9; // Giới hạn số lượng tối đa là 9
            orderItems[matchingIndex].quantity = String(newQuantity);
          } else {
            // Nếu không có món trùng, thêm món mới
            if(currentItemIndex < MAX_ITEMS - 1) {
              orderItems[currentItemIndex].dish = selectedDish;
              orderItems[currentItemIndex].size = selectedSize;
              orderItems[currentItemIndex].quantity = selectedQuantity;
              currentItemIndex++;
            }
          }
          
          // Reset các biến chọn
          selectedDish = "";
          selectedSize = "";
          selectedQuantity = "";
          
          // Chuyển sang trạng thái thêm món
          currentState = ADD_MORE_ITEMS;
          updateDisplay();
        }
        break;
        
      case ADD_MORE_ITEMS:
        if (key == 'A') {
          if (currentItemIndex < MAX_ITEMS - 1) {
            currentItemIndex++;
            currentState = SELECT_DISH;
          }
          updateDisplay();
        } else if (key == 'B') {
          currentState = CONFIRM_ORDER;
          updateDisplay();
        } else if (key == 'C') {
          // Reset đơn hàng
          currentItemIndex = 0;
          currentState = SELECT_DISH;
          updateDisplay();
        }
        break;
        
      case CONFIRM_ORDER:
        if (key == 'A') {
          sendOrder();
        } else if (key == 'B') {
          // Reset đơn hàng
          currentItemIndex = 0;
          currentState = SELECT_DISH;
          updateDisplay();
        }
        break;

      case SHOW_QR_CODE:
        if (key == 'C') {
          currentItemIndex = 0;
          currentState = SELECT_DISH;
          selectedDish = "";
          selectedSize = "";
          selectedQuantity = "";
          hasQrCode = false;
          qrCodeString = "";
          updateDisplay();
        }
        break;
    }
  }
  
  // Xử lý hiển thị QR code trong trạng thái SHOW_QR_CODE
  if (currentState == SHOW_QR_CODE && hasQrCode) {
    Serial.println("Dang hien thi QR code...");
    Serial.println("Chuoi QR: " + qrCodeString);
    
    QRCode qrcode;
    uint8_t qrcodeData[qrcode_getBufferSize(4)];
    
    // Kiểm tra chuỗi QR trước khi tạo
    if (qrCodeString.length() > 10) {
      qrcode_initText(&qrcode, qrcodeData, 4, 0, qrCodeString.c_str());
      
      int maxSize = min(SCREEN_WIDTH, SCREEN_HEIGHT) - 2;
      int scale = maxSize / qrcode.size;
      scale = min(scale, 4);
      int qrSize = qrcode.size * scale;
      int xOffset = (SCREEN_WIDTH - qrSize) / 2;
      int yOffset = (SCREEN_HEIGHT - qrSize) / 2;
      
      display.clearDisplay();
      display.drawRect(xOffset - 1, yOffset - 1, qrSize + 2, qrSize + 2, SH110X_WHITE);
      
      for (uint8_t y = 0; y < qrcode.size; y++) {
        for (uint8_t x = 0; x < qrcode.size; x++) {
          if (qrcode_getModule(&qrcode, x, y)) {
            display.fillRect(
              xOffset + x * scale, 
              yOffset + y * scale, 
              scale, 
              scale, 
              SH110X_WHITE
            );
          }
        }
      }
      display.display();
      Serial.println("Da hien thi QR code");
    } else {
      Serial.println("Chuoi QR khong hop le (qua ngan)");
      display.clearDisplay();
      display.setCursor(0,0);
      display.println("Loi: QR khong hop le");
      display.display();
    }
  }
  
  delay(50);
}