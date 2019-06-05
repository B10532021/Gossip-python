import socketio
import json
import pandas as pd
import numpy as np
from Dependent import Event, SplitEvents, MaxSimilarity
from Independent import CheckInDependent
from pymongo import MongoClient
import random
from datetime import datetime
random.seed(datetime.now())
sio = socketio.Client()
client = MongoClient('localhost', 27017)
db = client.gossip

@sio.on('connect')
def on_connect():
    print('connection established')

@sio.on('disconnect')
def on_disconnect():
    print('disconnected from server')

@sio.on('logInfo')
def log(info):
    info = bytes(info, 'utf-8')
    info = json.loads(info)
    db.logs.insert(info)


# ID, Hand, throwtimes, stepstohu, isting, otherting, safebefore, actions, deadcards
@sio.on('gossipInfo')
def GossipInfo(info):
    info = bytes(info, 'utf-8')
    info = json.loads(info)
    print(info['CurAction'])
    # 相依事件
    continuous_event = []
    for event in info['Actions']:
        continuous_event.append(Event(event['Turn'], event['Action'], event['From'], event['Card']))
        if len(continuous_event) >= 16:
            continuous_event.pop(0)

    split_events = SplitEvents(continuous_event)
    similarity_event, similarity, situation, from_same_player = MaxSimilarity(split_events)

    sentences = list(db.sentences.find({'Situation': situation, '$or':[ {'Name':''}, {'Name':info['PlayerNames'][info['Id']]}]}))
    if sentences != []:
        print(situation, [x['Sentence'] for x in sentences])
        return info['Id'], sentences[random.randint(0, len(sentences) - 1)]['Sentence']

    # 獨立事件
    pid, situation = CheckInDependent(info)
    sentences = list(db.sentences.find({'Situation': situation, '$or':[ {'Name':''}, {'Name':info['PlayerNames'][pid]}]}))
    
    if sentences != []:
        print(situation, [x['Sentence'] for x in sentences])
        return pid, sentences[random.randint(0, len(sentences) - 1)]['Sentence']
    
    return info['Id'], None


@sio.on('throwCardInfo')
def Throw(info):
    info = bytes(info, 'utf-8')
    info = json.loads(info)
    print(info['Card'])
    # 打牌
    sentences = list(db.sentences.find({'Situation': info['Card'], '$or':[ {'Name':''}, {'Name':info['PlayerNames'][info['Id']]}]}))
    if sentences != []:
        print(info['Card'], [x['Sentence'] for x in sentences])
        return info['Id'], sentences[random.randint(0, len(sentences) - 1)]['Sentence']

    
def ack(msg):
    print(msg)

if __name__ == '__main__':
    sio.connect('http://localhost:3000', transports=['websocket'])
    sio.emit('gossip', callback=ack)
    sio.wait()