import sys
import threading
import multiprocessing


class NodeDataBase:
    interfaces: list # [interfaces]
    streaming: bool # flag para saber se está a streamar
    neighbors: list # [ip]
    iPToInterface: dict  # { 'ip' : interfaces }
    times: dict  # { 'serverAddress', : { ip  :  time }  }
    jumps: dict  # { 'serverAddress' : { ip : jumps }
    streams: dict  # { 'ip' : stream(on/off) }
    alreadySent: dict  # {serverAddress : {seq : [lista visitados] }
    alreadyReceived: dict  # {serverAddress : {seq : [lista recebidos] }
    sendTo: list  # [(ip, port)]
    receiveFrom: str
    oldBest: tuple  # (ip, serverAddress, time, jumps)
    lock: threading.Lock # lock para aceder a variaveis partilhadas
    waitStreamCondition: threading.Condition # condição para esperar por um stream
    waitIp : str #ip do nodo que se espera receber a stream
    waitBool : bool #flag para saber se se está à espera de uma stream

    def __init__(self):
        self.interfaces = []
        self.streaming = False
        self.neighbors = []
        self.iPToInterface = {}
        self.times = {}
        self.jumps = {}
        self.streams = {}
        self.alreadySent = {}
        self.alreadyReceived = {}
        self.sendTo = []
        self.receiveFrom = ""
        self.oldBest = ("", "", 0, 0)
        self.lock = threading.Lock()
        self.waitStream = threading.Condition()
        self.waitIp = ""
        self.waitBool = False

    #Adiciona uma lista de vizinhos
    def addNeighbors(self, list: list):
        try:
            self.lock.acquire()
            self.neighbors.extend(list)
        finally:
            self.lock.release()

    #Adiciona uma lista de interfaces
    def addInterfaces(self, interface: list):
        try:
            self.lock.acquire()
            self.interfaces.extend(interface)
        finally:
            self.lock.release()

    #Atualiza as métricas com os valores recebidos
    def update(self, serverAddress, ip, time, jumps, stream, interface):
        try:
            self.lock.acquire()
            if serverAddress not in self.times.keys(): # cria um dicionario caso não exista
                self.times[serverAddress] = {}
                self.jumps[serverAddress] = {}

            self.iPToInterface[ip] = interface
            self.times[serverAddress][ip] = time
            self.jumps[serverAddress][ip] = jumps
            self.streams[ip] = stream
        finally:
            self.lock.release()

    #Atualiza o nodo de onde está a receber a stream
    def updateReceiveFrom(self, ip):
        try:
            self.lock.acquire()
            self.receiveFrom = ip
        finally:
            self.lock.release()

    #Retorna a interface que comunica com um dado ip
    def getIpToInterface(self, ip) -> str:
        return self.iPToInterface[ip]

    #Retorna a lista de vizinhos
    def getNeighbors(self) -> list:
        return self.neighbors

    #Retorna a lista de interfaces
    def getInterfaces(self) -> list:
        return self.interfaces

    #Adiciona o vizinho à lista de recebidos
    def addReceived(self, serverAdd, ip, seq):
        try:
            self.lock.acquire()
            if serverAdd not in self.alreadyReceived.keys():
                self.alreadyReceived[serverAdd] = {}
            if seq not in self.alreadyReceived[serverAdd].keys(): 
                self.alreadyReceived[serverAdd][seq] = []
                self.times[serverAdd] = {}
                self.jumps[serverAdd] = {}
            self.alreadyReceived[serverAdd][seq].append(ip)
        finally:
            self.lock.release()
        self.addSent(serverAdd, ip, seq)

    #Adiciona o vizinho à lista de enviados
    def addSent(self, serverAdd, ip, seq):
        try:
            self.lock.acquire()
            if serverAdd not in self.alreadySent.keys():
                self.alreadySent[serverAdd] = {}
            if seq not in self.alreadySent[serverAdd].keys():
                self.alreadySent[serverAdd][seq] = []
            self.alreadySent[serverAdd][seq].append(ip)
        finally:
            self.lock.release()

    #Retorna a lista de vizinhos que já foram enviados
    def getSent(self, serverAdd, seq) -> list:
        return self.alreadySent[serverAdd][seq]

    #Adiciona um nodo à lista de vizinhos a receber a stream
    def addSendTo(self, ip, port):
        try:
            self.lock.acquire()
            if (ip, port) not in self.sendTo:
                self.sendTo.append((ip, port))
        finally:
            self.lock.release()

    #Remove um nodo da lista de vizinhos a receber a stream
    def removeSendTo(self, ip, port):
        try:
            self.lock.acquire()
            if (ip, port) in self.sendTo:
                print("removing", ip, port)
                self.sendTo.remove((ip, port))
        finally:
            self.lock.release()

    #Retorna a lista de vizinhos a receber a stream
    def getSendTo(self) -> list:
        return self.sendTo

    #Atualiza a flag que indica se está à espera de uma stream
    def updateWaitBool(self, bool):
        try:
            self.lock.acquire()
            self.waitBool = bool
        finally:
            self.lock.release()

    #Cálculo do melhor vizinho
    def bestNeighbor(self) -> str:
        bestNeighborStreaming: tuple
        jumpThreshold = 0.95
        # Iniciliazar o melhor viznho com os valores dos antigo melhor vizinho
        # Para evitar a troca de viznhos por melhorias insignificantes nas métricas

        if self.oldBest[0] == "" or self.times.get(self.oldBest[1]):
            bestNeighborStreaming = ("", "", sys.float_info.max,
                                     sys.float_info.max)
        else:
            bestNeighborStreaming = (
                self.oldBest[0], self.oldBest[1],
                self.times[self.oldBest[1]][self.oldBest[0]],
                self.jumps[self.oldBest[1]][self.oldBest[0]]
            )  # (ip, server, time, jumps)
        bestNeighborTime = bestNeighborStreaming
        neighborStreaming = []
        for neighbor in self.neighbors:
            if self.streams.get(neighbor):
                neighborStreaming.append(neighbor)
        # Percorrer os vizinhos e verificar se algum deles está a fazer stream
        # Se estiver, guardar o vizinho com o melhores métricas, isto é, melhor tempo e menor número de saltos
        if len(neighborStreaming) != 0:
            for server in self.times.keys():
                for neighbor in neighborStreaming:
                    if self.times[server].get(neighbor) is not None:
                        if self.times[server][neighbor] < bestNeighborStreaming[2]:
                            #Se a diferença for minima o desempate é feito pelo número de saltos
                            if self.times[server][neighbor] / bestNeighborStreaming[
                                    2] > jumpThreshold:
                                if self.jumps[server][
                                        neighbor] < bestNeighborStreaming[3]:
                                    bestNeighborStreaming = (
                                        neighbor, server,
                                        self.times[server][neighbor],
                                        self.jumps[server][neighbor])
                            else:
                                bestNeighborStreaming = (
                                    neighbor, server, self.times[server][neighbor],
                                    self.jumps[server][neighbor])

        #Verificar qual o vizinho que esteja ou não a fazer stream com o melhor tempo e menor número de saltos
        for server in self.times.keys():
            for neighbor in self.neighbors:
                if self.times[server].get(neighbor) is not None:
                    if self.times[server][neighbor] < bestNeighborTime[2]:
                        if self.times[server][neighbor] / bestNeighborTime[
                                2] > jumpThreshold:
                            if self.jumps[server][neighbor] < bestNeighborTime[3]:
                                bestNeighborTime = (
                                    neighbor, server, self.times[server][neighbor],
                                    self.jumps[server][neighbor])
                        else:
                            bestNeighborTime = (neighbor, server,
                                                self.times[server][neighbor],
                                                self.jumps[server][neighbor])

        #Caso exista um vizinho que esteja streaming, esse é sempre o melhor vizinho,
        #a menos que exista um vizinho que não esta a fazer stream com um tempo razoavelmente melhor
        self.oldBest = bestNeighborTime
        if bestNeighborStreaming[0] != "" and bestNeighborTime[ 
                2] / bestNeighborStreaming[2] > 0.7:
            self.oldBest = bestNeighborStreaming

        return self.oldBest[0]
