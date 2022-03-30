import yfinance as yf
import time
import json
import urllib.request
from kafka import KafkaProducer
import ast

producer = KafkaProducer(bootstrap_servers="localhost:9092")
topic_name = "stocks_test"

while True:
	ticker = yf.Ticker("MSFT")

	message_df = ticker.history(period="1d", interval="1m").iloc[-1]

	message = message_df.to_json(orient="index").encode("utf-8")
	closing_stock = ast.literal_eval(message.decode('UTF-8'))['Close']
	producer.send(topic_name, message)
	print('----------------------')
	print(f"Sending stocks info to topic: {topic_name} at time {time.time()}")
	print(message)

	time.sleep(5)





