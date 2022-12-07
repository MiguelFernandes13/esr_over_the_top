import socket
import threading
from tkinter import *
#from PIL import Image, ImageTk

from RtpPacket import RtpPacket


class NodeClient:

    def __init__(self, serveraddr, serverport, clientaddr):
        self.serverAddr = serveraddr
        self.serverPort = serverport
        self.clientAddr = clientaddr

    def fload_keepAlive(self, client: socket):
        msg, add = client.recvfrom(1024)
        msg_decode = msg.decode('utf-8')
        time_receveid = msg_decode[1]
        jump = msg_decode[2]
        #atualizar o tempo de vida do cliente
        #atualizar o numero de saltos do cliente
        #enviar para os vizinhos um keepalive com o tempo atual e o numero de saltos atualizado
        #enviar tambem se o nodo esta a fazer streaming
        #for i in viznhos:
        #   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #   s.connect((i.ip, 5000))
        #   message = f'KEEPALIVE {time.time() - time_receveid} {jump + 1} {streaming}'
        #   s.sendall(message.encode('utf-8'))
        client.close()

    def keepAlive(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.clientAddr, 5000))
        s.listen(5)
        while True:
            client, add = s.accept()
            threading.Thread(target=self.fload_keepAlive, args=(self,client)).start()

    #def updateMovie(self, imageFile):
    #    """Update the image file as video frame in the GUI."""
    #    photo = ImageTk.PhotoImage(Image.open(imageFile))
    #    label.configure(image = photo, height=288)
    #    label.image = photo
    #
    #def writeFrame(self, data):
    #    """Write the received frame to a temp image file. Return the image file."""
    #    cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
    #    file = open(cachename, "wb")
    #    file.write(data)
    #    file.close()

    #    return cachename

    def getStream(self, stream_socket: socket):
        frameNbr = 0
        while True:
            data = stream_socket.recv(20480)
            if data:
                rtpPacket = RtpPacket()
                rtpPacket.decode(data)

                currFrameNbr = rtpPacket.seqNum()
                print("Current Seq Num: " + str(currFrameNbr))

                if currFrameNbr > frameNbr:  # Discard the late packet
                    frameNbr = currFrameNbr
                    print("Frame number: " + str(frameNbr))
                    #updateMovie(writeFrame(rtpPacket.getPayload()))

    def watchStream(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.serverAddr, 4000))

        #s.sendall("Watch Stream".encode('utf-8'))

        msg, _ = s.recvfrom(1024)
        stream_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(msg.decode('utf-8'))
        stream_socket.bind((self.clientAddr, int(msg.decode('utf-8'))))

        threading.Thread(target=self.getStream, args=(stream_socket, )).start()

    def main(self):
        s: socket.socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect((self.serverAddr, int(self.serverPort)))

        msg, _ = s.recvfrom(1024)

        print(f"Recebi {(msg.decode('utf-8'))}")

        threading.Thread(target=self.keepAlive, args=(self, )).start()
        self.watchStream()