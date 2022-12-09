import sys
from NodeClient import NodeClient

if __name__ == '__main__':
    try:
        serverAddr = sys.argv[1]

    except:
        print(
            "[Usage: NodeClientLauncher.py <Server_Addr>]\n"
        )

    client = NodeClient(serverAddr)
    client.main()
