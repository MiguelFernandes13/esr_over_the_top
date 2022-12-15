from tkinter import *
from tkinter import messagebox
import socket, threading, os
from PIL import Image, ImageTk

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

# Classe para o streaming do cliente (apresentação gráfica do video)
class ClientGUI:

    def __init__(self, master, clientaddr, clientport, serveraddr):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.clientAddr = clientaddr
        self.serverAddr = serveraddr
        self.serverPort = 5002
        self.clientPort = clientport
        self.rtspSeq = 0
        self.sessionId = 0
        self.rtpSocket = None
        # Ao inicializar é feito o setup do video automaticamente
        self.setupMovie()
        # É criada uma janela para apresentar graficamente o video
        self.createWidgets()
        # O video é iniciado automaticamente
        self.playMovie()
        self.frameNbr = 0

    # Método para criar, graficamente, a janela do video
    def createWidgets(self):
        """Build GUI."""
        # Create Play button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0,
                        column=0,
                        columnspan=4,
                        sticky=W + E + N + S,
                        padx=5,
                        pady=5)

    # Realizar setup do video
    # 1. É iniciada uma conexão TCP com o servidor (Porta 5002)
    # 2. É enviado o numero da porta RTP para o servidor (pela qual o cliente quer receber a stream)
    # 3. O servidor envia o numero de sessão do servidor (para diferenciar os nomes dos ficheiros de cache dos clientes)
    # 4. É iniciada uma conexão UDP com o servidor (Porta RTP) -> openRtpPort()
    def setupMovie(self):
        s: socket.socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect((self.serverAddr, 5002))

        s.send(str(self.clientPort).encode('utf-8'))

        self.sessionId = int(s.recv(1024).decode('utf-8'))

        s.close()
        self.openRtpPort()
        print("Conexão com o servidor estabelecida...")

    # Fecho da stream do cliente
    # Corresponde ao botão Teardown na janela do cliente
    # 1. Destroi a root window (usada pela biblioteca Tk para apresentar o vídeo)
    # 2. Removido o ficheiro cache
    # 3. É fechada a conexão UDP com o servidor (Porta RTP) -> stopStream()
    # 4. A porta RTP é fechada -> self.rtpSocket.close()
    def exitClient(self):
        """Teardown button handler."""
        self.master.destroy()  # Close the gui window
        os.remove(CACHE_FILE_NAME + str(self.sessionId) +
                  CACHE_FILE_EXT)  # Delete the cache image from video
        self.stopStream()
        self.rtpSocket.close()

    # Paragem da stream RTP
    # O cliente envia para o servidor um pedido de paragem da stream RTP (Porta 5004)
    # Uma vez que não está mais interessado em ver a stream
    def stopStream(self):
        """Stop button handler."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.serverAddr, 5004))
        s.close()

    # Método que inicia a visualização do video
    # 1. É criada uma thread para receber os pacotes RTP (listenRtp)
    # 2. Corresponde ao botão Play na janela do cliente
    def playMovie(self):
        """Play button handler."""
        # Create a new thread to listen for RTP packets
        threading.Thread(target=self.listenRtp).start()


    # Método que recebe os pacotes RTP
    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                # Fica a espera de receber um pacote RTP (pela porta RTP enviada pelo cliente)
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))

                    # Depois de obter corretamente a info do pacote -> (com a classe RtpPacket -> decode)
                    # Verifica se o número do frame recebido é superior ao número do frame atual do cliente
                    # Para a stream fluir suavemente são descartados frames que chegam atrasados
                    if currFrameNbr > self.frameNbr:  # Discard the late packet
                        self.frameNbr = currFrameNbr
                        # Depois de atualizar o número do frame atual do cliente é realizado o update do video
                        self.updateMovie(
                            self.writeFrame(rtpPacket.getPayload()))
            except:
                # No caso de ser pedido o teardown (ou ocorreu um erro)
                self.rtpSocket.shutdown(socket.SHUT_RDWR)
                self.rtpSocket.close()
                break

    # Método que escreve o frame recebido num ficheiro temporário
    # Este ficheiro é escrito com o número da sessão do cliente
    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    # Método que atualiza o video
    # 1. É aberto o ficheiro temporário com o frame recebido (diferenciado pelo número da sessão do cliente)
    # 2. Usa a biblioteca Tkinter para apresentar o frame recebido
    # 3. É atualizado o label da janela do cliente com o frame recebido
    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    # Método que abre a porta RTP do cliente
    # 1. É criado um socket UDP à escuta na porta RTP do cliente (escolhida pelo utilizador)
    # 2. É feito o bind do socket à porta RTP do cliente
    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        #self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port
            self.rtpSocket.bind((self.clientAddr, int(self.clientPort)))
            print('\nBind \n')
        except:
            messagebox.showwarning('Unable to Bind',
                                   'Unable to bind PORT=%d' % int(self.clientPort))

    # Método que é chamado quando o utilizador fecha a janela do cliente
    # 1. É apresentado um popup ao utilizador para confirmar se quer mesmo fechar a janela
    # 2. Caso o utilizador confirme o fecho da janela é fechada a stream RTP (stopStream)
    # 3. Caso contrário, a stream RTP continua a ser recebida
    def handler(self):
        """Handler on explicitly closing the GUI window."""
        if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
