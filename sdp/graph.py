
class Node(object):
    def __init__(self, _i, _o, _w, _p, _h=False):
        self.id = _i
        self.originForm = _o
        self.word = _w
        self.posTag = _p
        self.isHead = _h

class Edge(object):
    def __init__(self, _s, _d, _l):
        assert(isinstance(_s, Node))
        if _l[0] == 'L':
            if _s.id < _d.id:
                temp = _s
                _s = _d
                _d = temp
        if _l[0] == 'R':
            if _s.id > _d.id:
                temp = _s
                _s = _d
                _d = temp
        self.src = _s
        self.dst = _d
        self.label = _l
    def __eq__(self, other):
        return self.src == other.src and self.dst == other.dst and self.label == other.label

class Graph(object):
    def __init__(self):
        self.rowNum = '#'
        self.V = [] # Node set
        self.E = [] # Edge set
        self.headNodes = [] #head node index
        self.oracle = [] # oracle transitions for this sent
        self.V.append(Node(0, 'root', 'root', 'root', True))
        self.headNodes.append(0)
        self.table = []

    def buildTable(self): # build adjacent table and check cycle
        for i in range(len(self.V)):
            self.table.append([])
        for edge in self.E:
            i = edge.src.id
            j = edge.dst.id
            self.table[i].append(j)
        for i in range(len(self.table)):
            for j in self.table[i]:
                if i in self.table[j]:
                    print('cycle')
        for edge in self.E:
            i = edge.src.id
            j = edge.dst.id
            self.table[j].append(i)
