import socket
import sys

def main():
    s : socket.socket
    endereco : str
    porta : int

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    endereco = '10.0.0.10'
    porta = 3000

    s.connect((endereco, porta))

    msg, _ = s.recvfrom(1024)

    print(f"Recebi {(msg.decode('utf-8'))}")
    while True:
        pass

if __name__ == '__main__':
    main()