import threading


class NodeDataBase:
    ip : str
    streaming : bool
    neighbors : list
    times : dict # { 'ip' : { serverAddress : time }  }
    jumps : dict # { 'ip' : { serverAddress : jumps }
    streams : dict # { 'ip' : stream(on/off) }
    alreadySent : dict # {serverAddress : {seq : {lista visitados}}
    lock : threading.Lock

    def __init__(self, ip):
        self.ip = ip
        self.streaming = False
        self.neighbors =  []
        self.times = {}
        self.jumps = {}
        self.streams = {}
        self.alreadySent = {}
        self.lock = threading.Lock()

    def addNeighbors(self, list):
        try:
            self.lock.acquire()
            self.neighbors.append(list)
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

    def getNeighbors(self):
        return self.neighbors

    def addSent(self, serverAdd, ip, seq):
        try:
            self.lock.acquire()
            if serverAdd not in self.alreadySent.keys():
                self.alreadySent[serverAdd] = {}
            self.alreadySent[serverAdd][seq] = ip
        finally:
            self.lock.release()

    def getSent(self, serverAdd, seq):
        return self.alreadySent[serverAdd][seq]
