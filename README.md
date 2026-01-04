# 🏠 IOT Smart Home - Hệ thống nhà thông minh với Voice Assistant AI

Đồ án IoT: Hệ thống nhà thông minh điều khiển bằng giọng nói sử dụng ESP32 và AI.

## 📋 Mô tả dự án

Dự án kết hợp:
- **Hardware**: ESP32 điều khiển thiết bị thông minh (LED, servo, cảm biến DHT11)
- **AI Voice Assistant**: Trợ lý giọng nói tiếng Việt sử dụng SVM + TF-IDF
- **Kết nối**: HTTP REST API + Firebase Realtime Database
- **Tính năng**: Điều khiển thiết bị, đọc cảm biến, tự động hóa

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
│   ├── train_simple.py      # Training model
│   ├── test_svm.py          # Test model
│   ├── requirements.txt     # Python dependencies
│   ├── dataset/
│   │   └── intents.json     # Training data (18 intents)
│   └── models/              # Trained AI models
│
└── README.md                # File này
```

## 🌐 Web điều khiển từ xa (GitHub Pages)

Web dashboard remote được đặt tại thư mục `docs/` (static site). Phần web vẫn dùng **Firebase Realtime Database + Firebase Auth**, chỉ thay phần **hosting** (không dùng Firebase Hosting nữa).

### Bật GitHub Pages
1. Push code lên GitHub (repo public hoặc private tuỳ gói GitHub của bạn).
2. Vào **Settings → Pages**
3. **Build and deployment**:
  - Source: **Deploy from a branch**
  - Branch: `main` (hoặc `master`)
  - Folder: `/docs`
4. Đợi 1–2 phút, GitHub sẽ cấp URL dạng: `https://<username>.github.io/<repo>/`

### Lưu ý
- Muốn đăng nhập điều khiển: tạo user trong Firebase Console → Authentication → Users (Email/Password).
- `docs/config.js` đã chứa cấu hình Firebase web + `espBasePath = "esp32_1"`.


## 🚀 Hướng dẫn cài đặt

### 1️⃣ Setup ESP32

#### Yêu cầu:
- PlatformIO IDE (VS Code extension)
- ESP32 DevKit
- Cáp USB

#### Các bước:
```powershell
cd ESP32_Code
pio run              # Compile code
pio run -t upload    # Upload lên ESP32
pio device monitor   # Xem serial output
```

#### Cấu hình WiFi lần đầu:
1. ESP32 sẽ tạo Access Point: `ESP32_Config`
2. Kết nối vào AP này
3. Mở trình duyệt: `http://192.168.4.1`
4. Nhập SSID và password WiFi của bạn
5. ESP32 tự động kết nối và sử dụng **IP cố định: 192.168.1.100**

**⚡ Static IP Configuration:**
ESP32 được cấu hình với IP cố định để không bị thay đổi mỗi lần khởi động lại:
- **IP Address**: `192.168.1.100` (mặc định)
- **Gateway**: `192.168.1.1`
- **Subnet**: `255.255.255.0`

