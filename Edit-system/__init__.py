from .generation import GenerateKeywords
from .generation import generate_sentence
import bottle
import server.web_api_routes
import sys
import os

path_of_synonym_dict = os.path.dirname(__file__) + r'/generation/synonyms_tw.txt'


def training(data, answer):
    gk = GenerateKeywords(data, answer)
    gk.hierarchical_clustering(0.48)


def start_server(ip, port):
    if len(sys.argv) == 1:
        bottle.run(host=ip, port=port, server='waitress', debug=False)
    else:
        bottle.run(host=ip, port=port)
