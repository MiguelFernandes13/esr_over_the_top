import threading
import time

class database:
    quantos : int
    vizinhos : dict
    lock : threading.Lock

    def __init__(self):
        self.quantos = 0
        self.vizinhos = dict()
        self.lock = threading.Lock()

    def acrescenta(self, add):
        self.lock.acquire()
        self.quantos+=1 
        self.vizinhos[add[0]] = self.quantos
        self.lock.release()
    
    def remove(self, add):
        self.lock.acquire()
        self.quantos-=1 
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
        