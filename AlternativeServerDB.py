import socket


class AlternativeServerDB:
    ip : str
    neighbour : str
    frameNbr : int
    rtpSocket : socket
    stream : bool

    def __init__(self):
        self.neighbour = ""
        self.ip = ""
        self.frameNbr = 0
        self.stream = False


    def addIp(self, ip):
        self.ip = ip

    def addNeighbour(self, neighbour):
        self.neighbour = neighbour

    def addFrameNbr(self, frameNbr):
        self.frameNbr = frameNbr

    def addRtpSocket(self, rtpSocket):
        self.rtpSocket = rtpSocket

    def startStream(self):
        self.stream = True

    def stopStream(self):
        self.stream = False