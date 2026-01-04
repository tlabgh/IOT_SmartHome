"""
Voice Assistant - Trợ lý giọng nói điều khiển ESP32 Smart Home
Sử dụng model AI tự train để phân loại intent
Phản hồi bằng giọng nói + log message
"""

import speech_recognition as sr
import requests
import json
import time
import random
from pathlib import Path
import sys
import os
import tempfile
from datetime import datetime

# Text-to-Speech
from gtts import gTTS
import pygame

# Import trained model
from train_simple import IntentClassifierSVM


class VoiceAssistant:
    def __init__(self, esp32_ip, model_dir='models'):
        self.esp32_ip = esp32_ip
        self.base_url = f"http://{esp32_ip}"
        
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
        
        # 🚀 NÂNG CẤP: Tối ưu speech recognition
        self.recognizer.energy_threshold = 300  # Giảm từ 4000 (nhạy hơn)
        self.recognizer.dynamic_energy_threshold = True  # Tự động điều chỉnh
        self.recognizer.pause_threshold = 0.8  # Giảm thời gian chờ giữa các từ
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Adjust for ambient noise (tăng thời gian calibrate)
        print("🎤 Calibrating microphone...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("✅ Microphone ready!")
        
        # Temp directory for audio files
        self.temp_dir = Path(tempfile.gettempdir()) / 'voice_assistant'
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
            "ACTION": "⚡"
        }
        icon = icons.get(level, "📝")
        print(f"[{timestamp}] {icon} {message}")
    
    def speak(self, text):
        """Phát giọng nói (Text-to-Speech) + log"""
        try:
            self.log_message(f"Speaking: '{text}'", "SPEAK")
            
            # Generate speech
            tts = gTTS(text=text, lang='vi', slow=False)
            
            # Save to temp file
            audio_file = self.temp_dir / f"tts_{int(time.time())}.mp3"
            tts.save(str(audio_file))
            
            # Play audio
            pygame.mixer.music.load(str(audio_file))
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Cleanup
            try:
                audio_file.unlink()
            except:
                pass
                
        except Exception as e:
            self.log_message(f"TTS Error: {e}", "ERROR")
            # Fallback: just print
            print(f"🔊 [VOICE]: {text}")

    def listen(self, timeout=5):
        """Nghe giọng nói từ microphone"""
        with self.microphone as source:
            self.log_message("Listening... (Speak now)", "LISTEN")
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
                self.log_message("Processing audio...", "INFO")
                
                # Speech to text (Google API)
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

    def get_intent_info(self, intent_tag):
        """Lấy thông tin intent từ intents.json"""
        for intent in self.intents_data['intents']:
            if intent['tag'] == intent_tag:
                return intent
        return None

    def execute_action(self, intent_tag):
        """Thực thi action dựa trên intent"""
        intent_info = self.get_intent_info(intent_tag)
        
        if not intent_info:
            msg = "Không tìm thấy hành động tương ứng"
            self.log_message(msg, "ERROR")
            return msg
        
        # Get action
        action = intent_info.get('action')
        
        if not action:
            # No action, just respond
            response = random.choice(intent_info['responses'])
            self.log_message(f"Response: {response}", "INFO")
            return response
        
        # Execute action
        try:
            self.log_message(f"Executing action: {action}", "ACTION")
            
            # === LED CONTROLS ===
            if action == 'led1_on':
                requests.get(f"{self.base_url}/on1", timeout=5)
                response = "Đã bật đèn phòng khách"
                
            elif action == 'led1_off':
                requests.get(f"{self.base_url}/off1", timeout=5)
                response = "Đã tắt đèn phòng khách"
                
            elif action == 'led2_on':
                requests.get(f"{self.base_url}/on2", timeout=5)
                response = "Đã bật đèn phòng ngủ"
                
            elif action == 'led2_off':
                requests.get(f"{self.base_url}/off2", timeout=5)
                response = "Đã tắt đèn phòng ngủ"
                
            elif action == 'led3_on':
                requests.get(f"{self.base_url}/on3", timeout=5)
                response = "Đã bật đèn nhà bếp"
                
            elif action == 'led3_off':
                requests.get(f"{self.base_url}/off3", timeout=5)
                response = "Đã tắt đèn nhà bếp"
                
            elif action == 'led4_on':
                requests.get(f"{self.base_url}/on4", timeout=5)
                response = "Đã bật đèn nhà vệ sinh"
                
            elif action == 'led4_off':
                requests.get(f"{self.base_url}/off4", timeout=5)
                response = "Đã tắt đèn nhà vệ sinh"
                
            elif action == 'led5_on':
                requests.get(f"{self.base_url}/on5", timeout=5)
                response = "Đã bật đèn phòng làm việc"
                
            elif action == 'led5_off':
                requests.get(f"{self.base_url}/off5", timeout=5)
                response = "Đã tắt đèn phòng làm việc"
            
            # === ALL LIGHTS ===
            elif action == 'all_lights_on':
                self.log_message("Turning ON all lights...", "ACTION")
                for i in range(1, 6):
                    requests.get(f"{self.base_url}/on{i}", timeout=5)
                    time.sleep(0.1)
                response = "Đã bật tất cả đèn trong nhà"
                
            elif action == 'all_lights_off':
                self.log_message("Turning OFF all lights...", "ACTION")
                for i in range(1, 6):
                    requests.get(f"{self.base_url}/off{i}", timeout=5)
                    time.sleep(0.1)
                response = "Đã tắt tất cả đèn trong nhà"
            
            # === DOOR CONTROLS ===
            elif action == 'door_open':
                requests.get(f"{self.base_url}/gate_open", timeout=5)
                response = "Đã mở cửa ra vào"
                
            elif action == 'door_close':
                requests.get(f"{self.base_url}/gate_close", timeout=5)
                response = "Đã đóng cửa ra vào"
            
            # === TEMPERATURE CHECK ===
            elif action == 'check_temperature':
                self.log_message("Checking temperature...", "INFO")
                resp = requests.get(f"{self.base_url}/api/status", timeout=5)
                data = resp.json()
                temp = data.get('temp_c')
                
                if temp is not None:
                    response = f"Nhiệt độ hiện tại là {temp:.1f} độ C"
                    self.log_message(f"Temperature: {temp:.1f}°C", "SUCCESS")
                else:
                    response = "Không thể đọc được nhiệt độ từ cảm biến"
                    self.log_message("Temperature sensor error", "ERROR")
            
            # === HUMIDITY CHECK ===
            elif action == 'check_humidity':
                self.log_message("Checking humidity...", "INFO")
                resp = requests.get(f"{self.base_url}/api/status", timeout=5)
                data = resp.json()
                hum = data.get('hum')
                
                if hum is not None:
                    response = f"Độ ẩm hiện tại là {hum:.1f} phần trăm"
                    self.log_message(f"Humidity: {hum:.1f}%", "SUCCESS")
                else:
                    response = "Không thể đọc được độ ẩm từ cảm biến"
                    self.log_message("Humidity sensor error", "ERROR")
            
            # === SYSTEM STATUS ===
            elif action == 'check_status':
                self.log_message("Checking system status...", "INFO")
                resp = requests.get(f"{self.base_url}/api/status", timeout=5)
                data = resp.json()
                
                # Build status report
                wifi_status = "Bật" if data.get('wifi', False) else "Tắt"
                temp = data.get('temp_c', 'N/A')
                hum = data.get('hum', 'N/A')
                ip = data.get('ip', 'N/A')
                
                status_parts = [
                    f"Hệ thống đang hoạt động bình thường.",
                    f"WiFi: {wifi_status}.",
                    f"Nhiệt độ: {temp} độ C." if temp != 'N/A' else "",
                    f"Độ ẩm: {hum} phần trăm." if hum != 'N/A' else ""
                ]
                
                response = " ".join([p for p in status_parts if p])
                self.log_message(f"Status: WiFi={wifi_status}, Temp={temp}°C, Hum={hum}%", "SUCCESS")
                
            else:
                # Default response from intents
                response = random.choice(intent_info['responses'])
            
            self.log_message(f"Action completed: {response}", "SUCCESS")
            return response
        
        except requests.Timeout:
            msg = "Lỗi: ESP32 không phản hồi (timeout)"
            self.log_message(msg, "ERROR")
            return msg
        except requests.ConnectionError:
            msg = "Lỗi: Không thể kết nối với ESP32"
            self.log_message(msg, "ERROR")
            return msg
        except requests.RequestException as e:
            msg = f"Lỗi kết nối ESP32: {str(e)}"
            self.log_message(msg, "ERROR")
            return msg
        except Exception as e:
            msg = f"Lỗi không xác định: {str(e)}"
            self.log_message(msg, "ERROR")
            return msg

    def process_command(self, text):
        """Xử lý lệnh giọng nói - Hỗ trợ lệnh đơn và lệnh kép"""
        if not text:
            return
        
        # 🚀 NÂNG CẤP: Xử lý lệnh kép với "và"
        # Ví dụ: "bật đèn phòng ngủ và nhà vệ sinh"
        if ' và ' in text.lower() or ' với ' in text.lower():
            self.log_message("🔥 Detected compound command!", "AI")
            self.process_compound_command(text)
            return
        
        # Xử lý lệnh đơn bình thường
        self.process_single_command(text)
    
    def process_compound_command(self, text):
        """Xử lý lệnh kép (nhiều action cùng lúc)"""
        # Tách lệnh theo từ nối
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
            
            # Predict intent for each part
            intent, confidence = self.classifier.predict(part)
            
            if intent and confidence > 0.25:  # Lower threshold for compound commands
                self.log_message(f"  └─ Intent: {intent} (conf: {confidence*100:.1f}%)", "AI")
                
                # Execute action without speaking yet
                try:
                    response = self.execute_action(intent)
                    actions_executed.append(intent)
                    responses.append(response)
                    time.sleep(0.2)  # Small delay between actions
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
        # Predict intent using AI model
        self.log_message("Analyzing command with AI...", "AI")
        intent, confidence = self.classifier.predict(text)
        
        if intent is None:
            msg = "Tôi không hiểu lệnh này. Bạn có thể nói rõ hơn không?"
            self.log_message(f"Low confidence ({confidence*100:.1f}%), intent=None", "WARNING")
            self.speak(msg)
            return
        
        self.log_message(f"AI Prediction: {intent} (confidence: {confidence*100:.1f}%)", "AI")
        
        # Execute if confidence > threshold
        if confidence > 0.3:
            response = self.execute_action(intent)
            # Speak the response
            self.speak(response)
        else:
            msg = "Tôi không chắc lắm. Bạn có thể nói rõ hơn được không?"
            self.log_message(f"Low confidence ({confidence*100:.1f}%), not executing", "WARNING")
            self.speak(msg)

    def run(self):
        """Chạy voice assistant"""
        print("\n" + "="*70)
        print("🏠 ESP32 SMART HOME VOICE ASSISTANT - AI POWERED")
        print("="*70)
        print(f"🌐 ESP32 IP: {self.esp32_ip}")
        print(f"🎤 Speech Recognition: Google API (Vietnamese)")
        print(f"🧠 AI Model: SVM (TF-IDF)")
        print(f"🔊 Text-to-Speech: gTTS")
        print("\n📋 Commands:")
        print("   - Bật/tắt đèn từng phòng: 'Bật đèn phòng khách'")
        print("   - Bật/tắt tất cả: 'Bật tất cả đèn', 'Tắt hết đèn'")
        print("   - Cửa: 'Mở cửa', 'Đóng cửa'")
        print("   - Cảm biến: 'Nhiệt độ bao nhiêu', 'Độ ẩm bao nhiêu'")
        print("   - Thoát: 'Thoát', 'Exit', 'Dừng'")
        print("="*70)
        
        # Welcome message
        self.speak("Xin chào! Trợ lý thông minh đã sẵn sàng. Bạn cần điều khiển gì?")
        
        while True:
            try:
                # Listen
                text = self.listen(timeout=10)
                
                if text:
                    # Check for exit command
                    if any(word in text.lower() for word in ['thoát', 'exit', 'quit', 'dừng', 'tạm biệt']):
                        self.log_message("Exit command received", "INFO")
                        self.speak("Tạm biệt! Hẹn gặp lại.")
                        break
                    
                    # Process command
                    self.process_command(text)
                
                # Small delay
                time.sleep(0.5)
            
            except KeyboardInterrupt:
                self.log_message("Interrupted by user (Ctrl+C)", "WARNING")
                self.speak("Tạm biệt!")
                break
            except Exception as e:
                self.log_message(f"Unexpected error: {e}", "ERROR")
                time.sleep(1)


def main():
    import sys
    
    # Get ESP32 IP from command line or use default
    if len(sys.argv) > 1:
        esp32_ip = sys.argv[1]
    else:
        # Try to read from config or prompt user
        esp32_ip = input("Enter ESP32 IP address (e.g., 192.168.1.47): ").strip()
    
    if not esp32_ip:
        print("❌ ESP32 IP address is required!")
        sys.exit(1)
    
    # Check connection
    try:
        print(f"🔍 Testing connection to {esp32_ip}...")
        response = requests.get(f"http://{esp32_ip}/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ Connection successful!")
            data = response.json()
            print(f"   WiFi: {'Online' if data.get('wifi') else 'Offline'}")
            print(f"   IP: {data.get('ip', 'N/A')}")
        else:
            print(f"⚠️ Server returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        print(f"⚠️ Make sure ESP32 is running and IP address is correct!")
    
    # Initialize and run assistant
    print("\n" + "="*70)
    assistant = VoiceAssistant(esp32_ip)
    assistant.run()


if __name__ == '__main__':
    main()
