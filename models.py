import json
import time
import ast
import random
import numpy as np
import matplotlib.pyplot as plt
import pmdarima as pm

import yfinance as yf
import time
import json
import urllib.request

from sklearn.metrics import mean_squared_error
from kafka import KafkaProducer
from kafka import KafkaConsumer
from river import linear_model, ensemble, tree, preprocessing, evaluate, metrics, time_series, optim
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

# statsmodels version: 0.13
from statsmodels.tsa.arima.model import ARIMA
from tqdm import tqdm

from ARIMA_model import ARIMA_model, create_dataset

STOCK_NAME = 'stocks_test'
consumer = KafkaConsumer(STOCK_NAME, bootstrap_servers="localhost:9092", group_id="group-1")

# LINEAR MODEL FROM RIVER
river_lm = (
	preprocessing.StandardScaler() |
	linear_model.LinearRegression(intercept_lr=.1)
	)
# BAGGING REGRESSOR FROM RIVER
river_bagging_trees = preprocessing.StandardScaler()
river_bagging_trees |= ensemble.BaggingRegressor(
	model=linear_model.LinearRegression(intercept_lr=0.1),
	n_models=3,
	seed=42
)
# HOEFFDING REGRESSOR FROM RIVER
river_hoeffding = (
		preprocessing.StandardScaler() |
		tree.HoeffdingTreeRegressor(
			grace_period=100,
			leaf_prediction='adaptive',
			model_selector_decay=0.9
		)
)
# SNARIMAX FROM RIVER
snarimax = (
	time_series.SNARIMAX(
		p=0,
		d=0,
		q=0,
		m=12,
		sp=3,
		sq=6,
		regressor=(
			preprocessing.StandardScaler() |
			linear_model.LinearRegression(
				intercept_init=110,
				optimizer=optim.SGD(0.01),
				intercept_lr=0.3
			)
		)
	)
)

metric = metrics.RMSE()

dataset = []  # [({'x_t-1'}: x_t), ({'x_t-2'}: x_t-1), ...]
stream = [0]

i = len(dataset)
MIN_TRAIN = 20  # construct first model on 20 samples at least
TRAIN_EVERY = 10
lm_rmse, river_lm_rmse = [], []
rf_rmse, rbt_rmse, hfdg_rmse = [], [], []
arima_rmse, river_ts_rmse = [], []

y_lm, y_rlm, y_rf, y_rbt, y_rhfdg, y_arima, y_snarimax = [], [], [], [], [], [], []

fig = plt.figure()
is_plotted = False
ax1, ax2 = fig.subplots(2)

