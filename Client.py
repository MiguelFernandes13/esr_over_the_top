import sys
from tkinter import Tk

from ClientGUI import ClientGUI

if __name__ == "__main__":
    try:
        clientAddr = sys.argv[1]
        clientPort = sys.argv[2]
        serverAddr = sys.argv[3]
    except:
        print("[Usage: Client.py <Server_Addr> <Client_Addr> ]\n")

root = Tk()

# Create a new client
app = ClientGUI(root, clientAddr, clientPort ,serverAddr)
app.master.title("Cliente ESR")
root.mainloop()
