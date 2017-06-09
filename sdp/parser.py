from .perceptron import *
import codecs
import random
import time

class SemDepParser(object):
    def __init__(self):
        self.train_set = []
        self.test_set = []
        self.label_set = set()
        self.transition_set = set()
        self.feature_set = set()

    def preprocess(self):
        readFile(self.train_set, self.label_set)
        length = 0
        idx = 0
        for graph in self.train_set:
            #print(graph.rowNum)
            config = Configuration(graph.V)
            graph.oracle = config.extractOracle(graph)
            self.transition_set = self.transition_set.union(set(graph.oracle))
            length = max(length,len(graph.oracle))
            if graph.oracle[0] != 'SHIFT': # the first oracle is always SHIFT
                print('not shift')
            if graph.rowNum[:4] == '#200':
                idx += 1
            #print(graph.oracle)
        print('maximal oracle length', length)
        print('transition set size', len(self.transition_set))
        self.test_set = self.train_set[idx:]
        self.train_set = self.train_set[:idx]

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
        self.classifier = Perceptron(self.transition_set, self.feature_set)


    def train(self):
        t1 = time.time()
        for T in range(10):
            print('round', T)
            random.shuffle(self.train_set)
            for graph in self.train_set:
                print(graph.rowNum)
                self.classifier.train(graph)
            self.classifier.store(T)
        t2 = time.time()
        print('training finished in %f s' % (t2 - t1))

    def parse(self):
        self.classifier.load(2)
        self.test_set = self.train_set[:2]
        for graph in self.test_set:
            self.classifier.predict(graph)
            print(graph.rowNum)
            print(graph.oracle)
            print(graph.p_oracle)
        writeFile(self.test_set, 'resource/result.sdp')


def readFile(train_set, label_set):
    path = 'G:\课程资料\大三（下）\EMNLP\\assignment2\dm.sdp'
    f = codecs.open(path, 'r', encoding='utf-8')
    graph = Graph()
    table = []
    rootcnt = 0
    for line in f.readlines():
        line = line.strip()
        if not line:
            convertTableToArc(table, graph)
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
                graph.E.append(Edge(graph.V[0], graph.V[len(graph.V)-1], 'R_'))
            if line[5] == '+':
                graph.headNodes.append(len(graph.V)-1)
            table.append(line[6:])
    convertTableToArc(table, graph)
    for edge in graph.E:
        label_set.add(edge.label)
    train_set.append(graph)
    print('train_set size', len(train_set))
    print('label_set size', len(label_set))

def convertTableToArc(table, graph):
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

def convertArcToTable(graph):
    dependent = {}
    for edge in graph.E:
        if edge.src.id == 0:
            graph.topNodes.append(edge.dst.id)
        else:
            dependent.setdefault(edge.src.id, []).append(
                (edge.dst.id, edge.label.split('_')[1]))
    graph.headNodes = sorted(list(dependent.keys()))

    table = []
    for i in range(1, len(graph.V)):
        row = ['_'] * len(graph.headNodes)
        for j in range(len(graph.headNodes)):
            for (dst, label) in dependent[graph.headNodes[j]]:
                if dst == i:
                    row[j] = label
        table.append(row)
    return table

def writeFile(test_set, filename):
    f = codecs.open(filename, 'w', 'utf-8')
    for graph in test_set:
        f.write(graph.rowNum + '\n')
        table = convertArcToTable(graph)
        lines = []
        for i in range(len(table)):
            node = graph.V[i+1]
            row = [str(node.id), node.originForm, node.word, node.posTag]
            if i + 1 in graph.topNodes:
                row += ['+']
            else:
                row += ['-']
            if i + 1 in graph.headNodes:
                row += ['+']
            else:
                row += ['-']
            row += table[i]
            lines.append('\t'.join(row) + '\n')
        f.writelines(lines)
        f.write('\n')
    f.close()
