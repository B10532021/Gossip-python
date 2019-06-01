import pandas as pd
import json

temp = dict()

df = pd.read_csv('sentences.csv')
print(df)

for index, value in df.iterrows():
	if value['situation'] in temp.keys():
		temp[value['situation']].append(value['sentence'])
	else:
		temp[value['situation']] = [value['sentence']]

with(open(r'conversation.json', 'w', encoding='utf-8')) as data:
    json.dump(temp, data, indent = 2, ensure_ascii=False)