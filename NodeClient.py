import socket
import sys
import threading
import time
from tkinter import *
import ast
from NodeDatabase import NodeDataBase
#from PIL import Image, ImageTk

from RtpPacket import RtpPacket


class NodeClient:
    serverAddr: str
    db: NodeDataBase

    def __init__(self, serveraddr):
        self.serverAddr = serveraddr
        self.db = NodeDataBase()

    '''
    Método que envia um keep alive para um vizinho
    '''
    def send_keepAlive(self, server_address: str, add: tuple, seq: int,
                       time: float, jump: int):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(add)
            message = f'KEEPALIVE {server_address} {seq} {time} {jump + 1} {self.db.streaming}'
            s.sendall(message.encode('utf-8'))
            self.db.addSent(server_address, add[0], seq)
            s.close()
        except:
            print("Connection Error to ", add[0], ":", add[1])

    '''
    Calcula o melhor vizinho, caso este seja diferente do anterior,
    envia um pedido de stream para o novo melhor vizinho e 
    para o antigo melhor vizinho envia um pedido de parar stream
    '''
    def recalculate_roots(self):
        print("Recalculating roots")
        oldBest = self.db.receiveFrom
        best = self.db.bestNeighbor()
        print(f"Old best: {oldBest} New best: {best} streaming: {self.db.streaming}")
        self.db.updateReceiveFrom(best)
        if best != oldBest and self.db.streaming:
            print("Changing stream")
            self.db.updateWaitBool(True)
            self.db.waitIp = best
            if self.send_request_to_stream(best, 5002):
                self.db.waitStream.acquire()
                try:
                    print("Waiting for stream")
                    while self.db.waitBool: # Espera que a stream do nodo 'waitIp' seja recebida
                        self.db.waitStream.wait()
                    print("Stream received")
                    self.send_stop_stream(oldBest)
                finally:
                    self.db.waitStream.release()


    '''
    Método responsável por fazer a inudação dos keep alives pelos vizinhos
    '''
    def fload_keepAlive(self, client: socket, add: tuple, interface: str):
        #Recebe o keep alive e descodifica a mensagem
        msg, _ = client.recvfrom(1024)
        msg_decode = msg.decode('utf-8').split(' ')
        print(f"Mensagem recebida {msg_decode} de {add[0]}:{add[1]}")
        server_address = msg_decode[1]
        seq = int(msg_decode[2])
        time_receveid = msg_decode[3]
        time_ = time.time() - float(time_receveid)
        jump = int(msg_decode[4])
        stream = bool(msg_decode[5])

        #Adiona o nó à lista de recebidos atualiza as métricas
        self.db.addReceived(server_address, add[0], seq)
        self.db.update(server_address, add[0], time_, jump, stream, interface)
        #Apenas recalcula as rotas quando é a primeira vez ou quando recebe todos os keep alives
        if self.db.alreadyReceived[server_address].get(seq - 1):
            if len(self.db.alreadyReceived[server_address][seq -1]) == len(self.db.alreadyReceived[server_address][seq]):
                threading.Thread(target=self.recalculate_roots).start()
        else:
            threading.Thread(target=self.recalculate_roots).start()
        
        print("Tempos de vida ", self.db.times)
        #print("Saltos ", self.db.jumps)
        for i in self.db.getNeighbors():
            if i not in self.db.getSent(server_address, seq):
                print(f"Enviando para {i}")
                threading.Thread(target=self.send_keepAlive,
                                 args=(server_address, (i, 5000), seq,
                                       time_receveid, jump)).start()
        client.close()

    '''
    Serviço que fica à escuta de keep alives
    '''
    def keepAlive(self, interface: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((interface, 5000))
        s.listen(5)
        while True:
            client, add = s.accept()
            threading.Thread(target=self.fload_keepAlive,
                             args=(client, add, interface)).start()

    '''
    Envia um pedido de stream para um vizinho
    '''
    def send_request_to_stream(self, ip: str, port : int) -> bool:
        if (ip,port) not in self.db.getSendTo():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, 5001))
            message = f'{self.db.getIpToInterface(ip)}$5002'
            print("SEND REQUEST TO STREAM: ", message)
            s.sendall(message.encode('utf-8'))
            s.close()
            return True
        else:
            return False

    '''
    Adiciona um nodo à lista de nodos que querem ver o stream
    '''
    def start_streaming(self, client: socket):
        message, _ = client.recvfrom(1024)
        message = message.decode(
            'utf-8')  # recebe o ip e a porta do cliente que quer ver o stream
        message = message.split('$')
        print("Start Streaming to:", message)
        ip = message[0]
        port = int(message[1])
        self.db.addSendTo(ip, port)

        if not self.db.streaming:
            # estabelecer uma rota desde o servidor ate ao nodo
            best = self.db.receiveFrom
            print(f"O melhor vizinho e {best}")
            self.send_request_to_stream(best, port)

    '''
    Serviço que fica à escuta de pedidos de stream
    '''
    def waitToStream(self, interface: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((interface, 5001))
        s.listen(5)
        while True:
            client, _ = s.accept()
            threading.Thread(target=self.start_streaming,
                             args=(client,)).start()

    '''
    Envia um pedido para parar o stream
    '''
    def send_stop_stream(self, ip: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, 5003))
        message = f'{self.db.getIpToInterface(ip)}$5002'
        s.sendall(message.encode('utf-8'))
        print("SEND STOP STREAM: ", message)
        s.close()

    '''
    Remove um nodo da lista de nodos que querem ver o stream
    '''
    def stop_streaming(self, client: socket):
        message, _ = client.recvfrom(1024)
        message = message.decode('utf-8')
        message = message.split('$')
        ip = message[0]
        port = int(message[1])
        print("Remove stream to: ", ip, ":", port, "")
        self.db.removeSendTo(ip, port)
        if len(self.db.getSendTo()) == 0:
            self.db.streaming = False
            self.send_stop_stream(self.db.receiveFrom)
        client.close()

    '''
    Serviço que fica à escuta de pedidos para parar o stream
    '''
    def waitToStopStream(self, interface: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((interface, 5003))
        s.listen(5)
        while True:
            client, add = s.accept()
            threading.Thread(target=self.stop_streaming,
                             args=(client, )).start()

    '''
    Envia stream para o address
    '''
    def send_stream(self, address: tuple, message: bytes):
        print(f"Enviando stream para {address}")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(message, address)
        s.close()

    '''
    Serviço que fica à escuta de stream e envia para os nodos que querem ver o stream
    '''
    def resend_stream(self, interface: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Wait for stream in ", interface)
        s.bind((interface, 5002))
        try:
            while True:
                message, add = s.recvfrom(20480)
                self.db.streaming = True
                #print(f"Received stream from {add} and waitIp is {self.db.waitIp}")
                if self.db.waitBool and add[0] == self.db.waitIp: # se o nodo que enviou o stream for o que estava à espera
                    self.db.waitStream.acquire()
                    try:
                        self.db.updateWaitBool(False) # atualiza o waitBool para false
                        self.db.waitStream.notify() #notifica a thread que estava à espera
                    finally:
                        self.db.waitStream.release()
                for i in self.db.getSendTo():
                    threading.Thread(target=self.send_stream,
                                     args=(i, message)).start()
        finally:
            s.close()

    def stringToList(self, string) -> list:
        list = ast.literal_eval(string)
        list = [n.strip() for n in list]
        return list

    def main(self):
        s: socket.socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect((self.serverAddr, 3000)) # conecta-se ao servidor

        #Recebe o seu ip, a lista de vizinhos e a lista de interfaces
        msg, _ = s.recvfrom(1024)
        msg_decode = msg.decode('utf-8')
        print(f"Recebi {msg_decode}")
        msg_split = msg_decode.split('$')
        neighbors = msg_split[0]
        self.db.addNeighbors(self.stringToList(neighbors))
        interfaces = msg_split[1]
        self.db.addInterfaces(self.stringToList(interfaces))

        for i in self.db.getInterfaces(): # inicia os serviços em cada interface
            threading.Thread(target=self.keepAlive, args=(i, )).start()
            threading.Thread(target=self.waitToStream, args=(i, )).start()
            threading.Thread(target=self.waitToStopStream, args=(i, )).start()
            threading.Thread(target=self.resend_stream, args=(i, )).start()

