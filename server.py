import fcntl
from random import randint
import socket
import struct
import threading
import time
from signal import signal, SIGPIPE, SIG_DFL
from RtpPacket import RtpPacket
from VideoStream import VideoStream
from Database import Database
import json


class Server:

    def __init__(self, servernum):
        self.serverNum = servernum
        self.database = None

    def main(self):
        #signal(SIGPIPE,SIG_DFL)
        config_file = open("configuration.json", "r")
        config_text = config_file.read()
        data = json.loads(config_text)

        video = VideoStream("movie.Mjpeg")
        self.database = Database(self.serverNum, data['Mask'])

        for i in data['Nodes']:
            self.database.addNode(i['Id'], i['InternalInterfaces'],
                                  i['ExternalInterfaces'], i['Neighbors'])

        self.database.addNeighbors(data[self.serverNum]['Neighbors'])

        threading.Thread(target=self.join_network).start()
        threading.Thread(target=self.join_stream_node).start()
        threading.Thread(target=self.join_stream_client).start()
        threading.Thread(target=self.sendRtp, args=(video, )).start()
        threading.Thread(target=self.keepAlive).start()

    def send_neighbors(self, add: tuple, client: socket):
        self.database.connectNode(add[0])
        message = str(self.database.getNeighbors(add[0])) + "$" + str(
            self.database.getInternalInterfaces(add[0]))
        client.send(message.encode('utf-8'))
        client.close()

    def join_network(self):
        s: socket.socket
        endereco: str
        porta: int
        add: tuple

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        endereco = self.database.ip
        porta = 3000

        s.bind((endereco, porta))
        s.listen(5)

        print(f"Estou à escuta em {endereco}:{porta}")

        while True:
            client, add = s.accept()
            threading.Thread(target=self.send_neighbors,
                             args=(add, client)).start()

    def streaming(self, s: socket, db: Database):
        message = s.recv(1024).decode('utf-8')
        print("Message: ", message)
        ip = message.split('$')[0]
        port = int(message.split('$')[1])
        rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        db.joinStream(ip, rtpSocket)
        #s.send(str(db.nodes[add[0]].port).encode('utf-8'))
        #print("Stream To: ", db.streamTo['10.0.0.10'][0].port)

    def join_stream_node(self):
        s: socket.socket
        porta: int
        add: tuple

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 5001

        s.bind((self.database.ip, porta))
        s.listen(5)

        while True:
            client, add = s.accept()
            print(f"Conectado a {add[0]}:{add[1]}")
            threading.Thread(target=self.streaming, args=(client, )).start()

    def streaming_client(self, add: tuple, client: socket):
        message = client.recv(1024).decode('utf-8')
        client.close()
        port = int(message)
        nodeIp = self.database.getStreamTo(add[0])
        print("Node to stream: ", nodeIp)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((nodeIp, 5001))
        client_info = f"{add[0]}${port}".encode('utf-8')
        s.send(client_info)
        s.close()

    def join_stream_client(self):
        s: socket.socket
        porta: int
        add: tuple

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 5002

        s.bind((self.database.ip, porta))
        s.listen(5)

        while True:
            client, add = s.accept()
            print(f"Conectado a {add[0]}:{add[1]}")
            threading.Thread(target=self.streaming_client,
                             args=(add, client)).start()

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

    #print('-'*60)
    #traceback.print_exc(file=sys.stdout)
    #print('-'*60)

    def keepAlive(self):
        seq = 0
        while True:
            time.sleep(3)
            for ip in self.database.neighbors:
                node = self.database.getNode(ip)
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
                        s.connect((ip, 5000))
                        s.sendall(message.encode('utf-8'))
                        s.close()

                    except:
                        print("Connection Error no keepalive")
                        self.database.disconnectNode(ip)
