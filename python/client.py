#!/usr/bin/env python3

import socket

class Address():
    self.ip = ""
    self.port = ""

    def __init__(self, ip, port):
        


HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65000        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'0036 REG 127.0.0.10 8003 naveen')
    data = s.recv(1024)

print(data.decode())