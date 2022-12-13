import socket
import threading
import time
from AlternativeServerDB import AlternativeServerDB
from VideoStream import VideoStream
from RtpPacket import RtpPacket


class AlternativeServer:
    serverAddr : str 
    db : AlternativeServerDB


    def __init__(self, serverAddr):
        self.serverAddr = serverAddr
        self.db = AlternativeServerDB()

    def main(self):
        self.connectToServer()
        video = VideoStream("movie.Mjpeg")
        threading.Thread(target=self.join_stream_node).start()
        threading.Thread(target=self.sendRtp, args=(video, )).start()
        threading.Thread(target=self.keepAlive).start()
        threading.Thread(target=self.stopStream).start()


    def connectToServer(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.serverAddr, 7000))
        s.sendall(b"I am alive")
        message, _ = s.recvfrom(1024).decode('utf-8')
        message = message.split('$')
        print("Message: ", message)
        self.db.addIp(message[0])
        self.db.addNeighbour(message[1])
        self.db.addFrameNbr(message[2])
        s.close()
        

    def join_stream_node(self):
        s: socket.socket
        porta: int
        add: tuple

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 5001

        s.bind((self.serverAddr, porta))
        s.listen(5)

        while True:
            client, add = s.accept()
            print(f"Conectado a {add[0]}:{add[1]}")
            message = s.recv(1024).decode('utf-8')
            print("Message: ", message)
            ip = message.split('$')[0]
            rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.db.addRtpSocket(ip, rtpSocket)
            client.close()
            

            
    def keepAlive(self):
        seq = 0
        while True:
            time.sleep(3)
            try:
                #criar tantos sockets quantos os vizinhos
                #enviar para cada vizinho um keepalive com tempo atual e numero de saltos
                t = time.time()
                jumps = 1
                message = f'KEEPALIVE {self.serverAddr} {seq} {t} {jumps} {True}'
                seq += 1
                print("Sending: ", message)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.db.neighbour, 5000))
                s.sendall(message.encode('utf-8'))
                s.close()
            except:
                print("Connection Error no keepalive")
                self.database.disconnectNode(self.db.neighbour)


    def stopStream(self):
        s: socket.socket
        porta: int

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 5003

        s.bind((self.serverAddr, porta))
        s.listen(5)

        while True:
            client, _ = s.accept()
            message = client.recv(1024).decode('utf-8')
            ip = message.split('$')[0]
            if ip == self.db.neighbour:
                self.db.stream = False
            client.close()

    def sendRtp(self, video: VideoStream):
        """Send RTP packets over UDP."""
        video.getFrameByNumber(self.db.frameNbr - 1)
        while True:
            time.sleep(0.05)

            data = video.next_frame()
            if data:
                self.db.frameNbr = video.frameNbr()
                try:
                    if self.db.stream:
                        address = self.db.neighbour
                        port = 5002
                        print(
                            f"Sending frame {self.db.frameNbr} to {address}:{port}")
                        self.db.rtpSocket.sendto(self.makeRtp(data, self.db.frameNbr),
                                           (address, port))
                except:
                    print("Connection Error")

    def makeRtp(self, payload, frameNbr):
        """RTP-packetize the video data."""
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26  # MJPEG type
        seqnum = frameNbr
        ssrc = 0

        rtpPacket = RtpPacket()

        rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt,
                         ssrc, payload)

        return rtpPacket.getPacket()

        