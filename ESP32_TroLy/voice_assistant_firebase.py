"""
Voice Assistant Firebase - Điều khiển ESP32 từ xa qua Firebase
✅ Không cần cùng mạng WiFi với ESP32
✅ Không cần biết IP ESP32 (ESP32 có thể đổi IP/mạng bất kỳ)
✅ Điều khiển từ mọi nơi có internet
"""

import speech_recognition as sr
import firebase_admin
from firebase_admin import credentials, db
import json
import time
import random
from pathlib import Path
import sys
import tempfile
from datetime import datetime

# Text-to-Speech
from gtts import gTTS
import pygame

# Import trained model
from train_simple import IntentClassifierSVM


class VoiceAssistantFirebase:
    def __init__(self, firebase_cred_path, database_url, esp_base_path='esp32_1', model_dir='models'):
        """
        Khởi tạo Voice Assistant với Firebase
        
        Args:
            firebase_cred_path: Đường dẫn đến file service account key JSON
            database_url: URL của Firebase Realtime Database
            esp_base_path: Base path trong Firebase (mặc định: 'esp32_1')
            model_dir: Thư mục chứa AI model
        """
        self.esp_base_path = esp_base_path
        self.database_url = database_url
        
        # Initialize Firebase
        print("🔥 Initializing Firebase...")
        try:
            cred = credentials.Certificate(firebase_cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': database_url
            })
            print("✅ Firebase connected!")
        except Exception as e:
            print(f"❌ Firebase init failed: {e}")
            raise
        
        # Firebase references
        self.ref_state = db.reference(f'/{esp_base_path}')
        self.ref_cmd = db.reference(f'/{esp_base_path}/cmd')
        
        # Load intents
        intents_file = Path(__file__).parent / 'dataset' / 'intents.json'
        with open(intents_file, 'r', encoding='utf-8') as f:
            self.intents_data = json.load(f)
        
        # Load trained model
        print("🤖 Loading AI model...")
        self.classifier = IntentClassifierSVM()
        self.classifier.load(model_dir)
        print("✅ Model loaded successfully!")
        
        # Speech recognizer
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Optimize speech recognition
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Calibrate microphone
        print("🎤 Calibrating microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("✅ Microphone ready!")
        
        # Temp directory for audio
        self.temp_dir = Path(tempfile.gettempdir()) / 'voice_assistant_firebase'
        self.temp_dir.mkdir(exist_ok=True)
    
    def log_message(self, message, level="INFO"):
        """Log message với timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "SPEAK": "🔊",
            "LISTEN": "🎤",
            "AI": "🧠",
            "ACTION": "⚡",
            "FIREBASE": "🔥"
        }
        icon = icons.get(level, "📝")
        print(f"[{timestamp}] {icon} {message}")
    
    def speak(self, text):
        """Text-to-Speech"""
        try:
            self.log_message(f"Speaking: '{text}'", "SPEAK")
            
            tts = gTTS(text=text, lang='vi', slow=False)
            audio_file = self.temp_dir / f"tts_{int(time.time())}.mp3"
            tts.save(str(audio_file))
            
            pygame.mixer.music.load(str(audio_file))
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            try:
                audio_file.unlink()
            except:
                pass
                
        except Exception as e:
            self.log_message(f"TTS Error: {e}", "ERROR")
            print(f"🔊 [VOICE]: {text}")
    
    def listen(self, timeout=5):
        """Nghe giọng nói"""
        with self.microphone as source:
            self.log_message("Listening... (Speak now)", "LISTEN")
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
                self.log_message("Processing audio...", "INFO")
                
                text = self.recognizer.recognize_google(audio, language='vi-VN')
                self.log_message(f"You said: '{text}'", "SUCCESS")
                return text
            
            except sr.WaitTimeoutError:
                self.log_message("No speech detected (timeout)", "WARNING")
                return None
            except sr.UnknownValueError:
                self.log_message("Could not understand audio", "WARNING")
                self.speak("Tôi không nghe rõ, bạn có thể nói lại không?")
                return None
            except sr.RequestError as e:
                self.log_message(f"Speech recognition API error: {e}", "ERROR")
                return None
    
    def send_command_firebase(self, command_data):
        """
        Gửi lệnh lên Firebase
        ESP32 sẽ đọc và thực thi lệnh từ /esp32_1/cmd
        
        Args:
            command_data: Dict chứa lệnh, ví dụ: {'led1': 1, 'led2': 0}
        """
        try:
            self.log_message(f"Sending command to Firebase: {command_data}", "FIREBASE")
            self.ref_cmd.set(command_data)
            
            # Wait a bit for ESP32 to process
            time.sleep(0.5)
            
            self.log_message("Command sent successfully!", "SUCCESS")
            return True
        except Exception as e:
            self.log_message(f"Firebase command error: {e}", "ERROR")
            return False
    
    def get_esp_state(self):
        """
        Đọc trạng thái hiện tại của ESP32 từ Firebase
        Returns: Dict chứa trạng thái (led1, led2, temp_c, hum, etc.)
        """
        try:
            state = self.ref_state.get()
            if state:
                self.log_message(f"ESP32 state retrieved from Firebase", "FIREBASE")
                return state
            else:
                self.log_message("No ESP32 state in Firebase", "WARNING")
                return {}
        except Exception as e:
            self.log_message(f"Firebase read error: {e}", "ERROR")
            return {}
    
    def get_intent_info(self, intent_tag):
        """Lấy thông tin intent từ intents.json"""
        for intent in self.intents_data['intents']:
            if intent['tag'] == intent_tag:
                return intent
        return None
    
    def execute_action(self, intent_tag):
        """Thực thi action qua Firebase"""
        intent_info = self.get_intent_info(intent_tag)
        
        if not intent_info:
            msg = "Không tìm thấy hành động tương ứng"
            self.log_message(msg, "ERROR")
            return msg
        
        action = intent_info.get('action')
        
        if not action:
            # No action, just respond
            response = random.choice(intent_info['responses'])
            self.log_message(f"Response: {response}", "INFO")
            return response
        
        try:
            self.log_message(f"Executing action: {action}", "ACTION")
            
            # === LED CONTROLS (send command to Firebase) ===
            if action == 'led1_on':
                self.send_command_firebase({'led1': 1})
                response = "Đã bật đèn phòng khách"
                
            elif action == 'led1_off':
                self.send_command_firebase({'led1': 0})
                response = "Đã tắt đèn phòng khách"
                
            elif action == 'led2_on':
                self.send_command_firebase({'led2': 1})
                response = "Đã bật đèn phòng ngủ"
                
            elif action == 'led2_off':
                self.send_command_firebase({'led2': 0})
                response = "Đã tắt đèn phòng ngủ"
                
            elif action == 'led3_on':
                self.send_command_firebase({'led3': 1})
                response = "Đã bật đèn nhà bếp"
                
            elif action == 'led3_off':
                self.send_command_firebase({'led3': 0})
                response = "Đã tắt đèn nhà bếp"
                
            elif action == 'led4_on':
                self.send_command_firebase({'led4': 1})
                response = "Đã bật đèn nhà vệ sinh"
                
            elif action == 'led4_off':
                self.send_command_firebase({'led4': 0})
                response = "Đã tắt đèn nhà vệ sinh"
                
            elif action == 'led5_on':
                self.send_command_firebase({'led5': 1})
                response = "Đã bật đèn phòng làm việc"
                
            elif action == 'led5_off':
                self.send_command_firebase({'led5': 0})
                response = "Đã tắt đèn phòng làm việc"
            
            # === ALL LIGHTS ===
            elif action == 'all_lights_on':
                self.log_message("Turning ON all lights...", "ACTION")
                self.send_command_firebase({
                    'led1': 1, 'led2': 1, 'led3': 1, 'led4': 1, 'led5': 1
                })
                response = "Đã bật tất cả đèn trong nhà"
                
            elif action == 'all_lights_off':
                self.log_message("Turning OFF all lights...", "ACTION")
                self.send_command_firebase({
                    'led1': 0, 'led2': 0, 'led3': 0, 'led4': 0, 'led5': 0
                })
                response = "Đã tắt tất cả đèn trong nhà"
            
            # === DOOR CONTROLS ===
            elif action == 'door_open':
                self.send_command_firebase({'servo_angle': 180})
                response = "Đã mở cửa ra vào"
                
            elif action == 'door_close':
                self.send_command_firebase({'servo_angle': 0})
                response = "Đã đóng cửa ra vào"
            
            # === TEMPERATURE CHECK (read from Firebase) ===
            elif action == 'check_temperature':
                self.log_message("Checking temperature from Firebase...", "INFO")
                state = self.get_esp_state()
                temp = state.get('temp_c')
                
                if temp is not None:
                    response = f"Nhiệt độ hiện tại là {temp:.1f} độ C"
                    self.log_message(f"Temperature: {temp:.1f}°C", "SUCCESS")
                else:
                    response = "Không thể đọc được nhiệt độ từ cảm biến"
                    self.log_message("Temperature data not available", "ERROR")
            
            # === HUMIDITY CHECK ===
            elif action == 'check_humidity':
                self.log_message("Checking humidity from Firebase...", "INFO")
                state = self.get_esp_state()
                hum = state.get('hum')
                
                if hum is not None:
                    response = f"Độ ẩm hiện tại là {hum:.1f} phần trăm"
                    self.log_message(f"Humidity: {hum:.1f}%", "SUCCESS")
                else:
                    response = "Không thể đọc được độ ẩm từ cảm biến"
                    self.log_message("Humidity data not available", "ERROR")
            
            # === SYSTEM STATUS ===
            elif action == 'check_status':
                self.log_message("Checking system status from Firebase...", "INFO")
                state = self.get_esp_state()
                
                wifi_status = "Bật" if state.get('wifi', False) else "Tắt"
                temp = state.get('temp_c', 'N/A')
                hum = state.get('hum', 'N/A')
                ip = state.get('ip', 'N/A')
                
                status_parts = [
                    f"Hệ thống đang hoạt động bình thường.",
                    f"WiFi: {wifi_status}.",
                    f"Địa chỉ IP: {ip}.",
                    f"Nhiệt độ: {temp} độ C." if temp != 'N/A' else "",
                    f"Độ ẩm: {hum} phần trăm." if hum != 'N/A' else ""
                ]
                
                response = " ".join([p for p in status_parts if p])
                self.log_message(f"Status: WiFi={wifi_status}, IP={ip}, Temp={temp}°C, Hum={hum}%", "SUCCESS")
                
            # === GET IP ADDRESS ===
            elif action == 'get_ip':
                self.log_message("Getting IP address from Firebase...", "INFO")
                state = self.get_esp_state()
                ip = state.get('ip')
                
                if ip and ip != 'N/A':
                    response = f"Địa chỉ IP của ESP32 là {ip}"
                    self.log_message(f"IP Address: {ip}", "SUCCESS")
                else:
                    response = "Không thể lấy địa chỉ IP. ESP32 có thể chưa kết nối WiFi"
                    self.log_message("IP address not available", "ERROR")
                
            else:
                # Default response
                response = random.choice(intent_info['responses'])
            
            self.log_message(f"Action completed: {response}", "SUCCESS")
            return response
        
        except Exception as e:
            msg = f"Lỗi thực thi: {str(e)}"
            self.log_message(msg, "ERROR")
            return msg
    
    def process_command(self, text):
        """Xử lý lệnh giọng nói - Hỗ trợ lệnh đơn và lệnh kép"""
        if not text:
            return
        
        # Check for compound commands
        if ' và ' in text.lower() or ' với ' in text.lower():
            self.log_message("🔥 Detected compound command!", "AI")
            self.process_compound_command(text)
            return
        
        # Process single command
        self.process_single_command(text)
    
    def process_compound_command(self, text):
        """Xử lý lệnh kép"""
        parts = []
        for separator in [' và ', ' với ']:
            if separator in text.lower():
                parts = text.lower().split(separator)
                break
        
        if len(parts) < 2:
            self.process_single_command(text)
            return
        
        self.log_message(f"Split into {len(parts)} sub-commands: {parts}", "AI")
        
        actions_executed = []
        responses = []
        
        for idx, part in enumerate(parts):
            part = part.strip()
            self.log_message(f"Processing sub-command {idx+1}/{len(parts)}: '{part}'", "AI")
            
            intent, confidence = self.classifier.predict(part)
            
            if intent and confidence > 0.25:
                self.log_message(f"  └─ Intent: {intent} (conf: {confidence*100:.1f}%)", "AI")
                
                try:
                    response = self.execute_action(intent)
                    actions_executed.append(intent)
                    responses.append(response)
                    time.sleep(0.3)  # Small delay between Firebase writes
                except Exception as e:
                    self.log_message(f"  └─ Error: {e}", "ERROR")
            else:
                self.log_message(f"  └─ Low confidence or no intent", "WARNING")
        
        # Speak combined response
        if actions_executed:
            if len(actions_executed) == len(parts):
                final_response = f"Đã thực hiện {len(actions_executed)} lệnh: " + ", ".join(responses)
            else:
                final_response = f"Đã thực hiện {len(actions_executed)}/{len(parts)} lệnh. " + ", ".join(responses)
            
            self.log_message(f"Compound command completed: {len(actions_executed)} actions", "SUCCESS")
            self.speak(final_response)
        else:
            self.speak("Không thể thực hiện lệnh này. Bạn có thể nói rõ hơn không?")
    
    def process_single_command(self, text):
        """Xử lý lệnh đơn"""
        self.log_message("Analyzing command with AI...", "AI")
        intent, confidence = self.classifier.predict(text)
        
        if intent is None:
            msg = "Tôi không hiểu lệnh này. Bạn có thể nói rõ hơn không?"
            self.log_message(f"Low confidence ({confidence*100:.1f}%), intent=None", "WARNING")
            self.speak(msg)
            return
        
        self.log_message(f"AI Prediction: {intent} (confidence: {confidence*100:.1f}%)", "AI")
        
        if confidence > 0.3:
            response = self.execute_action(intent)
            self.speak(response)
        else:
            msg = "Tôi không chắc lắm. Bạn có thể nói rõ hơn được không?"
            self.log_message(f"Low confidence ({confidence*100:.1f}%), not executing", "WARNING")
            self.speak(msg)
    
    def run(self):
        """Chạy voice assistant"""
        print("\n" + "="*70)
        print("🏠 ESP32 SMART HOME VOICE ASSISTANT - FIREBASE REMOTE CONTROL")
        print("="*70)
        print(f"🔥 Firebase Database: {self.database_url}")
        print(f"📡 ESP32 Base Path: /{self.esp_base_path}")
        print(f"🎤 Speech Recognition: Google API (Vietnamese)")
        print(f"🧠 AI Model: SVM (TF-IDF)")
        print(f"🔊 Text-to-Speech: gTTS")
        print("\n✅ Ưu điểm:")
        print("   - Điều khiển từ xa (không cần cùng WiFi với ESP32)")
        print("   - ESP32 đổi IP/mạng vẫn hoạt động")
        print("   - Điều khiển từ mọi nơi có internet")
        print("\n📋 Commands:")
        print("   - Bật/tắt đèn: 'Bật đèn phòng khách'")
        print("   - Tất cả đèn: 'Bật tất cả đèn', 'Tắt hết đèn'")
        print("   - Cửa: 'Mở cửa', 'Đóng cửa'")
        print("   - Cảm biến: 'Nhiệt độ bao nhiêu', 'Độ ẩm bao nhiêu'")
        print("   - Lệnh kép: 'Bật đèn phòng ngủ và nhà vệ sinh'")
        print("   - Thoát: 'Thoát', 'Exit'")
        print("="*70)
        
        # Check Firebase connection
        try:
            self.log_message("Testing Firebase connection...", "FIREBASE")
            state = self.get_esp_state()
            if state:
                wifi = "Online" if state.get('wifi') else "Offline"
                ip = state.get('ip', 'N/A')
                self.log_message(f"ESP32 Status: WiFi={wifi}, IP={ip}", "SUCCESS")
            else:
                self.log_message("ESP32 not connected to Firebase yet", "WARNING")
        except Exception as e:
            self.log_message(f"Firebase connection test failed: {e}", "ERROR")
        
        # Welcome
        self.speak("Xin chào! Trợ lý điều khiển từ xa đã sẵn sàng. Bạn cần điều khiển gì?")
        
        while True:
            try:
                text = self.listen(timeout=10)
                
                if text:
                    # Check exit
                    if any(word in text.lower() for word in ['thoát', 'exit', 'quit', 'dừng', 'tạm biệt']):
                        self.log_message("Exit command received", "INFO")
                        self.speak("Tạm biệt! Hẹn gặp lại.")
                        break
                    
                    # Process
                    self.process_command(text)
                
                time.sleep(0.5)
            
            except KeyboardInterrupt:
                self.log_message("Interrupted by user (Ctrl+C)", "WARNING")
                self.speak("Tạm biệt!")
                break
            except Exception as e:
                self.log_message(f"Unexpected error: {e}", "ERROR")
                time.sleep(1)


def load_config():
    """Load config from file or create new one"""
    config_file = Path(__file__).parent / 'firebase_config.json'
    
    # Try to load existing config
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("✅ Loaded config from firebase_config.json")
            return config
        except Exception as e:
            print(f"⚠️ Could not load config: {e}")
    
    return None


def save_config(cred_path, database_url, esp_path):
    """Save config to file"""
    config_file = Path(__file__).parent / 'firebase_config.json'
    config = {
        'firebase_cred_path': cred_path,
        'database_url': database_url,
        'esp_base_path': esp_path
    }
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("✅ Config saved to firebase_config.json")
    except Exception as e:
        print(f"⚠️ Could not save config: {e}")


def main():
    print("\n" + "="*70)
    print("🔥 FIREBASE VOICE ASSISTANT")
    print("="*70)
    
    # Try to load existing config
    config = load_config()
    
    if config:
        print("\n📋 Current configuration:")
        print(f"   Service Account Key: {config['firebase_cred_path']}")
        print(f"   Database URL: {config['database_url']}")
        print(f"   ESP Base Path: {config['esp_base_path']}")
        print()
        use_existing = input("Use existing config? (Y/n): ").strip().lower()
        
        if use_existing != 'n':
            cred_path = config['firebase_cred_path']
            database_url = config['database_url']
            esp_path = config['esp_base_path']
        else:
            config = None
    
    if not config:
        # Firebase config
        print("\n📋 Firebase Configuration:")
        print("   1. Đường dẫn đến file service account key JSON")
        print("   2. Firebase Realtime Database URL")
        print("   3. ESP32 base path (mặc định: esp32_1)")
        print()
        
        # Get config from user
        cred_path = input("Service Account Key file path: ").strip()
        if not cred_path:
            print("❌ Service account key path is required!")
            print("\n💡 Hướng dẫn lấy Service Account Key:")
            print("   1. Vào Firebase Console: https://console.firebase.google.com/")
            print("   2. Chọn project của bạn")
            print("   3. Settings (⚙️) → Project settings")
            print("   4. Service accounts tab")
            print("   5. Generate new private key → Download file JSON")
            print("   6. Lưu file vào thư mục ESP32_TroLy/")
            sys.exit(1)
        
        database_url = input("Firebase Database URL (default: https://iot-smarthome-d03a9-default-rtdb.asia-southeast1.firebasedatabase.app): ").strip()
        if not database_url:
            database_url = "https://iot-smarthome-d03a9-default-rtdb.asia-southeast1.firebasedatabase.app"
        
        esp_path = input("ESP32 base path (default: esp32_1): ").strip()
        if not esp_path:
            esp_path = "esp32_1"
        
        # Save config for next time
        save_config(cred_path, database_url, esp_path)
    
    print("\n✅ Configuration complete!")
    
    # Initialize and run
    try:
        assistant = VoiceAssistantFirebase(
            firebase_cred_path=cred_path,
            database_url=database_url,
            esp_base_path=esp_path
        )
        assistant.run()
    except Exception as e:
        print(f"\n❌ Failed to start assistant: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