for message in consumer:
	print(f'dataset currently has {i+1} elements: {dataset}')
	#stocks_info = message.value
	#closing_stock = ast.literal_eval(stocks_info.decode('UTF-8'))['Close']
	closing_stock = random.uniform(300, 301)

	if len(dataset) < MIN_TRAIN:
		stream.append(closing_stock)
		if not bool(dataset):
			dataset.append(({'x': closing_stock}, closing_stock))  # first label is itself because we don't have x_t-1
		else:
			dataset.append(({'x': stream[-2]}, stream[-1]))
		X_t = stream[-2]  # feature is the x_t-1
		y_t = stream[-1]  # target is x_t
		# -------- training online models before making preds------
		river_bagging_trees = river_bagging_trees.learn_one({'x': X_t}, y_t)  # learn on this set
		river_hoeffding = river_hoeffding.learn_one({'x': X_t}, y_t)
		river_lm = river_lm.learn_one({'x': X_t}, y_t)
		snarimax = snarimax.learn_one(y=y_t)
		# ---------------------------------------------------------

		# create set for sklearn linear regressor
		x_batch = [el[0]['x'] for el in dataset]
		y_batch = [el[1] for el in dataset]

	else:
		stream.append(closing_stock)
		dataset.append(({'x': stream[-2]}, stream[-1]))
		# ---------teach online models--------------
		river_bagging_trees = river_bagging_trees.learn_one({'x': stream[-2]}, stream[-1])
		river_hoeffding = river_hoeffding.learn_one({'x': stream[-2]}, stream[-1])
		river_lm = river_lm.learn_one({'x': stream[-2]}, stream[-1])
		snarimax = snarimax.learn_one(y=stream[-1])
		# ------------------------------------------
		x_batch.append(stream[-2])
		y_batch.append(stream[-1])
		if (i > MIN_TRAIN) and (i % TRAIN_EVERY == 0):
			# ---------teach batch models--------------
			lm = LinearRegression().fit(np.array(x_batch[:-TRAIN_EVERY]).reshape(-1, 1), y_batch[:-TRAIN_EVERY])
			rf = RandomForestRegressor().fit(np.array(x_batch[:-TRAIN_EVERY]).reshape(-1, 1), y_batch[:-TRAIN_EVERY])
			# ------------------------------------------

			X_test, y_test = x_batch[-TRAIN_EVERY:], y_batch[-TRAIN_EVERY:]

			# ---------batch models predictions--------------
			y_pred_rf = rf.predict(np.array(X_test).reshape(-1, 1))
			y_pred_lm = lm.predict(np.array(X_test).reshape(-1, 1))
			# ------------------------------------------

			# ---------ARIMA batch model fitted and predicted-
			arima_model = ARIMA_model(6, 1, 0)
			X_train_arima, _ = create_dataset(x_batch, n_samples=len(x_batch) - TRAIN_EVERY - 1)
			y_pred_arima = arima_model.fit_predict(X_train_arima, y_test)
			# ------------------------------------------

			# ---------online models predictions--------------
			y_pred_river_lm = [river_lm.predict_one({'x': x}) for x in X_test]
			y_pred_river_rbt = [river_bagging_trees.predict_one({'x': x}) for x in X_test]
			y_pred_river_hfdg = [river_hoeffding.predict_one({'x': x}) for x in X_test]
			y_pred_river_snarimax = [snarimax.forecast(horizon=1, xs=None) for x in X_test]
			# ------------------------------------------

			# ---------linear models errors --------------
			print(f'Linear model RMSE (batch): {mean_squared_error(y_test, y_pred_lm)}')
			print(f'River linear model RMSE (batch): {mean_squared_error(y_test, y_pred_river_lm)}')
			# ------------------------------------------

			# ---------trees models errors --------------
			print(f'Random forest RMSE (batch): {mean_squared_error(y_test, y_pred_rf)}')
			print(f'Bagging trees RMSE (river): {mean_squared_error(y_test, y_pred_river_rbt)}')
			print(f'Hoeffding regressor RMSE (river): {mean_squared_error(y_test, y_pred_river_hfdg)}')
			# ------------------------------------------

			# ---------Time series models errors --------------
			print(f'SNARIMAX RMSE (river): {mean_squared_error(y_test, y_pred_river_snarimax)}')
			print(f'ARIMA RMSE (batch): {mean_squared_error(y_test, y_pred_arima)}')
			# ------------------------------------------

			# --------- errors list for plots --------------
			lm_rmse.append(mean_squared_error(y_test, y_pred_lm))
			river_lm_rmse.append(mean_squared_error(y_test, y_pred_river_lm))
			# ---
			rf_rmse.append(mean_squared_error(y_test, y_pred_rf))
			rbt_rmse.append(mean_squared_error(y_test, y_pred_river_rbt))
			hfdg_rmse.append(mean_squared_error(y_test, y_pred_river_hfdg))
			# ---
			river_ts_rmse.append(mean_squared_error(y_test, y_pred_river_snarimax))
			arima_rmse.append(mean_squared_error(y_test, y_pred_arima))
			# ----------------------------------------------

			x_batch = x_batch + X_test
			y_batch = y_batch + y_test

			y_lm.extend(y_pred_lm)
			y_rlm.extend(y_pred_river_lm)
			y_rf.extend(y_pred_rf)
			y_rbt.extend(y_pred_river_rbt)
			y_rhfdg.extend(y_pred_river_hfdg)
			y_snarimax.extend(y_pred_river_snarimax)
			y_arima.extend(y_pred_arima)

			ax1.plot(
				stream[MIN_TRAIN + 1: -1], color='green', label='Stream data', linewidth=4
			)
			ax1.plot(y_lm, color='magenta', label='Linear model')
			ax1.plot(y_rlm, color='cyan', label='River linear model')
			ax1.plot(y_rf, color='yellow', label='Random forest')
			ax1.plot(y_rbt, color='red', label='River Bagging regressor')
			ax1.plot(y_rhfdg, color='blue', label='River Hoeffding tree regressor')
			ax1.plot(y_snarimax, color='black', label='River SNARIMAX model')
			ax1.plot(y_arima, color='brown', label='Batch ARIMA model')

			ax2.plot(lm_rmse, color='magenta', label='Linear model')
			ax2.plot(river_lm_rmse, color='cyan', label='River linear model')
			ax2.plot(rf_rmse, color='green', label='Random forest')
			ax2.plot(rbt_rmse, color='red', label='River Bagging regressor')
			ax2.plot(hfdg_rmse, color='blue', label='River Hoeffding tree regressor')
			ax2.plot(river_ts_rmse, color='black', label='River SNARIMAX model')
			ax2.plot(arima_rmse, color='brown', label='Batch ARIMA model')

			if not is_plotted:
				ax1.legend()
				ax2.legend()
				ax1.set_xlabel(f'Number of iterations (x{TRAIN_EVERY})')
				ax1.set_ylabel('Predictions')
				ax2.set_xlabel(f'Number of iterations (x{TRAIN_EVERY})')
				ax2.set_ylabel('RMSE')
				is_plotted = True
			plt.pause(TRAIN_EVERY)

	i += 1











