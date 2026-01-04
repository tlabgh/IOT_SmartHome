from train_simple import IntentClassifierSVM
import json
from pathlib import Path

print('Loading model...')
classifier = IntentClassifierSVM()
classifier.load('models')
print('Model loaded')

intents_file = Path(__file__).parent / 'dataset' / 'intents.json'
with open(intents_file, 'r', encoding='utf-8') as f:
    intents = json.load(f)

print('Intents loaded:', len(intents['intents']))
