#import requests
import time
import json
import urllib.request
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers="localhost:9092")
topic_name = "stocks_test"

url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=S&P500&interval=1min&apikey=L942U7S3DKW2G7J5'

'''r = requests.get(url)
data = r.json()

print(data)'''

while True:
    message = urllib.request.urlopen(url)
    stocks_info = json.loads(message.read().decode('utf-8')) 
    msg = json.dumps(stocks_info).encode('utf-8')
    
    producer.send(topic_name, msg)
    print('----------------------')
    print(f"Sending {len(stocks_info)} stocks info to topic: {topic_name} at time {time.time()}") 
    print(stocks_info['Time Series (1min)'].keys())
    time.sleep(60)
    