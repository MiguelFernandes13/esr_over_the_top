import sys
import threading


class NodeDataBase:
    interfaces : list
    streaming : bool
    neighbors : list
    times : dict # { 'ip' : { serverAddress : time }  }
    jumps : dict # { 'ip' : { serverAddress : jumps }
    streams : dict # { 'ip' : stream(on/off) }
    alreadySent : dict # {serverAddress : {seq : [lista visitados] }
    sendTo : list # [(ip, port)]
    lock : threading.Lock

    def __init__(self):
        self.interfaces = []
        self.streaming = False
        self.neighbors =  []
        self.times = {}
        self.jumps = {}
        self.streams = {}
        self.alreadySent = {}
        self.sendTo = []
        self.lock = threading.Lock()

    def addNeighbors(self, list : list):
        try:
            self.lock.acquire()
            self.neighbors.extend(list)
        finally:
            self.lock.release()

    def addInterfaces(self, interface : list):
        try:
            self.lock.acquire()
            self.interfaces.extend(interface)
        finally:
            self.lock.release()
        

    def update(self, serverAddress,ip, time, jumps, stream):
        try:
            self.lock.acquire()
            if ip not in self.times.keys():
                self.times[ip] = {}
                self.jumps[ip] = {}

            self.times[ip][serverAddress] = time
            self.jumps[ip][serverAddress] = jumps
            self.streams[ip] = stream
        finally:
            self.lock.release()

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
            self.sendTo.append((ip, port))
        finally:
            self.lock.release()

    def getSendTo(self) -> list:
        return self.sendTo
        
    def bestNeighbor(self) -> str:
        bestNeighbor = None
        neighborStreaming = []
        for neighbor in self.neighbors:
            if self.streams.get(neighbor):
                neighborStreaming.append(neighbor)
        if len(neighborStreaming) != 0:
            time = sys.float_info.max
            for neighbor in neighborStreaming:
                for server in self.times[neighbor].keys():
                    if self.times[neighbor][server] < time:
                        time = self.times[neighbor][server]
                        bestNeighbor = neighbor
        else:
            time = sys.float_info.max
            for neighbor in self.neighbors:
                if self.times.get(neighbor):
                    for server in self.times.get(neighbor).keys():
                        if self.times[neighbor][server] < time:
                            time = self.times[neighbor][server]
                            bestNeighbor = neighbor
        return bestNeighbor
