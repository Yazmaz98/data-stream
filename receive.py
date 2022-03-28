import json
import time
import ast 
from kafka import KafkaProducer
from kafka import KafkaConsumer
from river import linear_model, preprocessing, evaluate, metrics

RECEIVE_FROM = "stocks_test"

consumer = KafkaConsumer(RECEIVE_FROM, bootstrap_servers="localhost:9092", group_id="group-1")

model = (
	preprocessing.StandardScaler() |
	linear_model.LinearRegression(intercept_lr=.1)
	)
dataset = []
stream = [0]
X_test = []
y_true = [] 
y_preds = []
i = 0
metric = metrics.RMSE()
for message in consumer:
	#if i < 1000:
	stocks_info = message.value
	closing_stock = ast.literal_eval(stocks_info.decode('UTF-8'))['Close']
	if len(dataset) < 100:
		stream.append(closing_stock)
		if not bool(dataset):
			dataset.append(({'x': closing_stock}, closing_stock)) # first prediction is itself
		else:
			dataset.append(({'x': stream[-2]}, stream[-1]))
		X_t = stream[-2]  # feature is the x_t-1
		y_t = stream[-1]  # target is x_t
		model = model.learn_one({'x': X_t}, y_t)  # learn on this set
		#print(i)
	else:
		stream.append(closing_stock)
		dataset.append(({'x': stream[-2]}, stream[-1]))
		X_test.append({'x': closing_stock})  # we predict on x_t
		y_preds.append(model.predict_one({'x': closing_stock}))  # predict on x_t
		model.learn_one({'x': stream[-2]}, closing_stock)
		if not bool(y_true):
			y_true.append(0)
		else:
			y_true.append(closing_stock)

		evaluate.progressive_val_score(model=model, dataset=dataset, metric=metric, print_every=100)

		#i += 1
	#else:
		#break


print(len(X_test), X_test)
print(len(y_true), y_true)
print(len(y_preds), y_preds)






