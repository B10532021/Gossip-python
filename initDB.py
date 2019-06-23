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
import random
from datetime import datetime
random.seed(datetime.now())

client = MongoClient('localhost', 27017)
db = client.gossip
# sentences = list(db.sentences.find({'Situation': "Pon", '$or':[ {'Name':''}, {'Name':"123"}]}))
# print(sentences[random.randint(0, len(sentences))]['Sentence'])

db.logs.remove()
collection = db.sentences
collection.remove({'Name': ''})

# conversation_dict = pd.read_csv('testdata/conversation.csv')
# for index, value in conversation_dict.iterrows():
#     data = {'uuid':index, 'Name': '', 'Situation': value['situation'],'Sentence': value['sentence']}
#     collection.insert(data)

with(open(r'testdata/conversation.json', 'r', encoding='utf-8')) as data:
    conversations = json.load(data)

uuid = 0
for key, values in conversations.items():
    for value in values:
        data = {'uuid':uuid, 'Name': '', 'Situation': key,'Events': value}
        collection.insert(data)
        uuid += 1

collection = db.situations
collection.remove()
with(open(r'continuous_event2.json', 'r', encoding='utf-8')) as data:
    continuous = json.load(data)

for index, (key, value) in enumerate(continuous.items()):
    data = {'uuid':index, 'Situation': key,'Events': value}
    collection.insert(data)