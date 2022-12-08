import sys
from tkinter import Tk

from Client.ClientGUI import ClientGUI

if __name__ == "__main__":
    try:
        serverAddr = sys.argv[1]
        clientAddr = sys.argv[2]
    except:
        print("[Usage: Client.py <Server_Addr> <Client_Addr> ]\n")

root = Tk()

# Create a new client
app = ClientGUI(root, clientAddr, serverAddr)
app.master.title("Cliente ESR")
root.mainloop()
