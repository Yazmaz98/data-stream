from pprint import pprint
from river import datasets

dataset = datasets.Phishing()

for x, y in dataset:
    pprint(x)
    print(y)
    break

