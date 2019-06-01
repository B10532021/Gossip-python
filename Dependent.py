import pandas as pd
import numpy as np
import json
import math
import time

Convert = dict({
    'Throw':'丟',
    'Draw':'摸',
    'SubTingNum':'進牌',
    'Eat':'吃',
    'CantEat':'吃不到',
    'Pon':'碰',
    'Gon':'槓',
    'OnGon':'暗槓',
    'PonGon':'加槓',
    'BaEat':'被吃',
    'BaPon':'被碰',
    'BaGon':'被槓',
    'Ting':'聽',
    'PassDraw':'被跳過',
    'Hu':'胡',
    'BaHu':'被胡'
})

with open("continuous_event2.json", 'r', encoding="utf-8") as f:
    datastore = json.load(f)

class Event(object):
    def __init__(self, turn=None, action=None, from_who=None, card=None):
        self.turn = turn
        self.action = action
        self.from_who = from_who
        self.card = card


def MaxSimilarity(split_events):
    similarity_score = []
    for key, values in datastore.items():
        for value in values:
            value = value.split(',')
            for split_event in split_events:
                if split_event[-1].action == value[-1]:
                    similarity_score.append([value, CalculateScore(split_event, value), key])
                    # print(value, CalculateScore(split_event, value))
    try:
        similar_event, similarity, situation, from_same_player = max(similarity_score, key=lambda x: x[1])
        if similarity < 0.6:
            return [], 0, None, False
        return similar_event, similarity, situation, from_same_player
    except Exception:
        return [], 0, None, False


def CalculateScore(query_event, event):
    max_weight = query_event[-1].turn
    x_len = len(query_event)
    y_len = len(event)
    num = np.zeros((x_len + 1, y_len + 1))
    check = np.zeros((x_len + 1, y_len + 1))
    max_length = 0

    for i in range(1, x_len + 1):
        for j in range(1, y_len + 1):
            if query_event[i - 1].action == event[j - 1]:
                add =  (query_event[i - 1].turn - query_event[0].turn + 1) / (max_weight - query_event[0].turn + 1)
                # if query_event[i - 1].action == '摸' or query_event[i - 1].action == '丟':
                #     add *= 0.3

                num[i, j] = 1 * add + num[i - 1, j - 1]
                check[i, j] = 1 # 來自左上
            else:
                if num[i - 1, j] < num[i, j - 1]:
                    num[i, j] = num[i, j - 1]
                    check[i, j] = 2 # 來自左方
                else:
                    num[i, j] = num[i - 1, j]
                    check[i, j] = 3 # 來自上方


    max_length = num[-1][-1]
    LCSS = max_length / len(event)# ((len(query_event) + len(event)) / 2) / max(len(query_event), len(event)) 
    lack_num = DiffNumOfAction(query_event, event)

    NAT = NoActionTurn(query_event)
    std = STD(query_event, check, x_len, y_len)
    nor = std / 10 + 1

    similarity = LCSS / nor - lack_num - 0.1 * NAT
    return similarity, CheckFromWho(query_event, check, x_len, y_len)

def STD(query_event, check, x_len, y_len):
    turn = []
    i = x_len
    j = y_len
    while i != 0 and j != 0:
        if check[i, j] == 1:
            turn.append(query_event[i - 1].turn)
            i -= 1
            j -= 1
        elif check[i, j] == 2:
            j -= 1
        elif check[i, j] == 3:
            i -= 1

    return np.std(turn)

def CheckFromWho(query_event, check, x_len, y_len):
    who = []
    i = x_len
    j = y_len
    while i != 0 and j != 0:
        if check[i, j] == 1:
            who.append(query_event[i - 1].from_who)
            i -= 1
            j -= 1
        elif check[i, j] == 2:
            j -= 1
        elif check[i, j] == 3:
            i -= 1

    if len(set(who)) == 1:
        return True

    return False

def SplitEvents(events):
    if len(events) > 16:
        event = event[len(event) - 16:]
    
    split = []
    for i in range(len(events) - 4, -1, -1):
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
    for key, value in count.items():
        if value > 0:
            lack += value
        else:
            enough += value

    return lack

def NoActionTurn(query_event):
    if query_event[-1] != '摸' and query_event[-1] != '丟':
        return 0
    else:
        for i in range(len(query_event) - 1, -1, -1):
            if query_event[i] == '吃' or query_event[i] == '碰' or query_event[i] == '聽'or query_event[i] == '槓' or query_event[i] == '暗槓' or query_event[i] == '加槓':
                return 1 - (query_event[-1].turn - query_event[i].turn) / (query_event[-1].turn - query_event[0].turn + 1)

    return 0


# for i in range(0, 3):
#     logs = pd.read_csv("./testdata/test2-"+ str(i) + ".csv", encoding='cp950')
#     continuous_event = []
#     for index, event in logs.iterrows():
#         if pd.isna(event['action']):
#             continuous_event.clear()
#             continue
#         continuous_event.append(Event(event['turn'], event['action'], event['from_who'], event['card']))
#         if len(continuous_event) >= 16:
#             continuous_event.pop(0)
        
#     split_events = SplitEvents(continuous_event)
#     similarity_event, similarity, situation, from_same_player = MaxSimilarity(split_events)
#     print(similarity_event)
#     print(similarity)
#     print("----------------------")

# logs = pd.read_csv("./testdata/real_testing.csv", encoding='cp950')
# # with open("test_{}.csv".format(time.strftime(r'%Y-%m-%d')), "a") as cout:
# with open("test_log.csv", "w") as cout:
#     continuous_event = []
#     for index, event in logs.iterrows():
#         if pd.isna(event['action']):
#             continuous_event.clear()
#             continue

#         continuous_event.append(Event(event['turn'], event['action'], event['from_who'], event['card']))
#         if len(continuous_event) >= 16:
#             continuous_event.pop(0)
        
#         split_events = SplitEvents(continuous_event)
#         similarity_event, similarity, situation, from_same_player = MaxSimilarity(split_events)
#         cout.write('、'.join(event.action for event in continuous_event) + "," + situation + ","
#                     + '、'.join(event for event in similarity_event) + "," + str(similarity) + '\n')
