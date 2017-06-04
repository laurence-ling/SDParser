from .state import *
import copy
import random
import pickle

class Perceptron(object):
    def __init__(self, _set):
        self.weight = {}
        self.action_set = _set

    def store(self):
        f = open('weight', 'wb')
        pickle.dump(self.weight, f)

    def load(self):
        f = open('weight', 'rb')
        self.weight = pickle.load(f)

    def train(self, graph):
        self.state = 'T'
        item = self.beamSearch(graph)
        if self.state != 'U':
            self.update(item.feature_vec, graph)

    def predict(self, graph):
        self.state = 'P'
        item = self.beamSearch(graph)
        graph.E = item.config.arcs
        graph.oracle = item.action_list

    def getScore(self, feature):
        score = 0
        for f in feature:
            if f in self.weight.keys():
                score += self.weight[f]
        return score

    def update(self, features, graph):
        gold = []
        for ele in graph.gold_feature:
            gold += ele[1]
        for f in gold:
            if f in self.weight.keys():
                self.weight[f] += 1
            else:
                self.weight[f] = 1
        for f in features:
            if f in self.weight.keys():
                self.weight[f] -= 1
            else:
                self.weight[f] = -1

    def canEarlyUpdate(self):
        return False

    def beamSearch(self, graph):
        agenda = [Item(graph)]
        terminate = []
        B = 8
        depth = 186 # maximal searching depth
        if self.state == 'T':
            depth = len(graph.oracle)
        for i in range(1, depth):
            new_agenda = []
            for item in agenda:
                if item.config.isTerminated():
                    terminate.append(item)
                    continue
                candidates = []
                for action in self.action_set:
                    feature = item.config.extractFeature(graph, action)
                    score = self.getScore(feature)
                    candidates.append((score, action, feature))
                random.shuffle(candidates)
                candidates = sorted(candidates, key=lambda x: x[0])[:B]
                for c in candidates:
                    new_item = copy.deepcopy(item)
                    new_item.add(c[0], c[1], c[2])
                    if self.state == 'T':
                        new_item.config.doAction(graph.oracle[i])
                    else:
                        new_item.config.doAction(c[1])
                    new_agenda.append(new_item)
            if not new_agenda: # all terminated
                break
            new_agenda += terminate # also consider terminated ones
            random.shuffle(new_agenda)
            agenda = sorted(new_agenda, key=lambda x: x.score)[:B]
            # perform early update
            if self.state == 'T' and self.canEarlyUpdate():
                item = max(agenda, key=lambda x: x.score)
                self.update(item.feature_vec, graph)
                self.state = 'U'
                return item
        return max(agenda, key=lambda x: x.score)


class Item(object):
    def __init__(self, graph):
        self.config = Configuration(graph.V)
        self.config.doAction('SHIFT')
        self.action_list = ['SHIFT']
        self.feature_vec = []
        self.score = 0
    def add(self, score, action, feature):
        self.score += score
        self.action_list.append(action)
        self.feature_vec += feature