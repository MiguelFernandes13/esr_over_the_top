import threading


class NodeDataBase:
    ip : str
    streaming : bool
    neighbors : list
    times : dict # { 'ip' : time }
    jumps : dict # { 'ip' : jumps }
    streams : dict # { 'ip' : stream(on/off) }
    lock : threading.Lock

    def __init__(self, ip):
        self.ip = ip
        self.streaming = False
        self.neighbors =  []
        self.times = {}
        self.jumps = {}
        self.streams = {}
        self.lock = threading.Lock()

    def addNeighbors(self, list):
        try:
            self.lock.acquire()
            self.neighbors.append(list)
        finally:
            self.lock.release()
        

    def update(self, ip, time, jumps, stream):
        try:
            self.lock.acquire()
            self.times[ip] = time
            self.jumps[ip] = jumps
            self.streams[ip] = stream
        finally:
            self.lock.release()

    def getNeighbors(self):
        return self.neighbors