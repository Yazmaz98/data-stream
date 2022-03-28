import json
import time
import ast 
from kafka import KafkaProducer
from kafka import KafkaConsumer
from river import linear_model, preprocessing, evaluate, metrics, time_series

RECEIVE_FROM = "stocks_test"

consumer = KafkaConsumer(RECEIVE_FROM, bootstrap_servers="localhost:9092", group_id="group-1")

model = (
	preprocessing.StandardScaler() |
	linear_model.LinearRegression(intercept_lr=.1)
	)
ts_model = time_series.Forecaster()
dataset = []
stream = [0]
X_test = []
y_true = [] 
y_preds = []

ts = []
i = 0

metric = metrics.RMSE()
for message in consumer:
	#if i < 1000:
	stocks_info = message.value
	closing_stock = ast.literal_eval(stocks_info.decode('UTF-8'))['Close']
	if len(ts) < 100:
		ts.append(closing_stock)
		ts_model = ts_model.learn_one(y=closing_stock, x=None)  # learn on this set
		#print(i)
	else:
		ts.append(closing_stock)
		y_preds.append(ts_model.forecast(1, closing_stock))  # predict on x_t
		ts_model.learn_one(y=closing_stock, x=None)
		evaluate.progressive_val_score(model=ts_model, dataset=ts, metric=metric, print_every=100)

		#i += 1
	#else:
		#break


print(len(X_test), X_test)
print(len(y_true), y_true)
print(len(y_preds), y_preds)






