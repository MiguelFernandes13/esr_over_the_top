import socket
import sys
import threading
import multiprocessing
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

    def recalculate_roots(self):
        oldBest = self.db.receiveFrom
        best = self.db.bestNeighbor()
        self.db.updateReceiveFrom(best)
        if best != oldBest and self.db.streaming:
            self.send_request_to_stream(best)
            p = multiprocessing.Process(
                target=self.resend_stream, args=(self.db.getIpToInterface(best), ))
            p.start()
            if self.db.processReceive is not None:
                self.db.waitIp = best
                self.db.waitStream.acquire()
                try:
                    print("Waiting for stream")
                    while not self.db.waitBool:
                        self.db.waitStream.wait()
                    print("Stream received")
                    self.db.waitBool = False
                    self.db.processReceive.terminate()
                    self.send_stop_stream(oldBest)
                finally:
                    self.db.waitStream.release()
            self.db.processReceive = p

    def fload_keepAlive(self, client: socket, add: tuple, interface: str):
        msg, _ = client.recvfrom(1024)
        msg_decode = msg.decode('utf-8').split(' ')
        print(f"Mensagem recebida {msg_decode} de {add[0]}:{add[1]}")
        server_address = msg_decode[1]
        seq = int(msg_decode[2])
        time_receveid = msg_decode[3]
        time_ = time.time() - float(time_receveid)
        jump = int(msg_decode[4])
        stream = bool(msg_decode[5])
        # atualizar o tempo de vida do cliente
        # atualizar o numero de saltos do cliente
        self.db.update(server_address, add[0], time_, jump, stream, interface)
        print("Tempos de vida ", self.db.times)
        print("Saltos ", self.db.jumps)
        self.db.addSent(server_address, add[0], seq)
        threading.Thread(target=self.recalculate_roots).start()
        # enviar para os vizinhos um keepalive com o tempo atual e o numero de saltos atualizado
        # enviar tambem se o nodo esta a fazer streaming
        for i in self.db.getNeighbors():
            if i not in self.db.getSent(server_address, seq):
                print(f"Enviando para {i}")
                threading.Thread(target=self.send_keepAlive,
                                 args=(server_address, (i, 5000), seq,
                                       time_receveid, jump)).start()
        client.close()

    def keepAlive(self, interface: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((interface, 5000))
        s.listen(5)
        while True:
            client, add = s.accept()
            threading.Thread(target=self.fload_keepAlive,
                             args=(client, add, interface)).start()

    def send_request_to_stream(self, ip: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, 5001))
        message = f'{self.db.getIpToInterface(ip)}$5002'
        print("SEND REQUEST TO STREAM: ", message)
        s.sendall(message.encode('utf-8'))
        s.close()

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
            self.send_request_to_stream(best)
            p = multiprocessing.Process(
                target=self.resend_stream, args=(self.db.getIpToInterface(best), ))
            p.start()
            self.db.processReceive = p

    def waitToStream(self, interface: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((interface, 5001))
        s.listen(5)
        while True:
            client, _ = s.accept()
            threading.Thread(target=self.start_streaming,
                             args=(client,)).start()

    def send_stop_stream(self, ip: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, 5003))
        message = f'{self.db.getIpToInterface(ip)}$5002'
        s.sendall(message.encode('utf-8'))
        print("SEND STOP STREAM: ", message)
        s.close()

    def stop_streaming(self, client: socket):
        message, _ = client.recvfrom(1024)
        message = message.decode('utf-8')
        message = message.split('$')
        ip = message[0]
        port = int(message[1])
        self.db.removeSendTo(ip, port)
        print("Remove:", message)
        if len(self.db.getSendTo()) == 0:
            self.db.streaming = False
            self.send_stop_stream(self.db.receiveFrom)
        client.close()

    def waitToStopStream(self, interface: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((interface, 5003))
        s.listen(5)
        while True:
            client, add = s.accept()
            threading.Thread(target=self.stop_streaming,
                             args=(client, )).start()

    def send_stream(self, address: tuple, message: bytes):
        print(f"Enviando stream para {address}")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(message, address)
        s.close()

    def resend_stream(self, interface: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Wait for stream in ", interface)
        s.bind((interface, 5002))
        try:
            while True:
                message, add = s.recvfrom(20480)
                self.db.streaming = True
                #print(f"Received stream from {add} and waitIp is {self.db.waitIp}")
                if add[0] == self.db.waitIp:
                    self.db.waitStream.acquire()
                    try:
                        self.db.waitStream.notify_all()
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

        s.connect((self.serverAddr, 3000))

        msg, _ = s.recvfrom(1024)
        msg_decode = msg.decode('utf-8')
        print(f"Recebi {msg_decode}")
        msg_split = msg_decode.split('$')
        neighbors = msg_split[0]
        self.db.addNeighbors(self.stringToList(neighbors))
        interfaces = msg_split[1]
        self.db.addInterfaces(self.stringToList(interfaces))

        for i in self.db.getInterfaces():
            threading.Thread(target=self.keepAlive, args=(i, )).start()
            threading.Thread(target=self.waitToStream, args=(i, )).start()
            threading.Thread(target=self.waitToStopStream, args=(i, )).start()
            #threading.Thread(target=self.resend_stream, args=(i, )).start()

        # self.watchStream()