📝 *Lưu ý: Nếu cần đổi IP, sửa trong [ESP32_SmartHome.cpp](ESP32_Code/src/ESP32_SmartHome.cpp#L62-L66)*

### 2️⃣ Setup Voice Assistant

#### Yêu cầu:
- Python 3.8+
- Microphone
- PyAudio (cần cài Visual C++ Build Tools trên Windows)

#### Các bước:
```powershell
cd ESP32_TroLy

# Tạo virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Cài đặt dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Test model AI
python test_svm.py

# Chạy voice assistant (thay <ESP32_IP> bằng IP thực tế)
python voice_assistant.py <ESP32_IP>

# Với Static IP mặc định:
python voice_assistant.py 192.168.1.100
```

**Lưu ý Windows**: Nếu gặp lỗi PyAudio, cài đặt:
```powershell
pip install pipwin
pipwin install pyaudio
```

## 📡 API Endpoints (ESP32)

ESP32 cung cấp các REST API endpoints qua HTTP:

### 1. Điều khiển LED đơn lẻ
```http
GET http://<ESP32_IP>/led/<số>/<on|off>
```
- `<số>`: 1-5 (LED1 đến LED5)
- Ví dụ: `http://192.168.1.86/led/1/on`

**Response:**
```json
{"status": "success", "message": "LED 1 turned on"}
```

### 2. Điều khiển tất cả LED
```http
GET http://<ESP32_IP>/all/<on|off>
```

### 3. Điều khiển cửa (Servo)
```http
GET http://<ESP32_IP>/door/<open|close>
```

### 4. Đọc cảm biến nhiệt độ/độ ẩm
```http
GET http://<ESP32_IP>/sensor
```
**Response:**
```json
{
  "temperature": 28.5,
  "humidity": 65.2,
  "status": "success"
}
```

### 5. Lấy trạng thái hệ thống
```http
GET http://<ESP32_IP>/status
```
**Response:**
```json
{
  "status": "online",
  "led_states": {"led1": false, "led2": true, ...},
  "door_open": false,
  "temperature": 28.5,
  "humidity": 65.2
}
```

### Test API với Python:
```python
import requests

ESP32_IP = "192.168.1.86"

# Bật đèn
requests.get(f"http://{ESP32_IP}/led/1/on")

# Đọc cảm biến
data = requests.get(f"http://{ESP32_IP}/sensor").json()
print(f"Nhiệt độ: {data['temperature']}°C")
```

### Firebase Integration:
ESP32 đồng bộ trạng thái lên Firebase Realtime Database:
```
Database: esp32-smart-home-42217-default-rtdb.asia-southeast1.firebasedatabase.app
Path: /esp32_1
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
┌─────────────┐         HTTP/REST        ┌─────────────┐
│   Voice     │ ──────────────────────►  │    ESP32    │
│  Assistant  │                           │  WebServer  │
│   (Python)  │ ◄──────────────────────  │             │
└─────────────┘      JSON Response       └─────────────┘
      │                                          │
      │                                          │
      ▼                                          ▼
┌─────────────┐                          ┌─────────────┐
│  SVM Model  │                          │  Firebase   │
│  (AI)       │                          │  (Cloud)    │
└─────────────┘                          └─────────────┘
```

## 🐛 Troubleshooting

### ESP32 không kết nối WiFi?
- Kiểm tra SSID/password
- Giữ nút BOOT 5 giây để reset WiFi
- Reconnect vào AP `ESP32_Config`

### Voice Assistant không nghe?
- Kiểm tra microphone
- Chạy `python -m speech_recognition` để test
- Cài đặt PyAudio đúng cách

### Model AI không chính xác?
- Retrain model: `python train_simple.py`
- Thêm training data vào `intents.json`

## 🌐 Điều khiển từ xa (Firebase Hosting + Realtime Database)

ESP32 đã hỗ trợ đồng bộ trạng thái lên Firebase và nhận lệnh điều khiển từ Firebase:

- **Trạng thái**: `/esp32_1` (ESP32 tự cập nhật định kỳ)
- **Lệnh**: `/esp32_1/cmd` (Web ghi lệnh, ESP32 đọc xong sẽ xoá)

Web dashboard nằm trong thư mục `Firebase_Web/`.

### 1) Tạo Firebase Project

1. Firebase Console → tạo Project
2. Bật **Realtime Database**
3. Tạo **Web App** để lấy cấu hình Web SDK

### 1.1) Bật đăng nhập (Firebase Auth)

Để an toàn hơn (chỉ người đã đăng nhập mới điều khiển):

1. Firebase Console → **Authentication** → **Get started**
2. **Sign-in method** → bật **Email/Password**
3. Tạo user cho các thành viên nhóm (tab **Users**)

### 1.2) Realtime Database Rules (gợi ý)

Gợi ý rules để:
- **ESP32** vẫn sync trạng thái (dùng legacy token)
- **Web** chỉ được **ghi lệnh** khi đã đăng nhập

```json
{
  "rules": {
    "esp32_1": {
      ".read": true,
      "cmd": {
        ".read": "auth != null",
        ".write": "auth != null"
      }
    }
  }
}
```

### 2) Cấu hình Web

- Mở `Firebase_Web/public/config.js` và điền `window.firebaseConfig`

### 3) Chạy thử local

```powershell
cd Firebase_Web
npm i -g firebase-tools
firebase login
firebase serve
```

### 4) Deploy public

```powershell
cd Firebase_Web
firebase use --add
firebase deploy --only hosting
```

Sau khi deploy, bạn sẽ có link dạng: `https://<project-id>.web.app`

## 📝 License

Đồ án môn học - Sử dụng cho mục đích học tập

## 👥 Tác giả

Đồ án IoT và Ứng dụng - HK I 2025-2026

---

**Happy Coding! 🚀**
