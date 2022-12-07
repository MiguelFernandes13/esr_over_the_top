import threading
import time
import socket

class Node:
    ip: str # binario
    interfaces: list
    neighbors: list # Node
    isActive: bool
    isStreaming: bool
    #session : int
    port : int
    rtpSocket : socket

    def __init__(self, ip, interfaces, neighbors) -> None:
        self.ip = ip
        self.interfaces = interfaces
        self.neighbors = neighbors
        self.isActive = False
        self.isStreaming = False
    
    def startStreaming(self, port: int, s : socket): 
        self.isStreaming = True
     #   self.session = session
        self.port = port
        self.rtpSocket = s

    def stopStreaming(self): self.isStreaming = False
    
    def connect(self): self.isActive = True
    def disconnect(self): self.isActive = False
    


class Database:
    lock : threading.Lock
    nodes: dict # { 'ip' : Node}
    neighbors : dict # [ips]
    iptobin: list # [ ('bin', 'ip') ]
    streamTo: dict # { 'stream to ip' : [Node] }
    mask = bin(24)
    port : int

    def __init__(self):
        self.lock = threading.Lock()
        self.nodes = {}
        self.neighbors = {}
        self.iptobin = []
        self.streamTo = {}
        self.port = 4001


    def addNeighbors(self, neighbors : list):
        try:
            self.lock.acquire()
            for neighbor in neighbors:
                if not neighbor in self.neighbors:
                    node = self.nodes.get(neighbor)
                    self.neighbors[neighbor] = node
                    self.iptobin.append((self.toBin(neighbor), neighbor))
        finally:
            self.lock.release()


    def addNode(self, ip, interfaces, neighbors):
        try:
            self.lock.acquire()
            self.nodes[ip] = Node(ip, interfaces, neighbors)
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
                node.startStreaming(self.port, s)
                self.port += 1
                if not self.streamTo.get('10.0.0.10'):
                    self.streamTo['10.0.0.10'] = []
                self.streamTo['10.0.0.10'].append(node)
        finally:
            self.lock.release()
    
    def getNeighbors(self, nodeIp):
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.get(nodeIp):
                return node.neighbors
        finally:
            self.lock.release()

    def toBin(self, ip): return ''.join([bin(int(x)+256)[3:] for x in ip.split('.')])

    def getStreamTo(self, clientIp):
        binIp = self.toBin(clientIp)
        selected = ('', 0)
        for nodeBin, nodeIp in self.iptobin:
            conta = 0
            for i in range(len(nodeBin)):
                #res = res + str(int(nodeBin[i]) & int(nodeIp[i]))
                if int(binIp[i]) & int(nodeBin[i]): conta += 1
                else:
                    if conta > selected[1]: selected = (nodeIp, conta)
                    break


    def show(self):
        self.lock.acquire()
        print(f"Tenho {self.quantos} vizinhos")

        for chave,valor in self.vizinhos.items():
            print(f"O vizinho {chave} é o número {valor}")
            time.sleep(2)
        print("")
        self.lock.release()
        time.sleep(3)
        