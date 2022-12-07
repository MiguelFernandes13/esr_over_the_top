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


def processamento(db: Database, add: tuple, client: socket):
    db.connectNode(add[0])
    client.send(str(db.getNeighbors(add[0])).encode('utf-8'))
    #while True:
    #    data = client.recv(2048)
    #    message = data.decode('utf-8')
    #    if message == 'BYE':
    #        break
    #    reply = f'Server: {message}'
    #    client.sendall(str.encode(reply))
    client.close()


def streaming(add: tuple, s: socket, db: Database):
    rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # session = randint(4000, 5000)
    db.joinStream(add[0], rtpSocket)
    s.send(str(db.nodes[add[0]].port).encode('utf-8'))
    print("Stream To: ", db.streamTo['10.0.0.10'][0].port)


def join_network(db: Database):
    s: socket.socket
    endereco: str
    porta: int
    mensagem: bytes
    add: tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    endereco = '10.0.0.10'
    porta = 3000

    s.bind((endereco, porta))
    s.listen(5)

    print(f"Estou à escuta em {endereco}:{porta}")

    while True:
        client, add = s.accept()
        threading.Thread(target=processamento, args=(db, add, client)).start()


def join_stream(db: Database):
    s: socket.socket
    endereco: str
    porta: int
    add: tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    endereco = '10.0.0.10'
    porta = 4000

    s.bind((endereco, porta))
    s.listen(5)

    while True:
        client, add = s.accept()
        print(f"Conectado a {add[0]}:{add[1]}")
        threading.Thread(target=streaming, args=(add, client, db)).start()


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
                for i in db.streamTo.get('10.0.0.10'):
                    print(i.port, i.ip)
                    address = i.ip
                    port = int(i.port)
                    print(f"Sending frame {frameNumber} to {address}:{port}")
                    i.rtpSocket.sendto(makeRtp(data, frameNumber),
                                       (address, port))
            except:
                print("Connection Error")

#print('-'*60)
#traceback.print_exc(file=sys.stdout)
#print('-'*60)

def keepAlive(db: Database):
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
                    message = f'KEEPALIVE {t} {jumps} {True}'
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

    video = VideoStream("movie.Mjpeg")
    db = Database()

    for i in data['Nodes']:
        db.addNode(i['Ip'], i['Interfaces'], i['Neighbors'])

    db.addNeighbors(data['Neighbors']) 

    threading.Thread(target=join_network, args=(db, )).start()
    threading.Thread(target=join_stream, args=(db, )).start()
    threading.Thread(target=sendRtp, args=(db, video)).start()
    threading.Thread(target=keepAlive, args=(db, )).start()


if __name__ == '__main__':
    main()