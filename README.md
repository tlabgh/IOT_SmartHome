# 🏠 IOT Smart Home - Hệ thống nhà thông minh với Voice Assistant AI

Đồ án IoT: Hệ thống nhà thông minh điều khiển bằng giọng nói sử dụng ESP32, Firebase và AI.

## 📋 Mô tả dự án

Dự án kết hợp:
- **Hardware**: ESP32 điều khiển thiết bị thông minh (5 LED, servo cửa, cảm biến DHT11)
- **AI Voice Assistant**: Trợ lý giọng nói tiếng Việt sử dụng SVM + TF-IDF
- **Cloud**: Firebase Realtime Database + Firebase Authentication
- **Web Dashboard**: GitHub Pages + Firebase SDK
- **Tính năng**: Điều khiển giọng nói, web remote, local dashboard, đọc cảm biến thời gian thực

## 🏗️ Cấu trúc dự án

```
IOT_SmartHome/
├── ESP32_Code/              # Firmware cho ESP32
│   ├── platformio.ini       # PlatformIO configuration
│   └── src/
│       └── ESP32_SmartHome.cpp  # Code chính ESP32
│
├── ESP32_TroLy/             # Voice Assistant AI
│   ├── voice_assistant.py   # Trợ lý giọng nói chính
│   ├── train_simple.py      # Training model SVM
│   ├── test_svm.py          # Test accuracy model
│   ├── test_comprehensive.py  # Test tổng hợp
│   ├── test_full_system.py   # Test toàn bộ hệ thống
│   ├── requirements.txt     # Python dependencies
│   ├── dataset/
│   │   └── intents.json     # Training data (18 intents)
│   └── models/
│       ├── intent_model.h5  # Trained SVM model
│       └── config.json      # Model configuration
│
├── docs/                    # Web Dashboard (GitHub Pages)
│   ├── index.html           # Web UI điều khiển
│   ├── app.js               # Firebase integration
│   └── config.js            # Firebase configuration
│
└── README.md                # File này
```

## 🌐 Web điều khiển từ xa (GitHub Pages)

Web dashboard remote được host tại **GitHub Pages** và tích hợp **Firebase Realtime Database + Firebase Authentication** để điều khiển ESP32 từ mọi nơi có internet.

### 🔑 Tính năng Web Dashboard:
- ✅ Đăng nhập bảo mật (Firebase Authentication)
- ✅ Điều khiển 5 LED (phòng khách, phòng ngủ, nhà bếp, nhà vệ sinh, phòng làm việc)
- ✅ Điều khiển cửa (mở/đóng servo)
- ✅ Hiển thị nhiệt độ & độ ẩm real-time
- ✅ Giao diện responsive, thân thiện mobile
- ✅ Dashboard tổng quan trạng thái thiết bị

### 📍 URL Public:
```
https://tlabgh.github.io/IOT_SmartHome/
```

### 🚀 Bật GitHub Pages (đã cấu hình)
1. Push code lên GitHub (repo: `https://github.com/tlabgh/IOT_SmartHome`)
2. Vào **Settings → Pages**
3. **Build and deployment**:
   - Source: **Deploy from a branch**
   - Branch: `master` (hoặc `main`)
   - Folder: `/docs`
4. Đợi 1–2 phút, GitHub sẽ deploy web

### 🔐 Cấu hình Firebase cho Web:
#### 1. Firebase Realtime Database:
- Database URL: `iot-smarthome-d03a9-default-rtdb.asia-southeast1.firebasedatabase.app`
- Region: `asia-southeast1` (Singapore)
- Database rules: Test mode (cho phép read/write)

#### 2. Firebase Authentication:
- Provider: Email/Password
- Authorized domains: Thêm `tlabgh.github.io` vào danh sách
- Tạo user trong Firebase Console → Authentication → Users

