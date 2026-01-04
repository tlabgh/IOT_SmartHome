import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import {
  getDatabase,
  ref,
  onValue,
  set
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

import {
  getAuth,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

function el(id) { return document.getElementById(id); }

function setHidden(element, hidden) {
  if (!element) return;
  element.classList.toggle("hidden", !!hidden);
}

const firebaseConfig = window.firebaseConfig;
const espBasePath = window.espBasePath || "esp32_1";

if (!firebaseConfig || firebaseConfig.apiKey === "YOUR_API_KEY") {
  const authBadge = el("auth-badge");
  if (authBadge) authBadge.textContent = "Thiếu Firebase config";
  throw new Error("Firebase config not set");
}

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);
const auth = getAuth(app);

const stateRef = ref(db, espBasePath);
const cmdRef = ref(db, `${espBasePath}/cmd`);

let canControl = false;

function requireAuthOrWarn() {
  if (canControl) return true;
  alert("Bạn cần đăng nhập để điều khiển.");
  return false;
}

async function sendCommand(commandObject) {
  // Ghi đè /cmd. ESP32 sẽ đọc rồi xóa node này.
  await set(cmdRef, {
    ...commandObject,
    client_ts: Date.now()
  });
}

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
  if (!requireAuthOrWarn()) return;
  const key = `led${idx}`;
  const value = state ? 1 : 0;
  sendCommand({ [key]: value }).catch(console.log);
}

function toggleLed(elm) {
  if (!requireAuthOrWarn()) return;
  var idx = parseInt(elm.getAttribute("data-led"));
  if (!idx) return;
  var isOn = elm.classList.contains("on");
  var newState = isOn ? 0 : 1;
  led(idx, newState);
}

function gateOpen() {
  if (!requireAuthOrWarn()) return;
  sendCommand({ servo_angle: 180 })
    .then(function(){
      var t = document.getElementById("door-state-text");
      if (t) t.innerText = "Đang mở";
    })
    .catch(function(e){ console.log(e); });
}

function gateClose() {
  if (!requireAuthOrWarn()) return;
  sendCommand({ servo_angle: 0 })
    .then(function(){
      var t = document.getElementById("door-state-text");
      if (t) t.innerText = "Đang đóng";
    })
    .catch(function(e){ console.log(e); });
}

let servoSendTimer = null;
function onServoSliderChange(val) {
  // cập nhật số bên cạnh thanh trượt
  var sliderVal = document.getElementById("servo-slider-value");
  if (sliderVal) sliderVal.innerText = val;

  if (!canControl) return;

  // throttle để không spam DB khi kéo slider
  if (servoSendTimer) clearTimeout(servoSendTimer);
  servoSendTimer = setTimeout(() => {
    const ang = Math.max(0, Math.min(180, Number(val) || 0));
    sendCommand({ servo_angle: Math.round(ang) }).catch(console.log);
  }, 180);
}

