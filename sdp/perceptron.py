from .state import *
import copy
import random
import pickle

class Perceptron(object):
    def __init__(self, l_set, f_set):
        self.action_set = l_set
        self.weight = dict.fromkeys(f_set, 0)

    def store(self, T):
        f = open('weight' + str(T), 'wb')
        pickle.dump(self.weight, f)

    def load(self, T):
        f = open('weight' + str(T), 'rb')
        self.weight = pickle.load(f)

    def train(self, graph):
        self.state = 'T'
        item = self.beamSearch(graph)
        self.update(graph, item)

    def predict(self, graph):
        self.state = 'P'
        item = self.beamSearch(graph)
        graph.E = item.config.arcs
        graph.p_oracle = item.action_list

    def getScore(self, feature):
        score = 0
        for f in feature:
            if f in self.weight.keys():
                score += self.weight[f]
        return score

    def update(self, graph, item):
        i = 0
        length = min(len(graph.p_oracle), len(item.action_list))
        for i in range(length):
            if not graph.oracle[i] == item.action_list[i]:
                break
        gold = []
        train = []
        for ele in graph.gold_feature[i:]:
            gold += ele[1]
        for ele in item.feature_vec[i:]:
            train += ele[1]
        for f in gold:
            self.weight[f] += 1
        for f in train:
            if f in self.weight.keys():
                self.weight[f] -= 1

    def canEarlyUpdate(self, graph, agenda, i):
        flag = False
        for item in agenda:
            if item.promising and item.action_list[i] == graph.oracle[i]:
                item.promising = True
                flag = True
            else:
                item.promising = False
        if flag:
            return False
        return True

    def legalAction(self, config):
        legal = self.action_set
        if config.stack.isEmpty():
            temp = [x for x in self.action_set
                    if 'REDUCE' in x or 'ARC' in x or 'MEM' in x]
            legal = legal.difference(set(temp))
        if config.memory.isEmpty():
            temp = [x for x in self.action_set if 'RECALL' in x]
            legal = legal.difference(set(temp))
        return legal

    def beamSearch(self, graph):
        agenda = [Item(graph)]
        B = 4
        depth = 186 # maximal searching depth
        if self.state == 'T':
            depth = len(graph.oracle)
        for i in range(1, depth):
            new_agenda = []
            all_terminate = True
            for item in agenda:
                if item.config.isTerminated():
                    new_agenda.append(item)
                    continue
                all_terminate = False
                candidates = []
                legal_action = self.legalAction(item.config)
                for action in legal_action:
                    feature = item.config.extractFeature(graph, action)
                    score = self.getScore(feature)
                    candidates.append((score, action, feature))
                random.shuffle(candidates)
                candidates = sorted(candidates, key=lambda x: x[0], reverse=True)[:B]
                for c in candidates:
                    new_item = copy.deepcopy(item)
                    new_item.add(c[0], c[1], c[2])
                    if self.state == 'T':
                        new_item.config.doAction(graph.oracle[i])
                    else:
                        new_item.config.doAction(c[1])
                    new_agenda.append(new_item)
            if all_terminate: # all terminated
                break
            random.shuffle(new_agenda)
            agenda = sorted(new_agenda, key=lambda x: x.score, reverse=True)[:B]
            # perform early update
            if self.state == 'T' and self.canEarlyUpdate(graph, agenda, i):
                return max(agenda, key=lambda x: x.score)

        return max(agenda, key=lambda x: x.score)


class Item(object):
    def __init__(self, graph):
        self.config = Configuration(graph.V)
        self.config.doAction('SHIFT')
        self.action_list = ['SHIFT']
        self.feature_vec = []
        self.score = 0
        self.promising = True
    def add(self, score, action, feature):
        self.score += score
        self.action_list.append(action)
        self.feature_vec += (action, feature)