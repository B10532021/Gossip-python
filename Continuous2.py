import pandas as pd
import numpy as np
import json
import math
import time

with open("continuous_event2.json", 'r', encoding="utf-8") as f:
    datastore = json.load(f)

logs = pd.read_csv("2019-05-12-201433_Player0.csv", encoding='cp950')


class Event(object):
    def __init__(self, turn=None, action=None, from_who=None, card=None):
        self.turn = turn
        self.action = action
        self.from_who = from_who
        self.card = card


def MaxSimilarity(split_events):
    similarity_score = []
    print([event.action for event in split_events])
    for _, values in datastore.items():
        for value in values:
            value = value.split(',')
            if split_events[-1].action == value[-1]:
                similarity_score.append([value, CalculateScore(split_events, value)])
                # print(value, CalculateScore(split_events, value))
    
    try:
        similar_event, similarity = max(similarity_score, key=lambda x: x[1])
        return similar_event, similarity
    except Exception:
        return [], 0
    


def CalculateScore(query_event, event):
    max_weight = query_event[-1].turn
    x_len = len(query_event)
    y_len = len(event)
    num = np.zeros(x_len * y_len).reshape(x_len, y_len)
    max_length = 0

    for i in range(x_len):
        for j in range(y_len):
            if query_event[i].action == event[j]:
                add = query_event[i].turn / max_weight
                if query_event[i].action == '摸' or query_event[i].action == '丟':
                    add *= 0.5

                if i == 0 or j == 0:
                    num[i, j] = 1 * add
                else:
                    num[i, j] = 1 * add + num[i - 1, j - 1]
            else:
                num[i, j] = max(num[i - 1, j], num[i, j - 1])

    max_length = num[-1][-1]
    LCSS = max_length / len(event)
    # ((len(query_event) + len(event)) / 2) / max(len(query_event), len(event))

    enough_num, lack_num = DiffNumOfAction(query_event, event)

    if enough_num < 0:    
        enough_num = math.exp(enough_num)
    # print(LCSS, enough_num, lack_num)
    NAT = NoActionTurn(query_event)
    
    return 1.5 * LCSS + 0.05 * enough_num - 0.1 * lack_num - 0.1 * NAT


def SplitEvents(events):
    split = []
    for i in range(len(events) - 1, -1, -1):
        split.append(events[i:])

    return split


def DiffNumOfAction(query_events, events):
    count = dict()
    for event in events:
        if event == '丟' or event == '摸':
            continue
        elif event in count.keys():
            count[event] += 1
        else:
            count[event] = 1

    for event in query_events:
        if event.action == '丟' or event.action == '摸':
            continue
        elif event.action in count.keys():
            count[event.action] -= 1

    enough = 0
    lack = 0
    for _, value in count.items():
        if value > 0:
            lack += value
        else:
            enough += value

    return enough, lack


def NoActionTurn(query_event):
    if query_event[-1] != '摸' and query_event[-1] != '丟':
        return 0
    else:
        for i in range(len(query_event) - 1, -1, -1):
            if query_event[i] == '吃' or query_event[i] == '碰' or query_event[i] == '聽'or query_event[i] == '槓' or query_event[i] == '暗槓' or query_event[i] == '加槓':
                return query_event[i].turn / query_event[-1].turn

    return 0



with open("test2_{}.csv".format(time.strftime(r'%Y-%m-%d')), "a") as cout:
    continuous_event = []
    for index, event in logs.iterrows():
        if pd.isna(event['action']):
            continuous_event.clear()
            continue

        continuous_event.append(Event(event['turn'], event['action'], event['from_who'], event['card']))
        if len(continuous_event) >= 16:
            continuous_event.pop(0)
        
        split_events = SplitEvents(continuous_event)
        similarity_event, similarity = MaxSimilarity(continuous_event)
        cout.write('、'.join(event.action for event in continuous_event) + "," 
                    + '、'.join(event for event in similarity_event) + "," + str(similarity) + '\n')
        # print(similarity_event)
        # print(similarity)
        # print("----------------------")