function applyStatus(data) {
  if (!data) return;

  // ----- WiFi badge -----
  const wifiBadge = document.getElementById("wifi-badge");
  if (wifiBadge) {
    if (data.wifi == 1 || data.wifi === true) {
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
  const doorOpenState = data.door_open == 1 || data.door_open === true;
  const doorTextDash = document.getElementById("door-state-text-dashboard");
  const doorPill = document.getElementById("door-state-pill");
  const doorStateText = doorOpenState ? "Đang mở" : "Đang đóng";

  if (doorTextDash) doorTextDash.innerText = "Cửa " + (doorOpenState ? "đang mở" : "đang đóng");
  if (doorPill) doorPill.innerText = doorStateText;

  const doorText = document.getElementById("door-state-text");
  if (doorText) doorText.innerText = doorStateText;

  // ----- Servo angle (góc cửa) -----
  var angle = (data.servo_angle != null) ? Number(data.servo_angle) : 0;
  if (!Number.isFinite(angle)) angle = 0;
  var angleText = document.getElementById("servo-angle-text");
  var slider = document.getElementById("servo-slider");
  var sliderValue = document.getElementById("servo-slider-value");

  if (angleText) angleText.innerText = angle;
  if (slider) slider.value = angle;
  if (sliderValue) sliderValue.innerText = angle;

  // ----- LED trạng thái tổng quát -----
  const leds = [data.led1, data.led2, data.led3, data.led4, data.led5];
  const onCount = leds.filter(function(x){ return x == 1 || x === true; }).length;
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
    if (st == 1 || st === true) sw.classList.add("on");
    else sw.classList.remove("on");
  });

  // ----- Trạng thái chi tiết từng đèn trên Dashboard -----
  for (var i = 0; i < leds.length; i++) {
    var st = leds[i];
    var item = document.getElementById("light-item-" + (i + 1));
    var textEl = document.getElementById("light-status-" + (i + 1));
    if (item) {
      if (st == 1 || st === true) item.classList.add("on");
      else item.classList.remove("on");
    }
    if (textEl) {
      textEl.innerText = (st == 1 || st === true) ? "Đang bật" : "Đang tắt";
    }
  }

  // ----- Nhiệt độ + độ ẩm -----
  const t = (data.temp_c != null) ? Number(data.temp_c) : null;
  const h = (data.hum != null) ? Number(data.hum) : null;

  const tempDash = document.getElementById("temp-val-dashboard");
  const humDash = document.getElementById("hum-val-dashboard");
  const tempDetail = document.getElementById("temp-val-detail");
  const humDetail = document.getElementById("hum-val-detail");

  if (tempDash)   tempDash.innerText   = (t != null && Number.isFinite(t)) ? t.toFixed(1) : "--";
  if (tempDetail) tempDetail.innerText = (t != null && Number.isFinite(t)) ? t.toFixed(1) : "--";
  if (humDash)    humDash.innerText    = (h != null && Number.isFinite(h)) ? h.toFixed(1) : "--";
  if (humDetail)  humDetail.innerText  = (h != null && Number.isFinite(h)) ? h.toFixed(1) : "--";

  const sensorDescDash = document.getElementById("sensor-desc-dashboard");
  const sensorDescDetail = document.getElementById("sensor-desc-detail");
  const ok = (t != null && Number.isFinite(t)) && (h != null && Number.isFinite(h));
  const msg = ok ? "Nhiệt độ & độ ẩm hiện tại." : "Không đọc được dữ liệu DHT11.";
  if (sensorDescDash) sensorDescDash.innerText = msg;
  if (sensorDescDetail) sensorDescDetail.innerText = msg;

  // ----- Hệ thống -----
  const statusText = (data.wifi == 1 || data.wifi === true) ? "Hệ thống hoạt động" : "WiFi chưa kết nối";
  const ipText = "IP: " + (data.ip || "N/A");
  const sysStatus = document.getElementById("sys-status");
  const sysExtra = document.getElementById("sys-extra");
  if (sysStatus) sysStatus.innerText = statusText;
  if (sysExtra)  sysExtra.innerText  = ipText;
}

// Firebase Auth wiring
function initAuthUi() {
  const authState = el("auth-state");
  const authBadge = el("auth-badge");
  const form = el("auth-form");
  const logoutBtn = el("logout-btn");
  const emailInput = el("auth-email");
  const passInput = el("auth-pass");

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = (emailInput?.value || "").trim();
      const pass = passInput?.value || "";
      if (!email || !pass) {
        alert("Nhập email và password.");
        return;
      }
      try {
        await signInWithEmailAndPassword(auth, email, pass);
        if (passInput) passInput.value = "";
      } catch (err) {
        alert("Đăng nhập thất bại: " + (err?.message || err));
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        await signOut(auth);
      } catch (err) {
        alert("Đăng xuất thất bại: " + (err?.message || err));
      }
    });
  }

  onAuthStateChanged(auth, (user) => {
    canControl = !!user;

    if (authState) authState.textContent = user ? (user.email || "Signed in") : "Signed out";

    if (authBadge) {
      authBadge.classList.remove("online", "offline");
      authBadge.classList.add(user ? "online" : "offline");
      authBadge.textContent = user ? "Auth: Signed in" : "Auth: Signed out";
    }

    // When signed in, hide email/password inputs and show logout.
    setHidden(emailInput, !!user);
    setHidden(passInput, !!user);
    const loginBtn = el("login-btn");
    setHidden(loginBtn, !!user);
    setHidden(logoutBtn, !user);
  });
}

initAuthUi();

// Subscribe trạng thái realtime
onValue(stateRef, (snapshot) => {
  const data = snapshot.val();
  applyStatus(data);
});

// Đảm bảo lúc load lên đang ở dashboard
window.showView = showView;
window.toggleLed = toggleLed;
window.gateOpen = gateOpen;
window.gateClose = gateClose;
window.onServoSliderChange = onServoSliderChange;
window.led = led;

showView("dashboard");
