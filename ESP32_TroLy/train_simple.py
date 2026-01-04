"""
Train Intent Classification với TF-IDF + SVM (Tốt hơn cho dataset nhỏ)
"""

import json
import numpy as np
import pickle
from pathlib import Path
import re

# Vietnamese NLP
from underthesea import word_tokenize

# Machine Learning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report


class IntentClassifierSVM:
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.label_encoder = None
        
    def preprocess_text(self, text):
        """Xử lý văn bản tiếng Việt"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        try:
            # Word tokenization
            text = word_tokenize(text, format="text")
        except Exception as e:
            print(f"Tokenization error: {e}")
            pass
        
        return text
    
    def load_data(self, intents_file):
        """Load dataset"""
        with open(intents_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        patterns = []
        tags = []
        
        for intent in data['intents']:
            tag = intent['tag']
            for pattern in intent['patterns']:
                processed = self.preprocess_text(pattern)
                patterns.append(processed)
                tags.append(tag)
        
        return patterns, tags, data['intents']
    
    def train(self, intents_file):
        """Train model"""
        print("="*60)
        print("🤖 TRAINING INTENT CLASSIFIER (TF-IDF + SVM)")
        print("="*60)
        
        # Load data
        print("\n📚 Loading data...")
        patterns, tags, intents_data = self.load_data(intents_file)
        print(f"✅ Loaded {len(patterns)} patterns with {len(set(tags))} intents")
        
        # Encode labels
        print("\n🔧 Encoding labels...")
        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(tags)
        print(f"✅ Classes: {list(self.label_encoder.classes_)}")
        
        # Split data (larger test set for small dataset)
        X_train, X_test, y_train, y_test = train_test_split(
            patterns, y, test_size=0.25, random_state=42, stratify=y
        )
        print(f"✅ Train: {len(X_train)} samples, Test: {len(X_test)} samples")
        
        # Vectorize text
        print("\n🔤 Vectorizing text with TF-IDF...")
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),  # Unigrams + bigrams
            min_df=1,
            max_df=0.8
        )
        
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        print(f"✅ Vocabulary size: {len(self.vectorizer.vocabulary_)}")
        print(f"✅ Feature matrix shape: {X_train_vec.shape}")
        
        # Train SVM với Grid Search
        print("\n🚀 Training SVM classifier...")
        param_grid = {
            'C': [0.1, 1, 10],
            'kernel': ['rbf', 'linear'],
            'gamma': ['scale', 'auto']
        }
        
        svm = SVC(probability=True, random_state=42)
        grid_search = GridSearchCV(
            svm, param_grid, cv=3, scoring='accuracy', 
            verbose=1, n_jobs=-1
        )
        
        grid_search.fit(X_train_vec, y_train)
        self.model = grid_search.best_estimator_
        
        print(f"\n✅ Best parameters: {grid_search.best_params_}")
        
        # Evaluate
        print("\n📊 Evaluating model...")
        train_pred = self.model.predict(X_train_vec)
        test_pred = self.model.predict(X_test_vec)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        
        print(f"\n📈 Training Accuracy: {train_acc*100:.2f}%")
        print(f"📈 Test Accuracy: {test_acc*100:.2f}%")
        
        print("\n📊 Classification Report (Test Set):")
        print(classification_report(
            y_test, test_pred, 
            target_names=self.label_encoder.classes_,
            zero_division=0
        ))
        
        return train_acc, test_acc
    
    def predict(self, text, threshold=0.3):
        """Predict intent"""
        processed = self.preprocess_text(text)
        vec = self.vectorizer.transform([processed])
        
        # Get probabilities
        proba = self.model.predict_proba(vec)[0]
        max_idx = np.argmax(proba)
        confidence = proba[max_idx]
        
        if confidence < threshold:
            return None, confidence
        
        intent = self.label_encoder.classes_[max_idx]
        return intent, confidence
    
    def save(self, model_dir):
        """Save model"""
        model_dir = Path(model_dir)
        model_dir.mkdir(exist_ok=True)
        
        # Save SVM model
        with open(model_dir / 'svm_model.pkl', 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save vectorizer
        with open(model_dir / 'vectorizer.pkl', 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        # Save label encoder
        with open(model_dir / 'label_encoder.pkl', 'wb') as f:
            pickle.dump(self.label_encoder, f)
        
        print(f"\n💾 Model saved to {model_dir.absolute()}")
    
    def load(self, model_dir):
        """Load model"""
        model_dir = Path(model_dir)
        
        with open(model_dir / 'svm_model.pkl', 'rb') as f:
            self.model = pickle.load(f)
        
        with open(model_dir / 'vectorizer.pkl', 'rb') as f:
            self.vectorizer = pickle.load(f)
        
        with open(model_dir / 'label_encoder.pkl', 'rb') as f:
            self.label_encoder = pickle.load(f)
        
        print(f"✅ Model loaded from {model_dir.absolute()}")


if __name__ == '__main__':
    # simple test helper
    base_dir = Path(__file__).parent
    intents_file = base_dir / 'dataset' / 'intents.json'
    classifier = IntentClassifierSVM()
    classifier.load('../models')
    tests = ['bật đèn phòng khách','tắt hết đèn','mở cửa','nhiệt độ bao nhiêu']
    for t in tests:
        intent, conf = classifier.predict(t)
        print(t, '->', intent, conf)
