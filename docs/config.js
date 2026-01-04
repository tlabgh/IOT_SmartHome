// Điền thông tin Firebase Web App Config của bạn tại đây.
// Cách lấy: Firebase Console -> Project settings -> General -> Your apps (Web app)
// Lưu ý: API key của Firebase Web không phải "secret", có thể commit trong repo private.

window.firebaseConfig = {
  apiKey: "AIzaSyByP2XPL9NUEO33aYh7p3N67IeKjVG0YUA",
  authDomain: "iot-smarthome-d03a9.firebaseapp.com",
  databaseURL: "https://iot-smarthome-d03a9-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "iot-smarthome-d03a9",
  storageBucket: "iot-smarthome-d03a9.firebasestorage.app",
  messagingSenderId: "419061662486",
  appId: "1:419061662486:web:b4f58308309135aca38637"
};

// Path đúng với ESP32 đang dùng (FB_BASE_PATH = "/esp32_1")
window.espBasePath = "esp32_1";
