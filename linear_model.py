import json
import time
import ast
import random
import numpy as np
import matplotlib.pyplot as plt

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
metric = metrics.RMSE()

dataset = []  # [({'x_t-1'}: x_t), ({'x_t-2'}: x_t-1), ...]
stream = [0]

i = len(dataset)
MIN_TRAIN = 20  # construct first model on 20 samples at least
TRAIN_EVERY = 10
batch_rmse, river_rmse = [], []
fig = plt.figure()
is_plotted = False
#ax = fig.subplots(1)

for message in consumer:
	print(f'dataset currently has {i+1} elements: {dataset}')
	stocks_info = message.value
	closing_stock = ast.literal_eval(stocks_info.decode('UTF-8'))['Close']
	#closing_stock = random.uniform(300, 301)

	if len(dataset) < MIN_TRAIN:
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

	else:
		stream.append(closing_stock)
		dataset.append(({'x': stream[-2]}, stream[-1]))
		model.learn_one({'x': stream[-2]}, stream[-1])
		x_batch.append(stream[-2])
		y_batch.append(stream[-1])
		if (i > MIN_TRAIN) and (i % TRAIN_EVERY == 0):
			lm = LinearRegression().fit(np.array(x_batch[:-TRAIN_EVERY]).reshape(-1, 1), y_batch[:-TRAIN_EVERY])
			X_test, y_test = x_batch[-TRAIN_EVERY:], y_batch[-TRAIN_EVERY:]
			y_pred_river = [model.predict_one({'x': x}) for x in X_test]
			y_pred_batch = lm.predict(np.array(X_test).reshape(-1, 1))
			print(f'BATCH RMSE: {mean_squared_error(y_test, y_pred_batch)}')
			print(f'RIVER RMSE: {mean_squared_error(y_test, y_pred_river)}')
			batch_rmse.append(mean_squared_error(y_test, y_pred_batch))
			river_rmse.append(mean_squared_error(y_test, y_pred_river))
			x_batch = x_batch + X_test
			y_batch = y_batch + y_test
			plt.plot(batch_rmse, color='green', label='batch')
			plt.plot(river_rmse, color='red', label='river')
			if not is_plotted:
				plt.legend()
				plt.xlabel(f'Number of iterations (x{TRAIN_EVERY})')
				plt.ylabel('RMSE')
				is_plotted = True
			plt.pause(TRAIN_EVERY)
	i += 1



# must delete first element of y_true and last element of y_pred








