import threading
import time
import socket


class Node:
    ip_to_server: str
    internalInterfaces: list
    clients: list
    neighbors: list  # Node
    isActive: bool
    isStreaming: bool
    port: int
    rtpSocket: socket

    def __init__(self, internalInterfaces, clients, neighbors) -> None:
        self.ip_to_server = ""
        self.internalInterfaces = internalInterfaces
        self.clients = clients
        self.neighbors = neighbors
        self.isActive = False
        self.isStreaming = False

    def startStreaming(self, s: socket):
        self.isStreaming = True
        self.rtpSocket = s

    def stopStreaming(self):
        self.isStreaming = False

    def connect(self, ip):
        self.isActive = True
        self.ip_to_server = ip

    def disconnect(self):
        self.isActive = False

    def active(self):
        return self.isActive

    def isClient(self, clientIp):
        return clientIp in self.clients


class Database:
    ip: int
    lock: threading.Lock
    nodes: dict  # { 'interface' : Node}
    all_nodes: list
    neighbors: dict  # [ips]
    streamTo: list  # [Node]

    def __init__(self, Ip):
        self.ip = Ip
        self.lock = threading.Lock()
        self.nodes = {}
        self.all_nodes = []
        self.neighbors = {}
        self.streamTo = []
        self.mask = 24
        self.masBin = bin(self.mask)

    def addNeighbors(self, neighbors: list):
        try:
            self.lock.acquire()
            for neighbor in neighbors:
                if not neighbor in self.neighbors:
                    node = self.getNode(neighbor)
                    self.neighbors[neighbor] = node
        finally:
            self.lock.release()

    def addNode(self, internalInterfaces, externalInterfaces, neighbors):
        try:
            self.lock.acquire()
            node = Node(internalInterfaces, externalInterfaces, neighbors)
            self.all_nodes.append(node)

            for interface in internalInterfaces:
                self.nodes[interface] = node
        finally:
            self.lock.release()

    def getNode(self, nodeIp) -> Node:
        res: Node
        res = None
        for node in self.nodes.values():
            interfaces = node.internalInterfaces
            if (nodeIp in interfaces):
                res = node
                break
        return res

    def connectNode(self, nodeIp):
        try:
            self.lock.acquire()
            node: Node
            if node := self.getNode(nodeIp):
                node.connect(nodeIp)
        finally:
            self.lock.release()

    def disconnectNode(self, nodeIp):
        try:
            self.lock.acquire()
            node: Node
            if node := self.getNode(nodeIp):
                node.disconnect()
        finally:
            self.lock.release()

    def joinStream(self, nodeIp, s):
        try:
            self.lock.acquire()
            node: Node
            if node := self.getNode(nodeIp):
                node.startStreaming(s)
                if not node in self.streamTo:
                    self.streamTo.append(node)
        finally:
            self.lock.release()

    def leaveStream(self, nodeIp):
        try:
            self.lock.acquire()
            node: Node
            if node := self.nodes.get(nodeIp):
                node.stopStreaming()
                if node in self.streamTo:
                    self.streamTo.remove(node)
        finally:
            self.lock.release()

    def getStreamToList(self) -> list:
        return self.streamTo

    def getNeighbors(self, nodeIp) -> list:
        try:
            self.lock.acquire()
            node: Node
            if node := self.getNode(nodeIp):
                return node.neighbors
        finally:
            self.lock.release()

    def getInternalInterfaces(self, nodeIp) -> list:
        try:
            self.lock.acquire()
            node: Node
            if node := self.getNode(nodeIp):
                return node.internalInterfaces
        finally:
            self.lock.release()

    def getStreamTo(self, clientIp) -> str:
        node: Node
        for node in self.all_nodes:
            if (node.isClient(clientIp)):
                return node.ip_to_server
