import json
import time
import ast 
from kafka import KafkaProducer
from kafka import KafkaConsumer
from river import linear_model
from river import preprocessing



RECEIVE_FROM = "stocks_test"

consumer = KafkaConsumer(RECEIVE_FROM, bootstrap_servers="localhost:9092", group_id="group-1")

model = (
	preprocessing.StandardScaler() |
	linear_model.LinearRegression(intercept_lr=.1)
	)
stream = [0]
X_test = []
y_true = [] 
y_preds = []

i = 0
for message in consumer:
	if i < 150:
	    stocks_info = message.value
	    closing_stock = ast.literal_eval(stocks_info.decode('UTF-8'))['Close']

	    # fun begins
	    if len(stream)<100:
	    	stream.append(closing_stock)
	    	X_t = stream[-2] # feature is the x_t-1
	    	y_t = stream[-1] # target is x_t
	    	model = model.learn_one(X_t, y_t) # learn on this set
	    else:
		    # predict after training model on at least 100 data points
		    stream.append(closing_stock) 

		    X_test.append(closing_stock) # we predict on x_t
		    
		    y_preds.append(model.predict_one(closing_stock)) # predict on x_t

		    if not bool(y_true):
		    	y_true.append(0)
		    else:
		    	y_true.append(closing_stock)

        i += 1

	else:
		break

print(len(X_test), X_test)
print(len(y_true), y_true)
print(len(y_preds), y_preds)

	    





