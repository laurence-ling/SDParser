from .state import *
import codecs

class SemDepParser(object):
    def __init__(self):
        self.train_set = []
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

    def train(self):
        readFile(self.train_set, self.label_set)
        for graph in self.train_set:
            config = Configuration(graph.V)
            graph.oracle = config.extractOracle(graph)
            #if graph.rowNum == '#20015004':
            print(graph.rowNum)
            #print(graph.oracle)

        for graph in self.train_set:
            config = Configuration(graph.V)
            config.doAction(graph.oracle[0])
            if graph.oracle[0] != 'SHIFT':
                print('not shift', graph.rowNum)
            for action in graph.oracle[1:]:
                feature = config.extractFeature(graph)
                for f in feature:
                    self.feature_set.add(f)
                config.doAction(action)
        print('feature set', len(self.feature_set))


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
