from .perceptron import *
import codecs
import random
import time

class SemDepParser(object):
    def __init__(self):
        self.train_set = []
        self.test_set = []
        self.label_set = set()
        self.transition_set = []
        self.feature_set = set()

    def loadSet(self):
        self.transition_set += ['SHIFT', 'REDUCE', 'MEM', 'RECALL']
        for label in self.label_set:
            self.transition_set.append('ARC-' + label + '-SHIFT')
            self.transition_set.append('ARC-' + label + '-REDUCE')
            self.transition_set.append('ARC-' + label + '-MEM')
            self.transition_set.append('ARC-' + label + '-RECALL')
        self.classifier = Perceptron(self.transition_set)

    def preprocess(self):
        readFile(self.train_set, self.label_set)
        self.loadSet()
        length = 0
        for graph in self.train_set:
            #print(graph.rowNum)
            config = Configuration(graph.V)
            graph.oracle = config.extractOracle(graph)
            length = max(length,len(graph.oracle))
            if graph.oracle[0] != 'SHIFT': # the first oracle is always SHIFT
                print('not shift')
            #if graph.rowNum == '#20015004':
            #print(graph.oracle)
        print('maximal oracle length', length)

        for graph in self.train_set:
            config = Configuration(graph.V)
            config.doAction(graph.oracle[0])
            for action in graph.oracle[1:]:
                feature = config.extractFeature(graph, action)
                for f in feature:
                    self.feature_set.add(f)
                graph.gold_feature.append((action, feature))
                config.doAction(action)
        print('feature set', len(self.feature_set))

    def train(self):
        t1 = time.time()
        for T in range(1):
            random.shuffle(self.train_set)
            for graph in self.train_set[:100]:
                print(graph.rowNum)
                self.classifier.train(graph)
            self.classifier.store()
        t2 = time.time()
        print('training finished in %f s' % (t2 - t1))

    def parse(self):
        self.classifier.load()
        self.test_set = self.train_set[:2]
        for graph in self.test_set:
            self.classifier.predict(graph)


def readFile(train_set, label_set):
    path = 'G:\课程资料\大三（下）\EMNLP\\assignment2\dm.sdp'
    f = codecs.open(path, 'r', encoding='utf-8')
    graph = Graph()
    table = []
    rootcnt = 0
    for line in f.readlines():
        line = line.strip()
        if not line:
            buildArc(table, graph)
            #graph.buildTable()
            for edge in graph.E:
                label_set.add(edge.label)
            train_set.append(graph)
            if rootcnt == 0:
                print(graph.rowNum, 'no root')
            graph = Graph()
            table = []
            rootcnt = 0
        elif line[0] == '#':
            graph.rowNum = line
        else:
            line = line.split('\t')
            graph.V.append(Node(int(line[0]), line[1], line[2], line[3]))
            if line[4] == '+':
                rootcnt += 1
                if rootcnt > 1:
                    print(len(train_set), "multiple root")
                graph.E.append(Edge(graph.V[0], graph.V[len(graph.V)-1], 'L_'))
            if line[5] == '+':
                graph.headNodes.append(len(graph.V)-1)
            table.append(line[6:])
    buildArc(table, graph)
    for edge in graph.E:
        label_set.add(edge.label)
    train_set.append(graph)
    print('train_set size', len(train_set))
    print('label_set size', len(label_set))

def buildArc(table, graph):
    for i in range(len(table)):
        for j in range(len(table[0])):
            if table[i][j] == '_':
                continue
            label = table[i][j]
            k = graph.headNodes[j + 1]
            if k > i + 1:
                label = 'L_' + label
            elif k < i + 1:
                label = 'R_' + label
            else:
                print(label, graph.rowNum)
            graph.E.append(Edge(graph.V[k], graph.V[i + 1], label))
