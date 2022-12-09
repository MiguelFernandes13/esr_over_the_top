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


def send_neighbors(db: Database, add: tuple, client: socket):
    db.connectNode(add[0])
    message = str(db.getNeighbors(add[0])) + "$" + str(db.getInternalInterfaces(add[0]))
    client.send(message.encode('utf-8'))
    client.close()

def join_network(db: Database):
    s: socket.socket
    endereco: str
    porta: int
    mensagem: bytes
    add: tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    endereco = db.ip
    porta = 3000

    s.bind((endereco, porta))
    s.listen(5)

    print(f"Estou à escuta em {endereco}:{porta}")

    while True:
        client, add = s.accept()
        threading.Thread(target=send_neighbors, args=(db, add, client)).start()

def streaming(add: tuple, s: socket, db: Database):
    message = s.recv(1024).decode('utf-8')
    rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    db.joinStream(add[0], rtpSocket)
    #s.send(str(db.nodes[add[0]].port).encode('utf-8'))
    #print("Stream To: ", db.streamTo['10.0.0.10'][0].port)


def join_stream_node(db: Database):
    s: socket.socket
    porta: int
    add: tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    porta = 5001

    s.bind((db.ip, porta))
    s.listen(5)

    while True:
        client, add = s.accept()
        print(f"Conectado a {add[0]}:{add[1]}")
        threading.Thread(target=streaming, args=(add, client, db)).start()

def streaming_client(db: Database, add: tuple, client: socket):
    message = client.recv(1024).decode('utf-8')
    client.close()
    port = int(message)
    nodeIp = db.getStreamTo(add[0])
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.connect((nodeIp, 5001))
    client_info = f"{add[0]}${port}".encode('utf-8')
    socket.send(client_info)
    socket.close()
    

def join_stream_client(db: Database):
    s: socket.socket
    porta: int
    add: tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    porta = 5002

    s.bind((db.ip, porta))
    s.listen(5)

    while True:
        client, add = s.accept()
        print(f"Conectado a {add[0]}:{add[1]}")
        threading.Thread(target=streaming_client, args=(add, client, db)).start()


def makeRtp(payload, frameNbr):
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

    rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc,
                     payload)

    return rtpPacket.getPacket()


def sendRtp(db: Database, video: VideoStream):
    """Send RTP packets over UDP."""
    while True:
        #self.clientInfo['event'].wait(0.05)
        time.sleep(1)

        data = video.next_frame()
        if data:
            frameNumber = video.frameNbr()
            try:
                for i in db.getStreamTo():
                    address = i.ip
                    port = 5002
                    print(f"Sending frame {frameNumber} to {address}:{port}")
                    i.rtpSocket.sendto(makeRtp(data, frameNumber),
                                       (address, port))
            except:
                print("Connection Error")

#print('-'*60)
#traceback.print_exc(file=sys.stdout)
#print('-'*60)

def keepAlive(db: Database, server_address: str):
    seq = 0
    while True:
        time.sleep(10)
        for ip in db.neighbors:
            node = db.getNode(ip)
            if node.active():
                try:
                    #criar tantos sockets quantos os vizinhos
                    #enviar para cada vizinho um keepalive com tempo atual e numero de saltos
                    t = time.time()
                    jumps = 1
                    message = f'KEEPALIVE {server_address} {seq} {t} {jumps} {True}'
                    seq += 1
                    print("Sending: ", message)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((ip, 5000))
                    s.sendall(message.encode('utf-8'))
                    s.close()

                except:
                    print("Connection Error no keepalive")
                    db.disconnectNode(ip)


def main():
    #signal(SIGPIPE,SIG_DFL)
    config_file = open("configuration.json", "r")
    config_text = config_file.read()
    data = json.loads(config_text)
    server_address = data['Ip']

    video = VideoStream("movie.Mjpeg")
    db = Database(data['Ip'])

    for i in data['Nodes']:
        db.addNode(i['Ip'], i['InternalInterfaces'], i['ExternalInterfaces'] , i['Neighbors'])

    db.addNeighbors(data['Neighbors']) 

    threading.Thread(target=join_network, args=(db, )).start()
    threading.Thread(target=join_stream_node, args=(db, )).start()
    threading.Thread(target=join_stream_client, args=(db, )).start()
    threading.Thread(target=sendRtp, args=(db, video)).start()
    threading.Thread(target=keepAlive, args=(db, server_address)).start()


if __name__ == '__main__':
    main()