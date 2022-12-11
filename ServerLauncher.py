import sys

from Server import Server

if __name__ == "__main__":
    try:
        serverAddr = sys.argv[1]
    except:
        print("[Usage: ServerLauncher.py <Server_Num>]")

app = Server(serverAddr)
app.main()