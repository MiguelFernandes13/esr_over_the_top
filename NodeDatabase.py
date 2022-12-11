import sys
import threading
import multiprocessing


class NodeDataBase:
    interfaces: list
    streaming: bool
    neighbors: list
    iPToInterface: dict  # { 'ip' : interfaces }
    times: dict  # { 'ip', : { serverAddress : time }  }
    jumps: dict  # { 'ip' : { serverAddress : jumps }
    streams: dict  # { 'ip' : stream(on/off) }
    alreadySent: dict  # {serverAddress : {seq : [lista visitados] }
    sendTo: list  # [(ip, port)]
    receiveFrom: str
    oldBest: tuple  # (ip, serverAddress, time, jumps)
    lock: threading.Lock
    processReceive: multiprocessing.Process
    waitStreamCondition: threading.Condition
    waitIp = str

    def __init__(self):
        self.interfaces = []
        self.streaming = False
        self.neighbors = []
        self.iPToInterface = {}
        self.times = {}
        self.jumps = {}
        self.streams = {}
        self.alreadySent = {}
        self.sendTo = []
        self.receiveFrom = ""
        self.oldBest = ("", "", 0, 0)
        self.lock = threading.Lock()
        self.processReceive = None
        self.waitStream = threading.Condition()
        self.waitIp = ""

    def addNeighbors(self, list: list):
        try:
            self.lock.acquire()
            self.neighbors.extend(list)
        finally:
            self.lock.release()

    def addInterfaces(self, interface: list):
        try:
            self.lock.acquire()
            self.interfaces.extend(interface)
        finally:
            self.lock.release()

    def update(self, serverAddress, ip, time, jumps, stream, interface):
        try:
            self.lock.acquire()
            if ip not in self.times.keys():
                self.times[ip] = {}
                self.jumps[ip] = {}

            self.iPToInterface[ip] = interface
            self.times[ip][serverAddress] = time
            self.jumps[ip][serverAddress] = jumps
            self.streams[ip] = stream
        finally:
            self.lock.release()

    def updateReceiveFrom(self, ip):
        try:
            self.lock.acquire()
            self.receiveFrom = ip
        finally:
            self.lock.release()

    def getIpToInterface(self, ip) -> str:
        return self.iPToInterface[ip]

    def getNeighbors(self) -> list:
        return self.neighbors

    def getInterfaces(self) -> list:
        return self.interfaces

    def addSent(self, serverAdd, ip, seq):
        try:
            self.lock.acquire()
            if serverAdd not in self.alreadySent.keys():
                self.alreadySent[serverAdd] = {}
            if seq not in self.alreadySent[serverAdd].keys():
                self.alreadySent[serverAdd][seq] = []
            self.alreadySent[serverAdd][seq].append(ip)
        finally:
            self.lock.release()

    def getSent(self, serverAdd, seq) -> list:
        return self.alreadySent[serverAdd][seq]

    def addSendTo(self, ip, port):
        try:
            self.lock.acquire()
            if (ip, port) not in self.sendTo:
                self.sendTo.append((ip, port))
        finally:
            self.lock.release()

    def removeSendTo(self, ip, port):
        try:
            self.lock.acquire()
            if (ip, port) in self.sendTo:
                self.sendTo.remove((ip, port))
        finally:
            self.lock.release()

    def getSendTo(self) -> list:
        return self.sendTo

    def bestNeighbor(self) -> str:
        bestNeighborStreaming: tuple
        jumpThreshold = 0.95
        # Iniciliazar o melhor viznho com os valores dos antigo melhor vizinho
        # Para evitar a troca de viznhos por melhorias insignificantes nas métricas

        if self.oldBest[0] == "":
            bestNeighborStreaming = ("", "", sys.float_info.max,
                                     sys.float_info.max)
        else:
            bestNeighborStreaming = (
                self.oldBest[0], self.oldBest[1],
                self.times[self.oldBest[0]][self.oldBest[1]],
                self.jumps[self.oldBest[0]][self.oldBest[1]]
            )  # (ip, sever, time, jumps)
        bestNeighborTime = bestNeighborStreaming

        neighborStreaming = []
        for neighbor in self.neighbors:
            if self.streams.get(neighbor):
                neighborStreaming.append(neighbor)
        # Percorrer os vizinhos e verificar se algum deles está a fazer stream
        # Se estiver, guardar o vizinho com o melhores métricas, isto é, melhor tempo e menor número de saltos
        if len(neighborStreaming) != 0:
            for neighbor in neighborStreaming:
                for server in self.times[neighbor].keys():
                    if self.times[neighbor][server] < bestNeighborStreaming[2]:
                        #Se a diferença for minima o desempate é feito pelo número de saltos
                        if self.times[neighbor][server] / bestNeighborStreaming[
                                2] > jumpThreshold:
                            if self.jumps[neighbor][
                                    server] < bestNeighborStreaming[3]:
                                bestNeighborStreaming = (
                                    neighbor, server,
                                    self.times[neighbor][server],
                                    self.jumps[neighbor][server])
                        else:
                            bestNeighborStreaming = (
                                neighbor, server, self.times[neighbor][server],
                                self.jumps[neighbor][server])

        #Verificar qual o vizinho com o melhor tempo e menor número de saltos
        for neighbor in self.neighbors:
            if self.times.get(neighbor):
                for server in self.times.get(neighbor).keys():
                    if self.times[neighbor][server] < bestNeighborTime[2]:
                        if self.times[neighbor][server] / bestNeighborTime[
                                2] > jumpThreshold:
                            if self.jumps[neighbor][server] < bestNeighborTime[
                                    3]:
                                bestNeighborTime = (
                                    neighbor, server,
                                    self.times[neighbor][server],
                                    self.jumps[neighbor][server])
                        else:
                            bestNeighborTime = (neighbor, server,
                                                self.times[neighbor][server],
                                                self.jumps[neighbor][server])

        #Caso exista um vizinho que esteja streaming, esse é sempre o melhor vizinho,
        #a menos que exista um vizinho que não esta a fazer stream com um tempo razoavelmente melhor
        self.oldBest = bestNeighborTime
        if bestNeighborStreaming[0] != "" and bestNeighborTime[
                2] / bestNeighborStreaming[2] > 0.8:
            self.oldBest = bestNeighborStreaming

        return self.oldBest[0]
