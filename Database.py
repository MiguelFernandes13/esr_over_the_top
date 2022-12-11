import threading
import time
import socket


class Node:
    id: str  # binario
    internalInterfaces: list
    externalInterfaces: list
    neighbors: list  # Node
    isActive: bool
    isStreaming: bool
    #session : int
    port: int
    rtpSocket: socket

    def __init__(self, id, internalInterfaces, externalInterfaces,
                 neighbors) -> None:
        self.id = id
        self.internalInterfaces = internalInterfaces
        self.externalInterfaces = externalInterfaces
        self.neighbors = neighbors
        self.isActive = False
        self.isStreaming = False

    def startStreaming(self, s: socket):
        self.isStreaming = True
        #   self.session = session
        self.rtpSocket = s

    def stopStreaming(self):
        self.isStreaming = False

    def connect(self):
        self.isActive = True

    def disconnect(self):
        self.isActive = False

    def active(self):
        return self.isActive


class Database:
    ip: int
    lock: threading.Lock
    nodes: dict  # { 'id' : Node}
    neighbors: dict  # [ips]
    #iptobin: list # [ ('bin', 'ip') ]
    streamTo: list  # [Node]
    mask = bin

    def __init__(self, Ip, Mask):
        self.ip = Ip
        self.lock = threading.Lock()
        self.nodes = {}
        self.neighbors = {}
        #self.iptobin = []
        self.streamTo = []
        self.mask = bin(Mask)

    def addNeighbors(self, neighbors: list):
        try:
            self.lock.acquire()
            for neighbor in neighbors:
                if not neighbor in self.neighbors:
                    node = self.getNodeByIp(neighbor)
                    self.neighbors[neighbor] = node
        finally:
            self.lock.release()

    def addNode(self, id, internalInterfaces, externalInterfaces, neighbors):
        try:
            self.lock.acquire()
            self.nodes[id] = Node(id, internalInterfaces, externalInterfaces,
                                  neighbors)
        finally:
            self.lock.release()

    def getNodeByIp(self, nodeIp) -> Node:
        try:
            self.lock.acquire()
            res: Node
            for node in self.nodes.values():
                interfaces = node.internalInterfaces
                if (nodeIp in interfaces):
                    res = node
                    break
            return res
        finally:
            self.lock.release()

    def getNode(self, nodeId) -> Node:
        try:
            self.lock.acquire()
            return self.nodes[nodeId]
        finally:
            self.lock.release()

    def connectNode(self, nodeIp):
        try:
            self.lock.acquire()
            node: Node
            if node := self.getNodeByIp(nodeIp):
                node.connect()
        finally:
            self.lock.release()

    def disconnectNode(self, nodeIp):
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.getNodeByIp(nodeIp):
                node.disconnect()
        finally:
            self.lock.release()

    def joinStream(self, nodeIp, s):
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.getNodeByIp(nodeIp):
                node.startStreaming(s)
                self.streamTo.append(node)
        finally:
            self.lock.release()

    def getStreamToList(self) -> list:
        return self.streamTo

    def getNeighbors(self, nodeIp) -> list:
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.getNodeByIp(nodeIp):
                return node.neighbors
        finally:
            self.lock.release()

    def getInternalInterfaces(self, nodeIp) -> list:
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.getNodeByIp(nodeIp):
                return node.internalInterfaces
        finally:
            self.lock.release()

    def toBin(self, ip):
        ipSplited = ip.split('/')
        return ''.join(
            [bin(int(x) + 256)[3:] for x in ipSplited[0].split('.')])

    def getStreamTo(self, clientIp) -> str:
        binIp = self.toBin(clientIp)
        print("binIp: ", binIp)
        selected = ('', 0)
        for (nodeId, node) in self.nodes.items():
            for external in node.externalInterfaces:
                nodeBin = self.toBin(external)
                conta = 0
                for i in range(24):
                    #res = res + str(int(nodeBin[i]) & int(nodeIp[i]))
                    if int(binIp[i]) == int(nodeBin[i]): conta += 1
                    else:
                        if conta > selected[1]:
                            selected = (nodeId, conta)
                            print("selected: ", selected)
                        break
        return selected[0]
