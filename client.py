import socket
import sys
import threading
import time
from tkinter import *
import ast
from NodeDatabase import NodeDataBase
#from PIL import Image, ImageTk

from RtpPacket import RtpPacket

# label = Label(Tk(), height=19)
# label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 

# CACHE_FILE_NAME = "cache-"
# CACHE_FILE_EXT = ".jpg"

def fload_keepAlive(db : NodeDataBase, client : socket):
    msg,add = client.recvfrom(1024)
    msg_decode = msg.decode('utf-8')
    time_receveid = msg_decode[1]
    time_ = time.time() - time_receveid
    jump = msg_decode[2]
    stream = msg_decode[3]
    #atualizar o tempo de vida do cliente
    #atualizar o numero de saltos do cliente
    db.update(add[0], time_, jump, stream)
    #enviar para os vizinhos um keepalive com o tempo atual e o numero de saltos atualizado
    #enviar tambem se o nodo esta a fazer streaming
    for i in db.neighbords:
        if i != add[0]:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((i, 5000))
            message = f'KEEPALIVE {time_} {jump + 1} {db.streaming}'
            s.sendall(message.encode('utf-8'))
    client.close()
    


def keepAlive(db : NodeDataBase, enderecoCliente: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((enderecoCliente, 5000))
    s.listen(5)
    while True:
        client, add = s.accept()
        threading.Thread(target=fload_keepAlive, args=(db, client,)).start()
        

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

def getStream(stream_socket: socket):
    frameNbr = 0
    while True:
            data = stream_socket.recv(20480)
            if data:
                rtpPacket = RtpPacket()
                rtpPacket.decode(data)
				
                currFrameNbr = rtpPacket.seqNum()
                print("Current Seq Num: " + str(currFrameNbr))
									
                if currFrameNbr > frameNbr: # Discard the late packet
                    frameNbr = currFrameNbr
                    print("Frame number: " + str(frameNbr))
                    #updateMovie(writeFrame(rtpPacket.getPayload()))            

def watchStream(enderecoServidor: str, enderecoCliente: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((enderecoServidor, 4000))

    #s.sendall("Watch Stream".encode('utf-8'))

    msg, _ = s.recvfrom(1024)
    stream_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(msg.decode('utf-8'))
    stream_socket.bind((enderecoCliente, int(msg.decode('utf-8'))))

    threading.Thread(target=getStream, args=(stream_socket,)).start()
    
def main():
    s: socket.socket
    enderecoServidor: str
    enderecoCliente: str
    porta: int
    db : NodeDataBase

    db = NodeDataBase()
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    enderecoServidor = '10.0.0.10'
    enderecoCliente = '10.0.1.2'
    porta = 3000

    s.connect((enderecoServidor, porta))

    msg, _ = s.recvfrom(1024)

    print(f"Recebi {(msg.decode('utf-8'))}")
    db.addNeighbors(ast.literal_eval(msg.decode('utf-8')))

    threading.Thread(target=keepAlive, args=(db, enderecoCliente, )).start()
    watchStream(enderecoServidor, enderecoCliente)


if __name__ == '__main__':
    main()
