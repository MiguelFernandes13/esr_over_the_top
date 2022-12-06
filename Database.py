import threading
import time
import socket


class Database:
    quantos : int
    sockets : dict
    interfaces : dict
    vizinhos : dict 
    lock : threading.Lock

    def __init__(self):
        self.vizinhos = dict()
        self.lock = threading.Lock()

    def acrescenta(self, add, v, s, i):
        self.lock.acquire()
        self.sockets[add] = s
        self.interfaces[add] = i
        self.vizinhos[add].append(v)
        self.lock.release()
    
    def remove(self, add):
        self.lock.acquire()
        self.vizinhos.pop(add[0])
        self.lock.release()
    
    def show(self):
        self.lock.acquire()
        print(f"Tenho {self.quantos} vizinhos")

        for chave,valor in self.vizinhos.items():
            print(f"O vizinho {chave} é o número {valor}")
            time.sleep(2)
        print("")
        self.lock.release()
        time.sleep(3)
        