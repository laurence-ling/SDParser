from collections import deque
from .graph import *

class Stack(object):
    def __init__(self):
        self.stack = deque()
    def __len__(self):
        return len(self.stack)
    def pop(self):
        return self.stack.pop()
    def push(self, arg):
        self.stack.append(arg)
    def isEmpty(self):
        return len(self.stack) == 0
    def top(self):
        assert len(self.stack) > 0
        return self.stack[len(self.stack)-1]
    def subTop(self):
        assert len(self.stack) > 1
        return self.stack[len(self.stack)-2]
    def clear(self):
        self.stack.clear()
    def getAll(self):
        return list(self.stack)

class Queue(object):
    def __init__(self):
        self.queue = deque()
    def push_back(self, arg):
        self.queue.append(arg)
    def push_front(self, arg):
        self.queue.appendleft(arg)
    def front(self):
        return self.queue[0]
    def isEmpty(self):
        return len(self.queue) == 0
    def pop_front(self):
        return self.queue.popleft()
    def clear(self):
        self.queue.clear()

class Configuration(object):
    def __init__(self, sent):
        self.stack = Stack()
        self.buffer = Queue()
        self.memory = Stack()
        self.arcs = []
        self.goldArc = []
        assert isinstance(sent, list)
        for node in sent:
            self.buffer.push_back(node)

    def initialize(self, sent):
        self.stack.clear()
        self.memory.clear()
        self.buffer.clear()
        self.arcs.clear()

    def isTerminated(self):
        return self.buffer.isEmpty()

    def doAction(self, action):
        if action == 'SHIFT':
            if not self.buffer.isEmpty():
                node = self.buffer.pop_front()
                self.stack.push(node)
        elif action == 'REDUCE':
            if not self.stack.isEmpty():
                self.stack.pop()
        elif action == 'SWAP':
            node_j = self.stack.pop()
            node_i = self.stack.pop()
            self.buffer.push_front(node_i)
            self.stack.push(node_j)
        elif action == 'MEM':
            if not self.stack.isEmpty():
                node = self.stack.pop()
                self.memory.push(node)
        elif action == 'RECALL':
            if not self.memory.isEmpty():
                node = self.memory.pop()
                self.stack.push(node)
        elif action[:3] == 'ARC':
            action = action.split('-')
            label = action[1]
            next_action = action[2]
            if not self.stack.isEmpty() and not self.buffer.isEmpty():
                top = self.stack.top()
                front = self.buffer.front()
                self.arcs.append(Edge(top, front, label))
            self.doAction(next_action)

    def extractOracle(self, graph):
        self.goldArc = graph.E[:]
        oracle = []
        while(True):
            t = self.extractOneOracle(None)
            if t == None:
                break
            oracle.append(t)
            self.doAction(t)
        for edge in graph.E:
            if not edge in self.arcs:
                print('No oracle', len(graph.E), len(self.arcs), edge.src.id, edge.dst.id, edge.label)
        return oracle

    def extractOneOracle(self, label):
        if not self.stack.isEmpty() and not self.buffer.isEmpty():
            top = self.stack.top()
            front = self.buffer.front()
            if self.reduceCondition(top.id, front.id):
                if label == None:
                    return 'REDUCE'
                else:
                    return 'ARC-' + label + '-REDUCE'
            e = self.arcCondition(top.id, front.id)
            if e is not None:
                self.goldArc.remove(e)
                return self.extractOneOracle(e.label)
            if self.memCondition(top.id, front.id):
                if label == None:
                    return 'MEM'
                else:
                    return 'ARC-' + label + '-MEM'
        if not self.memory.isEmpty():
            if label == None:
                return 'RECALL'
            else:
                return 'ARC-' + label + '-RECALL'
        if not self.buffer.isEmpty():
            if label == None:
                return 'SHIFT'
            else:
                return 'ARC-' + label + '-SHIFT'
        return None

    def reduceCondition(self, i, j):
        for edge in self.goldArc:
            if edge.src.id == i and edge.dst.id >= j:
                return False
            if edge.dst.id == i and edge.src.id >= j:
                return False
        return True

    def arcCondition(self, i, j):
        for edge in self.goldArc:
            if edge.dst.id == i and edge.src.id == j:
                return edge
            elif edge.src.id == i and edge.dst.id == j:
                return edge
        return None

    def memCondition(self, i, j):
        for node in self.stack.getAll()[:-1]:
            for edge in self.goldArc:
                if edge.src.id == node.id and edge.dst.id == j:
                    return True
                elif edge.dst.id == node.id and edge.src.id == j:
                    return True
        return False

    def extractFeature(self, graph, action):
        features = []
        top = None
        front = None
        mTop = None
        subTop = None
        # unigrams
        if not self.stack.isEmpty():
            top = self.stack.top()
            features += self.unigram('ST', top)
        if not self.buffer.isEmpty():
            front = self.buffer.front()
            features += self.unigram('N0', front)
        if not self.memory.isEmpty():
            mTop = self.memory.top()
            features += self.unigram('M', mTop)
        if len(self.stack) >= 2:
            subTop = self.stack.subTop()
            features += self.unigram('SST', subTop)

        # context
        if top is not None:
            features += self.context('ST', top, graph)
        if front is not None:
            features += self.context('N0', front, graph)

        # pair
        if top is not None and front is not None:
            features += self.pair('ST', top, 'N0', front)
        if subTop is not None and front is not None:
            features += self.pair('SST', subTop, 'N0', front)
        if mTop is not None and front is not None:
            features += self.pair('M', mTop, 'N0', front)

        features = [f + '&' + action for f in features]
        return features

    def leftmostParent(self, node):
        parents = [edge.src for edge in self.arcs if edge.dst.id == node.id]
        if not parents:
            return (None, None)
        result = min(parents, key=lambda n: n.id)
        label = [edge.label for edge in self.arcs if edge.dst.id == node.id and edge.src.id == result.id]
        return (result, label[0])

    def rightmostParent(self, node):
        parents = [edge.src for edge in self.arcs if edge.dst.id == node.id]
        if not parents:
            return (None, None)
        result = max(parents, key=lambda n: n.id)
        label = [edge.label for edge in self.arcs if edge.dst.id == node.id and edge.src.id == result.id]
        return (result, label[0])

    def leftmostChild(self, node):
        children = [edge.dst for edge in self.arcs if edge.src.id == node.id]
        if not children:
            return (None, None)
        result = min(children, key=lambda n: n.id)
        label = [edge.label for edge in self.arcs if edge.src.id == node.id and edge.dst.id == result.id]
        return (result, label[0])

    def rightmostChild(self, node):
        children = [edge.dst for edge in self.arcs if edge.src.id == node.id]
        if not children:
            return (None, None)
        result = max(children, key=lambda n: n.id)
        label = [edge.label for edge in self.arcs if edge.src.id == node.id and edge.dst.id == result.id]
        return (result, label[0])

    def unigram(self, tag, node):
        v = []
        v.append(tag + 'w-' + node.word)
        v.append(tag + 't-' + node.posTag)
        v.append(tag + 'wt-' + node.word + node.posTag)
        lmParent, lpLabel = self.leftmostParent(node)
        rmParent, rpLabel = self.rightmostParent(node)
        lmChild, lcLabel = self.leftmostChild(node)
        rmChild, rcLabel = self.rightmostChild(node)
        if lmParent is not None:
            v.append(tag + 'wLPt-' + node.word + lmParent.posTag)
            v.append(tag + 'tLPt-' + node.posTag + '-' + lmParent.posTag)
            v.append(tag + 'wLPl-' + node.word + '-' + lpLabel)
        if rmParent is not None:
            v.append(tag + 'wRPt-' + node.word + rmParent.posTag)
            v.append(tag + 'tRPt-' + node.posTag + '-' + rmParent.posTag)
            v.append(tag + 'wRPl-' + node.word + '-' + rpLabel)
        if lmChild is not None:
            v.append(tag + 'wLCt-' + node.word + lmChild.posTag)
            v.append(tag + 'tLCt-' + node.posTag + '-' + lmChild.posTag)
            v.append(tag + 'wLCw-' + node.word + '-' + lmChild.word)
            v.append(tag + 'wLCl-' + node.word + '-' + lcLabel)
        if rmChild is not None:
            v.append(tag + 'wRCt-' + node.word + rmChild.posTag)
            v.append(tag + 'tRCt-' + node.posTag + '-' + rmChild.posTag)
            v.append(tag + 'wRCw-' + node.word + '-' + rmChild.word)
            v.append(tag + 'wRCl-' + node.word + '-' + rcLabel)
        return v

    def pair(self, t1, x, t2, y):
        v = []
        v.append(t1 + 'w' + t2 + 'w-' + x.word + '-' + y.word)
        v.append(t1 + 't' + t2 + 't-' + x.posTag + '-' + y.posTag)
        v.append(t1 + 'wt' + t2 + 'wt-' + x.word + x.posTag + '-' + y.word + y.posTag)
        v.append(t1 + 'wt' + t2 + 'w-' + x.word + x.posTag + '-' + y.word)
        v.append(t1 + 'wt' + t2 + 't-' + x.word + x.posTag + '-' + y.posTag)
        v.append(t1 + 'w' + t2 + 'wt-' + x.word +  '-' + y.word + y.posTag)
        v.append(t1 + 't' + t2 + 'wt-' + x.posTag + '-' + y.word + y.posTag)
        v.append(t1 + 't' + t2 + 'w-' + x.posTag + '-' + y.word)
        v.append(t1 + 'w' + t2 + 't-' + x.word + '-' + y.posTag)
        x_lc, xlc_label = self.leftmostChild(x)
        x_rc, xrc_label = self.rightmostChild(x)
        y_lc, ylc_label = self.leftmostChild(y)
        if x_lc is not None:
            v.append(t1 + 'w' + t2 + 'w' + 'XLCt-' + x.word + '-' + y.word + x_lc.posTag)
            v.append(t1 + 'p' + t2 + 'p' + 'XLCt-' + x.posTag + '-' + y.posTag + '-' + x_lc.posTag)
        if x_rc is not None:
            v.append(t1 + 'w' + t2 + 'w' + 'XRCt-' + x.word + '-' + y.word + x_rc.posTag)
            v.append(t1 + 'p' + t2 + 'p' + 'XRCt-' + x.posTag + '-' + y.posTag + '-' + x_rc.posTag)
        if y_lc is not None:
            v.append(t1 + 'w' + t2 + 'w' + 'YLCt-' + x.word + '-' + y.word + y_lc.posTag)
            v.append(t1 + 'p' + t2 + 'p' + 'YLCt-' + x.posTag + '-' + y.posTag + '-' + y_lc.posTag)
        return v

    def context(self, tag, x, graph):
        v = []
        L1 = None
        L2 = None
        R1 = None
        R2 = None
        if x.id > 0:
            L1 = graph.V[x.id - 1]
            v.append(tag + 'L1w-' + L1.word)
            v.append(tag + 'L1t-' + L1.posTag)
        if x.id < len(graph.V) - 1:
            R1 = graph.V[x.id + 1]
            v.append(tag + 'R1w-' + R1.word)
            v.append(tag + 'R1t-' + R1.posTag)
        if x.id > 1:
            L2 = graph.V[x.id - 2]
            v.append(tag + 'L2w-' + L2.word)
            v.append(tag + 'L2t-' + L2.posTag)
        if x.id < len(graph.V) - 2:
            R2 = graph.V[x.id + 2]
            v.append(tag + 'R2w-' + R2.word)
            v.append(tag + 'R2t-' + R2.posTag)
        if L1 is not None and L2 is not None:
            v.append(tag + 'L2wL1w-' + L2.word + '-' + L1.word)
            v.append(tag + 'L2tL1t-' + L2.posTag + '-' + L1.posTag)
        if R1 is not None and R2 is not None:
            v.append(tag + 'R1wR2w-' + R1.word + '-' + R2.word)
            v.append(tag + 'R1tR2t-' + R1.posTag + '-' + R2.posTag)
        if L1 is not None and R1 is not None:
            v.append(tag + 'L1wR1w-' + L1.word + '-' + R1.word)
            v.append(tag + 'L1tR1t-' + L1.posTag + '-' + R1.posTag)
        return v