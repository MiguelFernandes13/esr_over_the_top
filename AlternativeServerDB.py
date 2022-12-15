import socket


class AlternativeServerDB:
    ip : str # ip do servidor alternativo
    neighbour : str # ip do vizinho
    frameNbr : int # número do frame
    rtpSocket : socket # socket RTP para fazer stream para o vizinho
    stream : bool # se o vizinho quer receber a stream

    def __init__(self):
        self.neighbour = ""
        self.ip = ""
        self.frameNbr = 0
        self.stream = False

    #Atualiza o ip do servidor alternativo
    def addIp(self, ip):
        self.ip = ip

    #Atualiza o ip do vizinho
    def addNeighbour(self, neighbour):
        self.neighbour = neighbour

    #Atualiza o número do frame
    def addFrameNbr(self, frameNbr):
        self.frameNbr = frameNbr

    #Atualiza o socket RTP
    def addRtpSocket(self, rtpSocket):
        self.rtpSocket = rtpSocket

    #Começa a stream para o vizinho
    def startStream(self):
        self.stream = True

    #Para a stream para o vizinho
    def stopStream(self):
        self.stream = False