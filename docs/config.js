// Điền thông tin Firebase Web App Config của bạn tại đây.
// Cách lấy: Firebase Console -> Project settings -> General -> Your apps (Web app)
// Lưu ý: API key của Firebase Web không phải "secret", có thể commit trong repo private.

window.firebaseConfig = {
  apiKey: "AIzaSyDmV5OjJyKScIxkwVZnoeob4l4KXcdEQdw",
  authDomain: "iot-smarthome-998dc.firebaseapp.com",
  databaseURL: "https://iot-smarthome-998dc-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "iot-smarthome-998dc",
  storageBucket: "iot-smarthome-998dc.firebasestorage.app",
  messagingSenderId: "21972927058",
  appId: "1:21972927058:web:62ab25a8a97bc7ff75d58b"
};

// Path đúng với ESP32 đang dùng (FB_BASE_PATH = "/esp32_1")
window.espBasePath = "esp32_1";