#### 3. Cấu hình trong code:
- File: `docs/config.js`
- Chứa: Firebase config (apiKey, authDomain, databaseURL, projectId, etc.)
- ESP32 base path: `/esp32_1`

### 🎯 Cách hoạt động:
1. **Web → Firebase**: User điều khiển trên web → ghi lệnh vào `/esp32_1/cmd`
2. **ESP32 → Firebase**: ESP32 đọc lệnh từ `/cmd` mỗi giây, thực thi, sau đó xóa lệnh
3. **ESP32 → Firebase**: ESP32 push trạng thái lên `/esp32_1` mỗi 5 giây
4. **Firebase → Web**: Web lắng nghe thay đổi real-time từ `/esp32_1`

### 📝 Lưu ý:
- Repo phải **public** để GitHub Pages hoạt động (hoặc nâng cấp GitHub Pro)
- Firebase API Key đã được thêm vào `docs/config.js`
- Cần thêm domain `tlabgh.github.io` vào Firebase Authorized domains


## 🚀 Hướng dẫn cài đặt

### 1️⃣ Setup ESP32

#### Yêu cầu:
- PlatformIO IDE (VS Code extension)
- ESP32 DevKit V1 (ESP-WROOM-32)
- Cáp USB type-C hoặc micro-USB
- Hardware:
  - 5x LED + resistor 220Ω
  - 1x Servo SG90
  - 1x DHT11 sensor
  - Breadboard & jumper wires

#### Kết nối Hardware:
| Thiết bị | ESP32 Pin | Ghi chú |
|----------|-----------|---------|
| LED 1 (Phòng khách) | GPIO 14 | Qua resistor 220Ω |
| LED 2 (Phòng ngủ) | GPIO 27 | Qua resistor 220Ω |
| LED 3 (Nhà bếp) | GPIO 26 | Qua resistor 220Ω |
| LED 4 (Nhà vệ sinh) | GPIO 25 | Qua resistor 220Ω |
| LED 5 (Phòng làm việc) | GPIO 33 | Qua resistor 220Ω |
| Servo (Cửa) | GPIO 32 | Signal pin |
| DHT11 Data | GPIO 4 | Data pin |
| DHT11 VCC | 3.3V | Power |
| DHT11 GND | GND | Ground |

#### Các bước upload code:
```powershell
cd ESP32_Code
pio run              # Compile code
pio run -t upload    # Upload lên ESP32
pio device monitor   # Xem serial output
```

#### Cấu hình WiFi lần đầu:
1. ESP32 sẽ tạo Access Point: `ESP32-XXXX` (XXXX là MAC address)
2. Kết nối vào AP này từ điện thoại/laptop
3. Mở trình duyệt: `http://192.168.4.1`
4. Scan và chọn SSID WiFi của bạn
5. Nhập password và Save
6. ESP32 sẽ restart và kết nối WiFi
7. Check IP address trong Serial Monitor

