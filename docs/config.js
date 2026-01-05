// Điền thông tin Firebase Web App Config của bạn tại đây.
// Cách lấy: Firebase Console -> Project settings -> General -> Your apps (Web app)
// Lưu ý: API key của Firebase Web không phải "secret", có thể commit trong repo private.

window.firebaseConfig = {
  apiKey: "AIzaSyBc1VcD0bwBuoe8QmhGONv2h9lvx_U28Hg",
  authDomain: "iot-smarthome-63a3c.firebaseapp.com",
  databaseURL: "https://iot-smarthome-63a3c-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "iot-smarthome-63a3c",
  storageBucket: "iot-smarthome-63a3c.firebasestorage.app",
  messagingSenderId: "462509465752",
  appId: "1:462509465752:web:fb720ea12082468f02b0ed"
};

// Path đúng với ESP32 đang dùng (FB_BASE_PATH = "/esp32_1")
window.espBasePath = "esp32_1";
