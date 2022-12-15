import threading
import time
import socket

#Classe que guarda a informação de servidor alternativo
class HelperServer:
    ip: str # ip do servidor
    neighbors: list # lista de ips dos vizinhos

    def __init__(self, ip, neighbors):
        self.ip = ip
        self.neighbors = neighbors

    #Retorna o ip do servidor
    def getIp(self):
        return self.ip

    #Retorna a lista de vizinhos
    def getNeighbors(self):
        return self.neighbors

#Classe que guarda a informação de um nó
class Node:
    ip_to_server: str # interface que comunica com o servidor
    internalInterfaces: list # lista de interfaces internas
    clients: list #lista de ips dos clientes
    neighbors: list  # lista de ips dos vizinhos
    isActive: bool # se está ativo
    isStreaming: bool # se está a fazer stream
    port: int 
    rtpSocket: socket # socket RTP para fazer stream

    def __init__(self, internalInterfaces, clients, neighbors) -> None:
        self.ip_to_server = ""
        self.internalInterfaces = internalInterfaces
        self.clients = clients
        self.neighbors = neighbors
        self.isActive = False
        self.isStreaming = False

    #Começa a stream num nó e guarda o socket RTP
    def startStreaming(self, s: socket):
        self.isStreaming = True
        self.rtpSocket = s

    #Para a stream num nó
    def stopStreaming(self):
        self.isStreaming = False

    #Ativa o nó
    def connect(self, ip):
        self.isActive = True
        self.ip_to_server = ip

    #Desativa o nó
    def disconnect(self):
        self.isActive = False

    #retorna se está ativo
    def active(self):
        return self.isActive

    #retorna se o clientIp é um cliente do nó
    def isClient(self, clientIp):
        return clientIp in self.clients


class Database:
    ip: int # ip do servidor
    lock: threading.Lock # lock para garantir que as variáveis são acessadas de forma segura
    nodes: dict  # { 'interface' : Node} 
    all_nodes: list # lista de todos os nós
    neighbors: dict  # { 'interface' : nó }
    streamTo: list  # [Node] lista de nós para onde se está a fazer stream
    helperServers: list  # [HelperServer] lista de servidores alternativos
    frameNumber: int # número do frame
    clientPort : dict # {ip : port} dicionário que guarda a porta de cada cliente

    def __init__(self, Ip):
        self.ip = Ip
        self.lock = threading.Lock()
        self.nodes = {}
        self.all_nodes = []
        self.neighbors = {}
        self.streamTo = []
        self.mask = 24
        self.helperServers = []
        self.frameNumber = 0
        self.clientPort = {}

    #Retorna a porta de um cliente
    def getClientPort(self, ip):
        return self.clientPort[ip]

    #Adiciona a porta a um cliente
    def addClientPort(self, ip, port):
        try:
            self.lock.acquire()
            self.clientPort[ip] = port
        finally:
            self.lock.release()

    #Adiciona um servidor alternativo
    def addHelperServer(self, ip, neighbors):
        try:
            self.lock.acquire()
            self.helperServers.append(HelperServer(ip, neighbors))
        finally:
            self.lock.release()

    #Retorna o servidor alternativo com base np ip dado
    def getHelperServer(self, ip):
        for helper in self.helperServers:
            if helper.getIp() == ip:
                return helper
        return None

    #Adiciona vizinhos ao servidor
    def addNeighbors(self, neighbors: list):
        try:
            self.lock.acquire()
            for neighbor in neighbors:
                if not neighbor in self.neighbors:
                    node = self.getNode(neighbor)
                    self.neighbors[neighbor] = node
        finally:
            self.lock.release()

    #Adiciona um nodo ao servidor
    def addNode(self, internalInterfaces, clients, neighbors):
        try:
            self.lock.acquire()
            node = Node(internalInterfaces, clients, neighbors)
            self.all_nodes.append(node)

            for interface in internalInterfaces:
                self.nodes[interface] = node
        finally:
            self.lock.release()

    #Retorna um nó com base no ip dado
    def getNode(self, nodeIp) -> Node:
        return self.nodes.get(nodeIp)

    #Ativa um nó
    def connectNode(self, nodeIp):
        try:
            self.lock.acquire()
            node: Node
            if node := self.getNode(nodeIp):
                node.connect(nodeIp)
        finally:
            self.lock.release()

    #Desativa um nó
    def disconnectNode(self, nodeIp):
        try:
            self.lock.acquire()
            node: Node
            if node := self.getNode(nodeIp):
                node.disconnect()
        finally:
            self.lock.release()

    #Adiciona um nó à lista de nós para onde se está a fazer stream
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

    #Remove um nó da lista de nós para onde se está a fazer stream
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

    #Retorna a lista de nós para onde se está a fazer stream
    def getStreamToList(self) -> list:
        return self.streamTo

    #Retorna os vizinhos de um nó
    def getNeighbors(self, nodeIp) -> list:
        try:
            self.lock.acquire()
            node: Node
            if node := self.getNode(nodeIp):
                return node.neighbors
        finally:
            self.lock.release()

    #Retorna as interfaces internas de um nó
    def getInternalInterfaces(self, nodeIp) -> list:
        try:
            self.lock.acquire()
            node: Node
            if node := self.getNode(nodeIp):
                return node.internalInterfaces
        finally:
            self.lock.release()

    #Retorna o nó conectado a um dado cliente
    def getStreamTo(self, clientIp) -> str:
        node: Node
        for node in self.all_nodes:
            if (node.isClient(clientIp)):
                return node.ip_to_server
