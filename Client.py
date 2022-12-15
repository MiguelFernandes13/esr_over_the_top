import sys
from tkinter import Tk

from ClientGUI import ClientGUI

# Ficheiro para o launch do cliente
# Este recebe o endereço IP do cliente, a porta RTP para o streaming e o endereço IP do servidor
if __name__ == "__main__":
    try:
        clientAddr = sys.argv[1]
        clientPort = sys.argv[2]
        serverAddr = sys.argv[3]
    except:
        print("[Usage: Client.py <Client_Addr> <Client_Port> <Server_Addr>]\n")

# Root window da biblioteca Tk
root = Tk()

# Create a new client
app = ClientGUI(root, clientAddr, clientPort ,serverAddr)
app.master.title("Cliente ESR")
# Inicia a root window (janela gráfica do utilizador)
root.mainloop()
