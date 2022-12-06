import fcntl
import socket
import struct
import threading
import time
from VideoStream import VideoStream
from Database import Database
import json

def processamento(db : Database, add : tuple, s : socket.socket, data : str):
    db.connectNode(add[0])
    s.sendto(db.getNeighbors(add[0]).encode('utf-8'), add[0])

#def processamento2(mensagem : bytes, add : tuple, s : socket.socket, cenas : database):
#    cenas.remove(add)
#    s.sendto("SUCESIUM!".encode('utf-8'), add)

def join_network(db : Database, data : str):
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
        try:
            connect, add = s.accept()
            #mensagem, add = s.recvfrom(1024)
            threading.Thread(target=processamento, args=(db, add, s, data)).start()         
        except Exception:
            break

    s.close()

#def start_streaming():
#    try:
#        video = VideoStream("video.mp4")
#    except:
#        print("Erro ao abrir o ficheiro")
#        #enviar mensagem de erro
#    #percorrer os vizinhos connectado e enviar o video
#    for vizinho in database.vizinhos:
        
#def sendRtp(self):
#    """Send RTP packets over UDP."""
#    while True:
#        self.clientInfo['event'].wait(0.05) 
#			
#        data = self.clientInfo['videoStream'].nextFrame()
#        if data: 
#            frameNumber = self.clientInfo['videoStream'].frameNbr()
#            try:
#                address = self.clientInfo['rtspSocket'][1][0]
#                port = int(self.clientInfo['rtpPort'])
#                self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber),(address,port))
#            except:
#                print("Connection Error")
#				#print('-'*60)
#				#traceback.print_exc(file=sys.stdout)
#				#print('-'*60)

#def servico2(cenas:database):
#    s : socket.socket
#    endereco : str
#    porta : int
#    mensagem : bytes
#    add : tuple
#
#    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#    endereco = '10.0.0.10'
#    porta = 4000
#
#    s.bind((endereco, porta))
#
#    print(f"Estou à escuta em {endereco}:{porta}")
#
#    while True:
#        try:
#            mensagem, add = s.recvfrom(1024)
#            threading.Thread(target=processamento2, args=(mensagem, add, s, cenas)).start()         
#        except Exception:
#            break
#
#    s.close()
#
#def servico3(cenas:database):
#    while True:
#       cenas.show() 

def main():
    config_file = open("configuration.json", "r")
    config_text = config_file.read()
    data = json.loads(config_text)

    db = Database()

    for i in data['Nodes']:
        db.addNode(i['Ip'], i['Interfaces'], i['Neighbors'])

    threading.Thread(target=join_network, args=(db, data)).start()
    #threading.Thread(target=servico2, args=(cenas,)).start()
    #threading.Thread(target=servico3, args=(cenas,)).start()           

if __name__ == '__main__':
    main()