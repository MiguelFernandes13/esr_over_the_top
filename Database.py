import threading
import time
import socket

class Node:
    ip: str # binario
    internalInterfaces: list
    externalInterfaces: list
    neighbors: list # Node
    isActive: bool
    isStreaming: bool
    #session : int
    port : int
    rtpSocket : socket

    def __init__(self, ip, internalInterfaces, externalInterfaces, neighbors) -> None:
        self.ip = ip
        self.internalInterfaces = internalInterfaces
        self.externalInterfaces = externalInterfaces
        self.neighbors = neighbors
        self.isActive = False
        self.isStreaming = False
    
    def startStreaming(self, s : socket): 
        self.isStreaming = True
     #   self.session = session
        self.rtpSocket = s

    def stopStreaming(self): self.isStreaming = False
    
    def connect(self): self.isActive = True
    def disconnect(self): self.isActive = False
    
    def active(self): return self.isActive


class Database:
    ip : str
    lock : threading.Lock
    nodes: dict # { 'ip' : Node}
    neighbors : dict # [ips]
    #iptobin: list # [ ('bin', 'ip') ]
    streamTo: list # [Node]
    mask = bin(24)

    def __init__(self, ip):
        self.ip = ip
        self.lock = threading.Lock()
        self.nodes = {}
        self.neighbors = {}
        #self.iptobin = []
        self.streamTo = []


    def addNeighbors(self, neighbors : list):
        try:
            self.lock.acquire()
            for neighbor in neighbors:
                if not neighbor in self.neighbors:
                    node = self.nodes.get(neighbor)
                    self.neighbors[neighbor] = node
        finally:
            self.lock.release()


    def addNode(self, ip, internalInterfaces, externalInterfaces, neighbors):
        try:
            self.lock.acquire()
            self.nodes[ip] = Node(ip, internalInterfaces, externalInterfaces, neighbors)
        finally:
            self.lock.release()


    def connectNode(self, nodeIp):
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.get(nodeIp):
                node.connect()
        finally:
            self.lock.release()
            
    def getNode(self, nodeIp) -> Node:
        try:
            self.lock.acquire()
            return self.nodes[nodeIp]
        finally:
            self.lock.release()
    
    def disconnectNode(self, nodeIp):
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.get(nodeIp):
                node.disconnect()
        finally:
            self.lock.release()

    def joinStream(self, nodeIp, s):
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.get(nodeIp):
                node.startStreaming(s)
                #if not self.streamTo.get(nodeIp):
                #    self.streamTo[nodeIp] = []
                self.streamTo[nodeIp].append(node)
        finally:
            self.lock.release()

    def getStreamToList(self) -> list:
        return self.streamTod
    
    def getNeighbors(self, nodeIp) -> list:
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.get(nodeIp):
                return node.neighbors
        finally:
            self.lock.release()
        
    def getInternalInterfaces(self, nodeIp) -> list:
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.get(nodeIp):
                return node.internalInterfaces
        finally:
            self.lock.release()

    def toBin(self, ip): 
        ipSplited = ip.split('/')
        return ''.join([bin(int(x)+256)[3:] for x in ipSplited[0].split('.')])

    def getStreamTo(self, clientIp) -> str:
        binIp = self.toBin(clientIp)
        print("binIp: ", binIp)
        selected = ('', 0)
        for (nodeIp, node) in self.nodes.items():
            for external in node.externalInterfaces:
                nodeBin = self.toBin(external)
                conta = 0
                for i in range(24):
                    #res = res + str(int(nodeBin[i]) & int(nodeIp[i]))
                    if int(binIp[i]) == int(nodeBin[i]): conta += 1
                    else:
                        if conta > selected[1]: selected = (nodeIp, conta); print("selected: ", selected)
                        break
        return selected[0]

        