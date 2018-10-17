#!/usr/bin/env python3

import socket

BS_HOST = '0.0.0.0'  # The server's hostname or IP address
BS_PORT = 60000        # The port used by the server

buffer_size = 2048 # Can be configured accordingly

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
    req = "0036 REG 127.0.0.10 80004 eranga"
    connection.sendto(req.encode("utf-8"), (BS_HOST, BS_PORT))
    
    res, address = connection.recvfrom(buffer_size)

print(res.decode())