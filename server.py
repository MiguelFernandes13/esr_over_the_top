from random import randint
import socket
import threading
import time
from RtpPacket import RtpPacket
from VideoStream import VideoStream
from Database import Database, Node, HelperServer
import json

# Classe para o servidor (onde são lançados os seus serviços)
class Server:
    serverAddr: str # Endereço IP do servidor
    database: Database # Base de dados do servidor

    def __init__(self):
        self.serverAddr = ""
        self.database = None

    # Função principal do servidor
    # 1. É lido o ficheiro de configuração (configuration.json)
    # 2. É iniciada a classe VideoStream (para a partição do vídeo em frames)
    # 3. É iniciada a base de dados do servidor (com o endereço IP do servidor)
    def main(self):
        config_file = open("configuration.json", "r")
        config_text = config_file.read()
        data = json.loads(config_text)

        video = VideoStream("movie.Mjpeg")
        self.serverAddr = data['Server']['Ip']
        self.database = Database(self.serverAddr)

        # São inseridos na base de dados os servidores auxiliares da topologia (HelperServers no ficheiro de configuração)
        for helper in data['HelperServers']:
            self.database.addHelperServer(helper['Ip'], helper['Neighbors'])

        # São inseridos na base de dados os nós da rede overlay (Nodes no ficheiro de configuração)
        for i in data['Nodes']:
            self.database.addNode(i['InternalInterfaces'], i['Clients'],
                                  i['Neighbors'])
            print(i['Neighbors'])

        # São inseridos na base de dados os vizinhos do servidor (Neighbors no ficheiro de configuração)
        self.database.addNeighbors(data['Server']['Neighbors'])

        # São lançadas todas threads para os serviços do servidor (em portas diferentes)
        threading.Thread(target=self.join_network).start()
        threading.Thread(target=self.join_stream_node).start()
        threading.Thread(target=self.join_stream_client).start()
        threading.Thread(target=self.sendRtp, args=(video, )).start()
        threading.Thread(target=self.keepAlive).start()
        threading.Thread(target=self.stopStream).start()
        threading.Thread(target=self.waitForAlternativeServer).start()
        threading.Thread(target=self.waitToStopStreamClient).start()

    # Construção da rede overlay
    # O serviço vai estar à escuta na porta 3000 
    def join_network(self):
        s: socket.socket
        porta: int
        add: tuple

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 3000

        s.bind((self.serverAddr, porta))
        s.listen(5)

        print(f"Estou à escuta em {self.serverAddr}:{porta}")

        while True:
            client, add = s.accept()
            # Após aceitar a conexão com um nodo é lançada uma thread para entregar os repetivos vizinhos ao nó
            threading.Thread(target=self.send_neighbors,
                             args=(add, client)).start()

    # Função de envio dos vizinhos e interfaces internas do nó da overlay a ele
    def send_neighbors(self, add: tuple, client: socket):
        # Atualiza o estado do nó da overlay na base de dados (para ativo)
        # Agora o nó pode receber stream 
        self.database.connectNode(add[0])

        # A mensagem é composta por dois campos: vizinhos e interfaces internas
        # Para questões de split da string usou-se o símbolo $
        message = str(self.database.getNeighbors(add[0])) + "$" + str(
            self.database.getInternalInterfaces(add[0]))
        print("SEND NEIGHBORS: ", message)

        # Envio da mensagem para o nó da overlay e fecho da conexão
        client.send(message.encode('utf-8'))
        client.close()

    # Adição de um nó da rede overlay à lista de nós a entregar stream
    # O serviço vai estar à escuta na porta 5001
    def join_stream_node(self):
        s: socket.socket
        porta: int
        add: tuple

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 5001

        s.bind((self.serverAddr, porta))
        s.listen(5)

        while True:
            client, add = s.accept()
            print(f"Conectado a {add[0]}:{add[1]}")
            # Após aceitar a conexão com um nodo é lançada uma thread para inserir o nó como elemento a dar stream
            threading.Thread(target=self.streaming, args=(client, )).start()

    # Função de inserção de um nó da rede overlay à lista de nós a entregar stream
    def streaming(self, s: socket):
        message = s.recv(1024).decode('utf-8')
        print("Message: ", message)
        ip = message.split('$')[0]
        rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # É criada uma socket para enviar a stream, juntamente com o ip do nó
        # É adicionada na base de dados do servidr à lista de streamTo
        self.database.joinStream(ip, rtpSocket)

    # Adição de um cliente à lista de clientes a receber stream
    # O serviço vai estar à escuta na porta 5002
    def join_stream_client(self):
        s: socket.socket
        porta: int
        add: tuple

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 5002

        s.bind((self.serverAddr, porta))
        s.listen(5)

        while True:
            client, add = s.accept()
            print(f"Conectado a {add[0]}:{add[1]}")
            threading.Thread(target=self.streaming_client,
                             args=(add, client)).start()

    # Função de inserção de um cliente à lista de clientes a receber stream
    def streaming_client(self, add: tuple, client: socket):
        # Receber a porta RTP do cliente
        message = client.recv(1024).decode('utf-8')

        # Cria um número random para a sessão RTP e enviar para o cliente
        sessionId = randint(100000, 999999)
        client.send(str(sessionId).encode('utf-8'))
        client.close()
        port = int(message)

        # Adicionar o cliente à lista de clientes a receber stream (com o endereço IP e a porta RTP)
        self.database.addClientPort(add[0], port)
        nodeIp = self.database.getStreamTo(add[0])

        # Imprime o nó responsável por entregar a stream ao cliente
        print("Node to stream: ", nodeIp)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Conecta-se com nó responsável por entregar a stream ao cliente e envia a informação do cliente
        # Na porta 5001
        s.connect((nodeIp, 5001))
        client_info = f"{add[0]}${port}".encode('utf-8')
        s.send(client_info)
        s.close()

    # Função de envio de stream RTP
    def sendRtp(self, video: VideoStream):
        """Send RTP packets over UDP."""
        node : Node
        while True:
            time.sleep(0.05)

            data = video.next_frame()
            if data:
                self.database.frameNumber = video.frameNbr()

                # Obtém a frame d vídeo a ser enviada
                try:
                    # Iterar a lista de nós a receber stream (na porta 5002)
                    for node in self.database.getStreamToList():
                        address = node.ip_to_server
                        port = 5002
                        print(
                            f"Sending frame {self.database.frameNumber} to {address}:{port}")
                        # Envia a frame para o nó responsável por entregar a stream ao cliente
                        node.rtpSocket.sendto(self.makeRtp(data, self.database.frameNumber),
                                           (address, port))
                except:
                    print("Connection Error")

    # Função de criação de RTP packet
    # Com o uso da classe RtpPacket fornecida pela equipa docente
    def makeRtp(self, payload, frameNbr):
        """RTP-packetize the video data."""
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26  # MJPEG type
        seqnum = frameNbr
        ssrc = 0

        rtpPacket = RtpPacket()

        rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt,
                         ssrc, payload)

        return rtpPacket.getPacket()

    # Função de remoção de um nó da rede overlay da lista de nós a entregar stream
    # O serviço vai estar à escuta na porta 5003
    def stopStream(self):
        s: socket.socket
        porta: int

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 5003

        s.bind((self.serverAddr, porta))
        s.listen(5)

        while True:
            client, _ = s.accept()
            message = client.recv(1024).decode('utf-8')
            ip = message.split('$')[0]

            # Remover o nó da lista de nós a entregar stream (pr endereço IP enviado pelo cliente)
            self.database.leaveStream(ip)
            client.close()

    # Função de envio da mensagem de keepalive como "inundação" controlada para a topologia overlay
    # Na porta 5000 do nó da overlay
    def keepAlive(self):
        node: Node

        # Número de sequência do keepalive
        seq = 0
        while True:
            time.sleep(3)
            for node in self.database.neighbors.values():
                if node.active():
                    try:
                        #criar tantos sockets quantos os vizinhos
                        #enviar para cada vizinho um keepalive com tempo atual e numero de saltos
                        t = time.time()
                        jumps = 1
                        message = f'KEEPALIVE {self.serverAddr} {seq} {t} {jumps} {True}'
                        seq += 1
                        print("Sending: ", message)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect((node.ip_to_server, 5000))
                        # Envio da mensagem com os parâmetros (endereço IP, número de sequência, tempo, número de saltos, esta ou não streaming) 
                        s.sendall(message.encode('utf-8'))
                        s.close()

                    except:
                        print("Connection Error no keepalive")
                        # Desconectar o nó da rede overlay
                        self.database.disconnectNode(node.ip_to_server)

    # Função para a conexão com o servidor auxiliar
    # Encontra-se à escuta na porta 7000
    def waitForAlternativeServer(self):
        s: socket.socket
        porta: int
        helper: HelperServer

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 7000

        s.bind((self.serverAddr, porta))
        s.listen(5)

        while True:
            client, add = s.accept()
            client.recv(1024)

            # Verifica se o nó que está a tentar conectar-se é um servidor auxiliar
            if helper := self.database.getHelperServer(add[0]):
                server_info = f"{helper.getIp()}${helper.getNeighbors()}${self.database.frameNumber}".encode('utf-8')

                # Envio dos vizinhos do servidor auxiliar e do número da última frame enviada
                client.send(server_info)
            client.close()

    def stopStreamClient(self, add : tuple):
        nodeIp = self.database.getStreamTo(add[0])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((nodeIp, 5003))
        # conecta-se ao nó a enviar a stream ao cliente e fecha a sua ligação
        port = self.database.getClientPort(add[0])
        message = f"{add[0]}${port}".encode('utf-8')
        s.send(message)
        s.close()

    # Função para terminar envio de stream a um cliente
    # Na porta 5003 do nó da overlay
    def waitToStopStreamClient(self):
        s: socket.socket
        porta: int

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        porta = 5004

        s.bind((self.serverAddr, porta))
        s.listen(5)

        while True:
            client, add = s.accept()
            threading.Thread(target=self.stopStreamClient, args=(add, )).start()
            client.close()
            
            
