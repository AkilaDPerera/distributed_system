#!/usr/bin/env python3

import socket
import random

class Address():
    def __init__(self, ip, port, username):
        self.ip = ip
        self.port = port
        self.username = username
    
    def __repr__(self):
        return "%s %d"%(self.ip, self.port)

def decode_reg_response(response):
    res = response.split()

    num_char = int(res.pop(0))
    status = res.pop(0)
    num_addresses = int(res.pop(0))

    # Check for errors
    # 9999 – failed, there is some error in the command
    # 9998 – failed, already registered to you, unregister first
    # 9997 – failed, registered to another user, try a different IP and port
    # 9996 – failed, can’t register. BS full.

    if num_addresses==9999:
        return 0, "Failed, There is an error in the command"
    elif num_addresses==9998:
        return 0, "Failed, Already registered to you, unregister first"
    elif num_addresses==9997:
        return 0, "Failed, Registered to another user, try a different IP and Port"
    elif num_addresses==9996:
        return 0, "Failed, Cannot register. BS full."
    else:
        # Here is the success case
        addresses = []
        for address_no in range(num_addresses):
            ip = res.pop(0)
            port = int(res.pop(0))
            username = res.pop(0)
            addresses.append(Address(ip, port, username))
        
        return 1, addresses







clients_msgs = [
    b"0029 REG 127.0.0.1 8000 akila",
    b"0029 REG 127.0.0.1 8001 amila",
    b"0030 REG 127.0.0.1 8002 eminda",
    b"0030 REG 127.0.0.1 8003 eranga",
    b"0031 REG 127.0.0.1 8004 dumindu",
    b"0030 REG 127.0.0.1 8005 jeevan",
]

nodes = []

def main():
    global nodes

    HOST = '127.0.0.1'
    PORT = 65001 # The port used by the boostrap server

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(clients_msgs[4])
        data = s.recv(1024).decode()

        isSuccess, addresses = decode_reg_response(data)

        if isSuccess:
            if len(addresses)>2:
                # Select two random links
                address_1 = random.randint(0, len(addresses)-1)
                address_2 = random.randint(0, len(addresses)-1)
                while address_1==address_2:
                    address_2 = random.randint(0, len(addresses)-1)
                nodes.append(addresses[address_1])
                nodes.append(addresses[address_2])
            else:
                nodes = addresses
        print(addresses)
        print(nodes)
        

main()