import socket
import sys
import threading
from tkinter import *
#from PIL import Image, ImageTk

from RtpPacket import RtpPacket

# label = Label(Tk(), height=19)
# label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 

# CACHE_FILE_NAME = "cache-"
# CACHE_FILE_EXT = ".jpg"

def keepAlive(s: socket):
    while True:
        msg,_ = s.recvfrom(1024)
        print(f"Recebi {(msg.decode('utf-8'))}")

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
                    print("Frame number: " + frameNbr)
                    #updateMovie(writeFrame(rtpPacket.getPayload()))            

def watchStream(endereco: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((endereco, 4000))

    s.sendall("Watch Stream".encode('utf-8'))

    msg, _ = s.recvfrom(1024)
    stream_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    stream_socket.bind((endereco, int(msg.decode('utf-8'))))
    threading.Thread(target=getStream, args=(stream_socket,)).start()
    
def main():
    s: socket.socket
    endereco: str
    porta: int

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    endereco = '10.0.0.10'
    porta = 3000

    s.connect((endereco, porta))

    msg, _ = s.recvfrom(1024)

    print(f"Recebi {(msg.decode('utf-8'))}")

    threading.Thread(target=keepAlive, args=(s,)).start()
    watchStream(endereco)


if __name__ == '__main__':
    main()
