import json
import time
import ast
import random
import numpy as np
import matplotlib.pyplot as plt

from sklearn.metrics import mean_squared_error
from kafka import KafkaProducer
from kafka import KafkaConsumer
from river import linear_model, preprocessing, evaluate, metrics, time_series
from river.time_series import Forecaster
from sklearn.linear_model import LinearRegression

RECEIVE_FROM = "stocks_test"

consumer = KafkaConsumer(RECEIVE_FROM, bootstrap_servers="localhost:9092", group_id="group-1")

model = time_series.Forecaster

metric = metrics.RMSE()

dataset = []  # [({'x_t-1'}: x_t), ({'x_t-2'}: x_t-1), ...]
stream = [0]

i = len(dataset)
MIN_TRAIN = 20  # construct first model on 20 samples at least
TRAIN_EVERY = 10
batch_rmse, river_rmse = [], []
#fig = plt.figure()
#is_plotted = False

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
		#X_t = stream[-2]  # feature is the x_t-1
		#y_t = stream[-1]  # target is x_t
		Forecaster.learn_one(x=None, y=closing_stock)  # learn on this set
		# create set for sklearn linear regressor
		#x_batch = [el[0]['x'] for el in dataset]
		#y_batch = [el[1] for el in dataset]

	else:
		stream.append(closing_stock)
		dataset.append(({'x': stream[-2]}, stream[-1]))
		y_pred = Forcaster.forecast(x=[closing_stock], horizon=1)
		Forcaster.learn_one(x=None, y=closing_stock)
		print(y_pred)
