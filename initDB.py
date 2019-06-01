import sys
import os.path
import subprocess
import time
import datetime
import shutil
import unicodedata
import json
import pandas as pd
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.gossip
collection = db.sentences
collection.remove({'who': ''})

conversation_dict = pd.read_csv('sentences.csv')
for index, value in conversation_dict.iterrows():
    data = {'uuid':index, 'who': '', 'situation': value['situation'],'sentence': value['sentence']}
    collection.insert(data)

collection = db.situations
collection.remove()
with(open(r'continuous_event.json', 'r', encoding='utf-8')) as data:
    continuous = json.load(data)

index = 0
for key, values in continuous.items():
    for value in values:
        data = {'uuid':index, 'situation': key,'events': value}
        collection.insert(data)
        index += 1