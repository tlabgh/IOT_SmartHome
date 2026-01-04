from train_simple import IntentClassifierSVM

c = IntentClassifierSVM()
c.load('models')

tests = ['bật đèn phòng khách','tắt hết đèn','mở cửa','nhiệt độ bao nhiêu','xin chào']
for t in tests:
    intent, conf = c.predict(t)
    print(t, '->', intent, conf)
