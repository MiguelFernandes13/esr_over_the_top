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

def processamento(db : Database, add : tuple, client : socket):
    db.connectNode(add[0])
    client.send(str(db.getNeighbors(add[0])).encode('utf-8'))
    while True:
        data = client.recv(2048)
        message = data.decode('utf-8')
        if message == 'BYE':
            break
        reply = f'Server: {message}'
        client.sendall(str.encode(reply))
    client.close()

def streaming(add : tuple,s: socket, db : Database):
    rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    session = randint(100000, 999999)
    s.sendto(str(session).encode('utf-8'), add)
    db.joinStream(add[0], session, rtpSocket)

def join_network(db : Database):
    s : socket.socket
    endereco : str
    porta : int
    mensagem : bytes
    add : tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    

    endereco = '10.0.0.10'
    porta = 3000

    
    s.bind((endereco, porta))
    s.listen(5)

    print(f"Estou à escuta em {endereco}:{porta}")

    while True:
        client, add = s.accept()
        threading.Thread(target=processamento, args=(db, add, client)).start()         

def join_stream(db : Database):
    s : socket.socket
    endereco : str
    porta : int
    add : tuple

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    endereco = '10.0.0.10'
    porta = 4000

    s.bind((endereco, porta))
    s.listen(5)

    while True:
        _, add = s.recvfrom(1024)
        threading.Thread(target=streaming, args=(add, s, db)).start()


def makeRtp(payload, frameNbr):
    """RTP-packetize the video data."""
    version = 2
    padding = 0
    extension = 0
    cc = 0
    marker = 0
    pt = 26 # MJPEG type
    seqnum = frameNbr
    ssrc = 0 
	
    rtpPacket = RtpPacket()
	
    rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
	
    return rtpPacket.getPacket()
        
def sendRtp(db : Database, video : VideoStream):
    """Send RTP packets over UDP."""
    while True:
        #self.clientInfo['event'].wait(0.05) 
        time.sleep(1)
			
        data = video.next_frame()
        if data: 
            frameNumber = video.frameNbr()
            try:
                if(db.streamTo.get("10.0.0.10")):
                    for i in db.streamTo.get("10.0.0.10"):
                        address = i.ip
                        port = int(i.rtpPort)
                        i.rtpSocket.sendto(makeRtp(data, frameNumber),(address,port))
            except:
                print("Connection Error")
				#print('-'*60)
				#traceback.print_exc(file=sys.stdout)
				#print('-'*60)


def main():
    signal(SIGPIPE,SIG_DFL) 
    config_file = open("configuration.json", "r")
    config_text = config_file.read()
    data = json.loads(config_text)

    video = VideoStream("movie.Mjpeg")
    db = Database()

    for i in data['Nodes']:
        db.addNode(i['Ip'], i['Interfaces'], i['Neighbors'])
    
    threading.Thread(target=join_network, args=(db, )).start()
    threading.Thread(target=join_stream, args=(db,)).start()
    threading.Thread(target=sendRtp, args=(db, video)).start()           

if __name__ == '__main__':
    main()