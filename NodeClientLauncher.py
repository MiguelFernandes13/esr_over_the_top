import sys
from NodeClient import NodeClient

if __name__ == '__main__':
    try:
        serverAddr = sys.argv[1]
        serverPort = sys.argv[2]
        port = sys.argv[3]

    except:
        print(
            "[Usage: NodeClientLauncher.py <Server_Addr> <Server_Port> <Client_Addr>]\n"
        )

    client = NodeClient(serverAddr, serverPort, port)
    client.main()
