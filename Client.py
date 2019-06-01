import socketio
import json
import pandas as pd
import numpy as np
from Dependent import Event, SplitEvents, MaxSimilarity
# import Independent

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('connection established')

@sio.on('disconnect')
def on_disconnect():
    print('disconnected from server')


# ID, Hand, throwtimes, stepstohu, isting, otherting, safebefore, actions, deadcards
@sio.on("gossipInfo")
def GossipInfo(info):
    # info = bytes(info, 'utf-8')
    # info = json.loads(info)
    
    # continuous_event = []
    # for event in info['Actions']:
    #     continuous_event.append(Event(event['Turn'], event['Action'], event['FromWho'], event['Card']))
    #     if len(continuous_event) >= 16:
    #         continuous_event.pop(0)

    # split_events = SplitEvents(continuous_event)
    # similarity_event, similarity, situation, from_same_player = MaxSimilarity(split_events)
    
    # if situation != None:
    #     return info['Id'], situation

    # pid, situation = CheckDependent(info)
    # if situation != None:
    #     return pid, situation
    logs = pd.read_csv("./testdata/test1.csv", encoding='cp950')
    continuous_event = []
    for index, event in logs.iterrows():
        if pd.isna(event['action']):
            continuous_event.clear()
            continue
        continuous_event.append(Event(event['turn'], event['action'], event['from_who'], event['card']))
        if len(continuous_event) >= 16:
            continuous_event.pop(0)
        
    split_events = SplitEvents(continuous_event)
    similarity_event, similarity, situation, from_same_player = MaxSimilarity(split_events)
    print(situation)
    return 0, situation
    

    
def ack(msg):
    print(msg)

if __name__ == '__main__':
    sio.connect('http://localhost:3000', transports=['websocket'])
    sio.emit('gossip', callback=ack)
    sio.wait()