**⚡ IP Configuration:**
- Mặc định: **DHCP** (IP tự động từ router)
- Có thể config Static IP trong code (xem comment trong [ESP32_SmartHome.cpp](ESP32_Code/src/ESP32_SmartHome.cpp#L244-L251))

#### Local Dashboard:
Sau khi kết nối WiFi, truy cập:
```
http://<ESP32_IP>/dashboard
```
Dashboard cung cấp:
- 🏠 Tổng quan trạng thái thiết bị
- 💡 Điều khiển 5 LED (switch toggle)
- 🚪 Điều khiển cửa (open/close + slider góc servo 0-180°)
- 🌡️ Hiển thị nhiệt độ & độ ẩm real-time
- 📡 Trạng thái WiFi & IP

### 2️⃣ Setup Voice Assistant

#### Yêu cầu:
- Python 3.8+ (đã test với Python 3.11)
- Microphone (built-in hoặc external)
- PyAudio (cần Visual C++ Build Tools trên Windows)
- Internet (cho Google Speech Recognition & gTTS)

#### Các bước:
```powershell
cd ESP32_TroLy

# Tạo virtual environment (khuyến nghị)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Cài đặt dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Test model AI
python test_svm.py

# Chạy voice assistant
python voice_assistant.py <ESP32_IP>

# Ví dụ:
python voice_assistant.py 192.168.1.86
```

**Lưu ý Windows**: Nếu gặp lỗi PyAudio, cài đặt theo cách này:
```powershell
pip install pipwin
pipwin install pyaudio
```

#### Cách sử dụng Voice Assistant:
1. Chạy script → đợi thông báo "Đang lắng nghe..."
2. Nói lệnh tiếng Việt vào microphone
3. Đợi xử lý (nhận dạng → phân loại intent → gửi lệnh ESP32)
4. Nghe phản hồi giọng nói
5. Lặp lại từ bước 2

#### Test hệ thống:
```powershell
# Test accuracy model
python test_svm.py

# Test tổng hợp (tất cả intents)
python test_comprehensive.py

# Test full system (ESP32 + voice)
python test_full_system.py <ESP32_IP>
```

## 📡 API Endpoints (ESP32)

ESP32 cung cấp các REST API endpoints qua HTTP để điều khiển từ Voice Assistant hoặc các ứng dụng khác:

### 1. Điều khiển LED đơn lẻ (Sử dụng bởi Voice Assistant)
```http
GET http://<ESP32_IP>/on<số>    # Bật đèn
GET http://<ESP32_IP>/off<số>   # Tắt đèn
```
- `<số>`: 1-5 (LED1 đến LED5)
- Ví dụ:
  - `http://192.168.1.86/on1` → Bật đèn phòng khách
  - `http://192.168.1.86/off3` → Tắt đèn nhà bếp

**Mapping LED:**
- LED1 (GPIO 14): Phòng khách
- LED2 (GPIO 27): Phòng ngủ
- LED3 (GPIO 26): Nhà bếp
- LED4 (GPIO 25): Nhà vệ sinh
- LED5 (GPIO 33): Phòng làm việc

### 2. Điều khiển cửa (Servo)
```http
GET http://<ESP32_IP>/gate_open   # Mở cửa (servo 180°)
GET http://<ESP32_IP>/gate_close  # Đóng cửa (servo 0°)
GET http://<ESP32_IP>/gate_angle?val=90  # Đặt góc tùy ý (0-180°)
```

### 3. Dashboard & Status API
```http
GET http://<ESP32_IP>/dashboard    # Web UI dashboard
GET http://<ESP32_IP>/api/status   # JSON trạng thái hệ thống
```

**Response `/api/status`:**
```json
{
  "wifi": 1,
  "ip": "192.168.1.86",
  "door_open": 0,
  "servo_angle": 0,
  "led1": 1,
  "led2": 0,
  "led3": 1,
  "led4": 0,
  "led5": 0,
  "temp_c": 28.5,
  "hum": 65.2
}
```

### Test API với Python:
```python
import requests

ESP32_IP = "192.168.1.86"

# Bật đèn phòng khách
requests.get(f"http://{ESP32_IP}/on1")

# Đọc trạng thái
data = requests.get(f"http://{ESP32_IP}/api/status").json()
print(f"Nhiệt độ: {data['temp_c']}°C")
print(f"Độ ẩm: {data['hum']}%")
```

## 🔥 Firebase Integration

ESP32 tích hợp Firebase Realtime Database để đồng bộ trạng thái và nhận lệnh điều khiển từ xa:

### Cấu hình Firebase:
- **Database URL**: `iot-smarthome-d03a9-default-rtdb.asia-southeast1.firebasedatabase.app`
- **API Key**: `AIzaSyByP2XPL9NUEO33aYh7p3N67IeKjVG0YUA`
- **Base Path**: `/esp32_1`
- **Region**: asia-southeast1 (Singapore)

### Cách hoạt động:
1. **ESP32 → Firebase** (mỗi 5 giây):
   - Push trạng thái lên `/esp32_1`:
   ```json
   {
     "led1": 1,
     "led2": 0,
     "led3": 1,
     "led4": 0,
     "led5": 0,
     "door_open": 0,
     "servo_angle": 0,
     "temp_c": 28.5,
     "hum": 65.2,
     "wifi": 1,
     "ip": "192.168.1.86"
   }
   ```

2. **Web/App → Firebase** (khi người dùng điều khiển):
   - Ghi lệnh vào `/esp32_1/cmd`:
   ```json
   {
     "led1": 1,
     "servo_angle": 180
   }
   ```

3. **Firebase → ESP32** (mỗi 1 giây):
   - ESP32 đọc lệnh từ `/esp32_1/cmd`
   - Thực thi lệnh (bật đèn, xoay servo...)
   - Xóa lệnh sau khi thực thi
   - Push trạng thái mới lên Firebase

### Cấu hình trong code:
```cpp
// ESP32_Code/src/ESP32_SmartHome.cpp
#define FIREBASE_HOST "iot-smarthome-d03a9-default-rtdb.asia-southeast1.firebasedatabase.app"
#define FIREBASE_AUTH "AIzaSyByP2XPL9NUEO33aYh7p3N67IeKjVG0YUA"
#define FB_BASE_PATH  "/esp32_1"
```

```javascript
// docs/config.js
window.firebaseConfig = {
  apiKey: "AIzaSyByP2XPL9NUEO33aYh7p3N67IeKjVG0YUA",
  authDomain: "iot-smarthome-d03a9.firebaseapp.com",
  databaseURL: "https://iot-smarthome-d03a9-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "iot-smarthome-d03a9",
  // ...
};
window.espBasePath = "esp32_1";
```

## 🎤 Voice Commands (Tiếng Việt)

Voice Assistant hỗ trợ 18 intents + **Lệnh kép**:

### Lệnh đơn:
| Intent | Ví dụ lệnh |
|--------|------------|
| `turn_on_light` | "Bật đèn 1", "Mở đèn phòng khách" |
| `turn_off_light` | "Tắt đèn 2", "Tắt đèn phòng ngủ" |
| `turn_on_all` | "Bật tất cả đèn", "Mở hết đèn" |
| `turn_off_all` | "Tắt tất cả đèn", "Tắt hết" |
| `open_door` | "Mở cửa", "Mở cổng" |
| `close_door` | "Đóng cửa", "Khóa cửa" |
| `check_temperature` | "Nhiệt độ bao nhiêu", "Kiểm tra nhiệt độ" |
| `check_humidity` | "Độ ẩm thế nào", "Đo độ ẩm" |
| `greeting` | "Xin chào", "Hello" |
| `goodbye` | "Tạm biệt", "Bye" |

### 🔥 Lệnh kép (Mới!):
Điều khiển nhiều thiết bị cùng lúc bằng từ nối **"và"** hoặc **"với"**:

| Lệnh kép | Kết quả |
|----------|---------|
| "Bật đèn phòng ngủ và nhà vệ sinh" | Bật cả 2 đèn cùng lúc |
| "Tắt đèn phòng khách và phòng bếp" | Tắt cả 2 đèn |
| "Bật đèn nhà bếp với phòng làm việc" | Bật cả 2 đèn |
| "Mở cửa và bật đèn phòng khách" | Thực hiện 2 lệnh |

💡 *Trợ lý sẽ tự động tách và thực thi từng lệnh con!*

...và nhiều intent khác trong `intents.json`

## 🔧 Công nghệ sử dụng

### Hardware:
- **ESP32**: Vi điều khiển chính
- **DHT11**: Cảm biến nhiệt độ/độ ẩm
- **SG90 Servo**: Điều khiển cửa
- **Relay Module**: Điều khiển LED/thiết bị

### Software:
- **PlatformIO**: Framework phát triển ESP32
- **Arduino Framework**: Lập trình ESP32
- **Firebase**: Cloud database
- **Python**: Voice Assistant
- **SciKit-Learn**: Machine Learning (SVM)
- **SpeechRecognition**: Nhận dạng giọng nói
- **gTTS + Pygame**: Text-to-Speech

### AI Model:
- **SVM Classifier**: Phân loại intent
- **TF-IDF Vectorizer**: Vector hóa text
- **Underthesea**: Xử lý tiếng Việt

## 🎯 Tính năng nổi bật

✅ Điều khiển giọng nói tiếng Việt  
✅ Nhận dạng 18+ intent khác nhau  
✅ **Xử lý lệnh kép** - Điều khiển nhiều thiết bị cùng lúc  
✅ **Static IP cố định** - Không lo IP thay đổi  
✅ Phản hồi bằng giọng nói  
✅ Kết nối WiFi tự động  
✅ Firebase integration  
✅ Web interface cấu hình  
✅ Real-time sensor reading  
✅ Độ chính xác cao (~95%)  

## 📊 Kiến trúc hệ thống

```
┌──────────────────┐         HTTP REST API         ┌──────────────────┐
│  Voice Assistant │ ──────────────────────────►   │      ESP32       │
│     (Python)     │                                │    WebServer     │
│  SVM + TF-IDF    │ ◄──────────────────────────   │  (192.168.x.x)   │
└──────────────────┘      JSON Response            └──────────────────┘
         │                                                    │
         │                                                    │
         │          ┌─────────────────────┐                  │
         │          │  Firebase Realtime  │                  │
         └─────────►│     Database        │◄─────────────────┘
                    │  (Cloud Sync)       │
                    └─────────────────────┘
                              ▲
                              │
                              │
                    ┌─────────────────────┐
                    │   Web Dashboard     │
                    │  (GitHub Pages)     │
                    │  Firebase Auth      │
                    └─────────────────────┘

                    ┌──────────────────────┐
                    │   ESP32 Hardware     │
                    ├──────────────────────┤
                    │ • 5x LED (GPIO)      │
                    │ • 1x Servo (GPIO 32) │
                    │ • 1x DHT11 (GPIO 4)  │
                    │ • WiFi Module        │
                    └──────────────────────┘
```

### Luồng hoạt động:
1. **Local Control**: Voice Assistant → HTTP REST → ESP32 (trực tiếp)
2. **Remote Control**: Web Dashboard → Firebase → ESP32 (qua cloud)
3. **State Sync**: ESP32 → Firebase (mỗi 5s) → Web Dashboard (realtime)
4. **Sensor Data**: DHT11 → ESP32 → Firebase → Web/Voice (mỗi 2s đọc sensor)

## 🐛 Troubleshooting

### ESP32 không kết nối WiFi?
- ✅ Kiểm tra SSID/password trong AP config page
- ✅ Giữ nút BOOT (GPIO 0) 5 giây để reset WiFi
- ✅ Kết nối lại vào AP `ESP32-XXXX` và cấu hình lại
- ✅ Check Serial Monitor để xem lỗi kết nối
- ✅ Đảm bảo router WiFi ở tần số 2.4GHz (ESP32 không hỗ trợ 5GHz)

### Voice Assistant không nghe/nhận dạng được?
- ✅ Kiểm tra microphone: `python -m speech_recognition`
- ✅ Test mic với Windows Voice Recorder
- ✅ Cài đặt PyAudio đúng cách (dùng pipwin trên Windows)
- ✅ Đảm bảo có internet (Google Speech Recognition cần online)
- ✅ Nói rõ ràng, không quá nhanh/chậm
- ✅ Kiểm tra environment variable nếu dùng venv

### Model AI không chính xác?
- ✅ Retrain model: `python train_simple.py`
- ✅ Thêm training examples vào `dataset/intents.json`
- ✅ Test accuracy: `python test_svm.py`
- ✅ Check model files trong `models/` (intent_model.h5, config.json)
- ✅ Đảm bảo underthesea đã cài đặt đầy đủ

### Firebase không đồng bộ?
- ✅ Check Serial Monitor: tìm "Firebase initialized!" và "✅ Synced to Firebase"
- ✅ Verify Firebase config trong ESP32_SmartHome.cpp (FIREBASE_HOST, FIREBASE_AUTH)
- ✅ Check Firebase Realtime Database rules (cho phép read/write)
- ✅ Đảm bảo ESP32 đã kết nối WiFi và có internet
- ✅ Test bằng Firebase Console → Realtime Database → xem `/esp32_1`

### Web Dashboard không load/không điều khiển được?
- ✅ Hard refresh: Ctrl+Shift+R hoặc Ctrl+F5
- ✅ Clear browser cache (F12 → Application → Clear storage)
- ✅ Check Firebase config trong `docs/config.js`
- ✅ Verify authorized domain: Firebase Console → Authentication → Settings → Authorized domains → thêm `tlabgh.github.io`
- ✅ Tạo user trong Firebase Authentication (Email/Password)
- ✅ Check browser console (F12) để xem error

### ESP32 restart liên tục?
- ✅ Check nguồn điện (cần >= 500mA, dùng USB tốt hoặc adapter 5V/1A)
- ✅ Tháo servo ra test (servo kéo dòng cao có thể làm ESP32 reset)
- ✅ Kiểm tra short circuit trên breadboard
- ✅ Upload lại firmware với Serial Monitor mở để xem crash log

### Sensor DHT11 trả về NaN?
- ✅ Check kết nối: Data pin đúng GPIO 4, VCC 3.3V, GND
- ✅ Đợi 2-3 giây sau khi bật nguồn (DHT11 cần warm-up)
- ✅ Thử sensor khác (DHT11 dễ hỏng)
- ✅ Kiểm tra pull-up resistor 10kΩ trên data pin (một số module đã tích hợp)

## � Demo & Testing

### 1. Test ESP32 Local Dashboard:
```
1. Upload code lên ESP32
2. Mở Serial Monitor → copy IP address
3. Mở browser: http://<ESP32_IP>/dashboard
4. Test điều khiển LED, cửa, xem sensor
```

### 2. Test Voice Assistant:
```powershell
cd ESP32_TroLy
python voice_assistant.py <ESP32_IP>

# Thử các lệnh:
- "Bật đèn phòng khách"
- "Tắt đèn nhà bếp"
- "Mở cửa"
- "Nhiệt độ bao nhiêu"
- "Bật đèn phòng ngủ và nhà vệ sinh"  # Lệnh kép
```

### 3. Test Web Dashboard Remote:
```
1. Push code lên GitHub
2. Enable GitHub Pages (Settings → Pages)
3. Thêm domain vào Firebase Authorized domains
4. Tạo user trong Firebase Authentication
5. Truy cập: https://tlabgh.github.io/IOT_SmartHome/
6. Đăng nhập và test điều khiển
```

### 4. Test Firebase Sync:
```
1. Mở Firebase Console → Realtime Database
2. Xem path /esp32_1 (cập nhật mỗi 5s)
3. Điều khiển từ web → check /esp32_1/cmd
4. ESP32 nhận lệnh → cmd bị xóa → state cập nhật
```

## 📝 License

MIT License - Đồ án môn học IoT và Ứng dụng. Sử dụng cho mục đích học tập và nghiên cứu.

## 👥 Tác giả

**Đồ án IoT và Ứng dụng - HK I 2025-2026**

Học viện Công nghệ Bưu chính Viễn thông cơ sở TP.HCM

---

**⭐ Star repo trên GitHub nếu thấy hữu ích!**

**Happy Coding! 🚀**
