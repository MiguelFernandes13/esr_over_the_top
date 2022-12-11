from random import randint
import socket
import threading
import time
from RtpPacket import RtpPacket
from VideoStream import VideoStream
from Database import Database, Node
import json


class Server:
    serverAddr: str
    database: Database

    def __init__(self):
        self.serverAddr = ""
        self.database = None

    def main(self):
        config_file = open("configuration.json", "r")
        config_text = config_file.read()
        data = json.loads(config_text)

        video = VideoStream("movie.Mjpeg")
        self.serverAddr = data['Server']['Ip']
        self.database = Database(self.serverAddr)

        for i in data['Nodes']:
            self.database.addNode(i['InternalInterfaces'], i['Clients'],
                                  i['Neighbors'])
            print(i['Neighbors'])

        self.database.addNeighbors(data['Server']['Neighbors'])

        threading.Thread(target=self.join_network).start()
        threading.Thread(target=self.join_stream_node).start()
        threading.Thread(target=self.join_stream_client).start()
        threading.Thread(target=self.sendRtp, args=(video, )).start()
        threading.Thread(target=self.keepAlive).start()
        threading.Thread(target=self.stopStream).start()

    def join_network(self):
        s: socket.socket
        porta: int
        add: tuple

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 3000

        s.bind((self.serverAddr, porta))
        s.listen(5)

        print(f"Estou à escuta em {self.serverAddr}:{porta}")

        while True:
            client, add = s.accept()
            threading.Thread(target=self.send_neighbors,
                             args=(add, client)).start()

    def send_neighbors(self, add: tuple, client: socket):
        self.database.connectNode(add[0])
        print(add[0])
        message = str(self.database.getNeighbors(add[0])) + "$" + str(
            self.database.getInternalInterfaces(add[0]))
        print(message)
        client.send(message.encode('utf-8'))
        client.close()

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
            threading.Thread(target=self.streaming, args=(client, )).start()

    def streaming(self, s: socket):
        message = s.recv(1024).decode('utf-8')
        print("Message: ", message)
        ip = message.split('$')[0]
        rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.database.joinStream(ip, rtpSocket)

    def join_stream_client(self):
        s: socket.socket
        porta: int
        add: tuple

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 5002

        s.bind((self.serverAddr, porta))
        s.listen(5)

        while True:
            client, add = s.accept()
            print(f"Conectado a {add[0]}:{add[1]}")
            threading.Thread(target=self.streaming_client,
                             args=(add, client)).start()

    def streaming_client(self, add: tuple, client: socket):
        message = client.recv(1024).decode('utf-8')
        sessionId = randint(100000, 999999)
        client.send(str(sessionId).encode('utf-8'))
        client.close()
        port = int(message)
        nodeIp = self.database.getStreamTo(add[0])
        print("Node to stream: ", nodeIp)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((nodeIp, 5001))
        client_info = f"{add[0]}${port}".encode('utf-8')
        s.send(client_info)
        s.close()

    def sendRtp(self, video: VideoStream):
        """Send RTP packets over UDP."""
        while True:
            time.sleep(0.05)

            data = video.next_frame()
            if data:
                frameNumber = video.frameNbr()
                try:
                    print("List of streams: ", self.database.getStreamToList())
                    for i in self.database.getStreamToList():
                        address = i.ip
                        port = 5002
                        print(
                            f"Sending frame {frameNumber} to {address}:{port}")
                        i.rtpSocket.sendto(self.makeRtp(data, frameNumber),
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
            self.database.leaveStream(ip)
            client.close()

    def keepAlive(self):
        node: Node
        seq = 0
        while True:
            time.sleep(3)
            for node in self.database.neighbors.values():
                if node.active():
                    try:
                        #criar tantos sockets quantos os vizinhos
                        #enviar para cada vizinho um keepalive com tempo atual e numero de saltos
                        t = time.time()
                        jumps = 1
                        message = f'KEEPALIVE {self.serverAddr} {seq} {t} {jumps} {True}'
                        seq += 1
                        print("Sending: ", message)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((node.ip_to_server, 5000))
                        s.sendall(message.encode('utf-8'))
                        s.close()

                    except:
                        print("Connection Error no keepalive")
                        self.database.disconnectNode(node.ip_to_server)
