import json
import time
import ast
import random
import numpy as np
from sklearn.metrics import mean_squared_error
from kafka import KafkaProducer
from kafka import KafkaConsumer
from river import linear_model, preprocessing, evaluate, metrics
from sklearn.linear_model import LinearRegression

RECEIVE_FROM = "stocks_test"

consumer = KafkaConsumer(RECEIVE_FROM, bootstrap_servers="localhost:9092", group_id="group-1")

model = (
	preprocessing.StandardScaler() |
	linear_model.LinearRegression(intercept_lr=.1)
	)
dataset = []  # [({'x_t-1'}: x_t), ({'x_t-2'}: x_t-1), ...]
stream = [0]
X_test_river = []  # for river
y_true_river = []  # for river
y_pred_river = []  # river predictions
i = 0
metric = metrics.RMSE()
for message in consumer:
	stocks_info = message.value
	closing_stock = ast.literal_eval(stocks_info.decode('UTF-8'))['Close']
	#closing_stock = random.uniform(300, 301)  # np.random.randint(100, 200)

	if len(dataset) < 20:
		stream.append(closing_stock)
		if not bool(dataset):
			dataset.append(({'x': closing_stock}, closing_stock))  # first label is itself because we don't have x_t-1
		else:
			dataset.append(({'x': stream[-2]}, stream[-1]))
		X_t = stream[-2]  # feature is the x_t-1
		y_t = stream[-1]  # target is x_t
		model = model.learn_one({'x': X_t}, y_t)  # learn on this set
		# create set for sklearn linear regressor
		x_batch = [el[0]['x'] for el in dataset]
		y_batch = [el[1] for el in dataset]
		print(len(dataset))
	else:
		stream.append(closing_stock)
		dataset.append(({'x': stream[-2]}, stream[-1]))
		x_batch.append(stream[-2])  # for batch learning
		y_batch.append(stream[-1])  # for batch learning
		X_test_river.append({'x': closing_stock})  # we predict on x_t
		y_pred_river.append(model.predict_one({'x': closing_stock}))  # predict on x_t
		model.learn_one({'x': stream[-2]}, stream[-1])
		'''if not bool(y_true_river):
			y_true_river.append(0)
		else:'''
		y_true_river.append(closing_stock)
		# condition to start printing RMSE for batch learning to compare with river
		if (len(x_batch) > 100) and (len(y_true_river) > 100) and (len(x_batch) % 10 == 0):
			lm = LinearRegression().fit(np.array(x_batch).reshape(-1, 1), y_batch)
			y_pred_batch = lm.predict(np.array(x_batch).reshape(-1, 1))
			print(f'-----length x_batch: {len(x_batch)}')
			print(f'-----length y_true_river: {len(y_true_river)}')
			print(f'-----length y_pred_batch: {len(y_pred_batch)}')
			print(f'-----length y_pred_river: {len(y_pred_river)}')
			n = len(y_pred_batch)
			print(f'BATCH RMSE: {mean_squared_error(y_true_river, y_pred_batch)}')
			#print(f'RIVER RMSE: {mean_squared_error(y_true_river, y_pred_river)}')

			'''print(len(X_test_river), X_test_river[-10:])
			print(len(y_true_river), y_true_river[-10:])
			print(len(y_pred_batch), y_pred_batch[-10:])'''

		print(evaluate.progressive_val_score(model=model, dataset=dataset, metric=metric, print_every=10))
		# must delete first element of y_true and last element of y_pred








