import sys

from AlternativeServer import AlternativeServer


if __name__ == '__main__':
    try:
        serverAddr = sys.argv[1]

    except:
        print(
            "[Usage: AlternativeServerLauncher.py <Server_Addr>]\n"
        )

    server = AlternativeServer(serverAddr)
    server.main()