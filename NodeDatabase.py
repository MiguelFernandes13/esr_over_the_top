import threading


class NodeDataBase:
    interfaces : list
    streaming : bool
    neighbors : list
    times : dict # { 'ip' : { serverAddress : time }  }
    jumps : dict # { 'ip' : { serverAddress : jumps }
    streams : dict # { 'ip' : stream(on/off) }
    alreadySent : dict # {serverAddress : {seq : [lista visitados] }
    lock : threading.Lock

    def __init__(self):
        self.interfaces = []
        self.streaming = False
        self.neighbors =  []
        self.times = {}
        self.jumps = {}
        self.streams = {}
        self.alreadySent = {}
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
