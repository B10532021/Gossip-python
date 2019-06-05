import json
import random
from datetime import datetime


ToTile = dict({
	"c": 0,
	"d": 1,
	"b": 2,
	"o": 3, # 中發白、風
	"f": 4, # 花
})

def CheckInDependent(info):
	turn = info['Actions'][-1]['Turn']
	pid = info['Id']
	action = info['CurAction']
	card = info['Actions'][-1]['Card']
	hand = info['Hand']
	safe_before = info['SafeBefore']
	actions = info['Actions']
	deadcards = info['DeadCards']
    # convert card(string) to tile
	if action == "Throw":
		if info['OtherTing'] or turn >= 36 :
			if not CheckIsSafe(card, deadcards):
				action = "Dangerous"
			else:
				if card in safe_before:
					action = "Follow"

		# for i := 1; i < 3; i++ {
		# 	if otherPlayer := room.Players[(currentIdx+4-i)%4]; otherPlayer.CheckEat(card) {
		# 		otherPlayer.Hand.Add(card)
		# 		if otherPlayer.StepsToHu > otherPlayer.Hand.CountStepsToHu() {
		# 			room.BroadcastCoversation(otherPlayer.ID, "WantEat")
		# 		}
		# 		otherPlayer.Hand.Sub(card)
		# 	}
		# }

    # 別人前兩輪不是丟字牌
		elif info['ThrowTimes'] < 1 and ToTile[card[0]] != 3: 
			action = "ThrowGoodFirst"
			pid = (pid + random.randint(0, 3) + 1) % 4

	elif action == "Draw":
		if ToTile[card[0]] == 4:
			# if flowers := room.Players[currentIdx].Flowers.Count(); flowers >= 6:
			# 	if flowers == CountDeadCard(card):
			# 		action = "LotsOfFlowers"
			print(4)
		elif card in [action['Card'] for action in actions if action['Action'] == "Throw"]:
			action = "ThrowBefore"
		elif info['OtherTing'] or  turn >= 36:
			if CheckIsUseless(card, deadcards):
				if info['IsTing'] or info['StepsToHu'] <= 2:
					action = "Useless"
				else:
					action = "Safe"

	elif action == "Ting" and turn < 20:
		action += "Fast"

	elif action == "Pon" or action == "Eat" or action == "CantEat":
		if CheckLastNeed(card, deadcards, hand):
			action += "LastCard"

	# if action == "Dangerous" or action == "Follow" or action == "Ting" or action == "TingFast" or action == "Ongon" or action == "KeepWin":
	# 	action = "Other" + action

	return pid, action



def CheckIsUseless(card, deadcards):
	IsUseless = False
	amount = CountCard(card, deadcards)
	if amount >= 2:
		IsUseless = True
	return IsUseless


def CheckLastNeed(card, deadcards, hand):
	IsLast = False
	amount = CountCard(card, deadcards)
    # check pid's hand card
	amount += CountCard(card, hand)
	if amount == 4:
		IsLast = True
	return IsLast


def CheckIsSafe(card, deadcards):
	amount = CountCard(card, deadcards)
	if amount <= 2:
		return False
	elif amount >= 3:
		return True
	return True


def CheckKeepWin(keepwin):
	if keepwin:
		return True
	else:
		return False
	

def CountCard(card, cards):
	#convert card(string) to tile
	amount = cards[ToTile[card[0]]] >> (int(card[1]) * 3) & 7
	return amount