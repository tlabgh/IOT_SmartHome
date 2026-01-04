"""
Test toàn diện cho dự án Voice Assistant
Kiểm tra: Model loading, Intent prediction, Dataset integrity
"""

from train_simple import IntentClassifierSVM
import json
from pathlib import Path
import sys

print("="*70)
print("🧪 COMPREHENSIVE SYSTEM TEST")
print("="*70)

# Test 1: Load dataset
print("\n1️⃣ Testing dataset loading...")
try:
    intents_file = Path(__file__).parent / 'dataset' / 'intents.json'
    with open(intents_file, 'r', encoding='utf-8') as f:
        intents_data = json.load(f)
    
    num_intents = len(intents_data['intents'])
    total_patterns = sum(len(intent['patterns']) for intent in intents_data['intents'])
    
    print(f"   ✅ Dataset loaded successfully")
    print(f"   📊 Total intents: {num_intents}")
    print(f"   📊 Total patterns: {total_patterns}")
    
    # Show intent tags
    tags = [intent['tag'] for intent in intents_data['intents']]
    print(f"   📋 Intent tags: {', '.join(tags[:5])}... (showing first 5)")
    
except Exception as e:
    print(f"   ❌ Dataset loading failed: {e}")
    sys.exit(1)

# Test 2: Load model
print("\n2️⃣ Testing model loading...")
try:
    classifier = IntentClassifierSVM()
    classifier.load('models')
    print(f"   ✅ Model loaded successfully from 'models/' directory")
except Exception as e:
    print(f"   ❌ Model loading failed: {e}")
    sys.exit(1)

# Test 3: Predictions
print("\n3️⃣ Testing intent predictions...")
test_cases = [
    ('bật đèn phòng khách', 'light_on_livingroom'),
    ('tắt đèn phòng ngủ', 'light_off_bedroom'),
    ('mở cửa', 'door_open'),
    ('đóng cửa', 'door_close'),
    ('nhiệt độ bao nhiêu', 'temperature_check'),
    ('độ ẩm hiện tại', 'humidity_check'),
    ('bật tất cả đèn', 'light_all_on'),
    ('tắt hết đèn', 'light_all_off'),
    ('xin chào', 'greeting'),
    ('bật đèn nhà bếp', 'light_on_kitchen'),
]

correct = 0
total = len(test_cases)

for text, expected_intent in test_cases:
    intent, confidence = classifier.predict(text)
    status = "✅" if intent == expected_intent else "❌"
    
    if intent == expected_intent:
        correct += 1
        print(f"   {status} '{text}' → {intent} ({confidence*100:.1f}%)")
    else:
        print(f"   {status} '{text}' → Expected: {expected_intent}, Got: {intent} ({confidence*100:.1f}%)")

accuracy = (correct / total) * 100
print(f"\n   📊 Accuracy: {correct}/{total} ({accuracy:.1f}%)")

# Test 4: Check model files
print("\n4️⃣ Testing model file integrity...")
model_files = [
    'models/svm_model.pkl',
    'models/vectorizer.pkl',
    'models/label_encoder.pkl',
]

for file_path in model_files:
    full_path = Path(__file__).parent / file_path
    if full_path.exists():
        size_kb = full_path.stat().st_size / 1024
        print(f"   ✅ {file_path} ({size_kb:.1f} KB)")
    else:
        print(f"   ❌ {file_path} - NOT FOUND")

# Test 5: Check optional files
print("\n5️⃣ Checking optional model files...")
optional_files = [
    'models/intent_model.h5',  # Keras model (nếu có từ project cũ)
    'models/config.json',
]

for file_path in optional_files:
    full_path = Path(__file__).parent / file_path
    if full_path.exists():
        size_kb = full_path.stat().st_size / 1024
        print(f"   ℹ️  {file_path} ({size_kb:.1f} KB) - Optional file present")
    else:
        print(f"   ℹ️  {file_path} - Not present (OK)")

# Test 6: Requirements check
print("\n6️⃣ Checking required packages...")
required_packages = [
    'speech_recognition',
    'pyaudio',
    'gtts',
    'pygame',
    'sklearn',
    'numpy',
    'requests',
    'underthesea',
]

missing_packages = []
for pkg in required_packages:
    try:
        __import__(pkg)
        print(f"   ✅ {pkg}")
    except ImportError:
        print(f"   ❌ {pkg} - NOT INSTALLED")
        missing_packages.append(pkg)

# Final summary
print("\n" + "="*70)
if accuracy >= 80 and len(missing_packages) == 0:
    print("🎉 ALL TESTS PASSED! System is ready to use.")
    print(f"✅ Model accuracy: {accuracy:.1f}%")
    print(f"✅ All required packages installed")
    print("\n📝 You can now run: python voice_assistant.py <ESP32_IP>")
elif accuracy < 80:
    print("⚠️  TESTS COMPLETED WITH WARNINGS")
    print(f"⚠️  Model accuracy is low: {accuracy:.1f}% (expected >= 80%)")
    print("💡 Consider retraining the model with more data")
else:
    print("❌ TESTS FAILED")
    print(f"❌ Missing packages: {', '.join(missing_packages)}")
    print("💡 Run: pip install -r requirements.txt")

print("="*70)
