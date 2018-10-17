#!/usr/bin/env python3

# bootstrap server

# BS: 60000
# Nodes: 80000 - 90000

class BootstrapServer:
    def __init__(self):
        self.max_nodes = 5 # Change the max connections
        self.nodes = []
    
    def REG(self, ip, port, username):
        if len(self.nodes)==self.max_nodes: 
            return "REGOK 9996"

        for node in self.nodes:
            if node["ip"]==ip and node["port"]==port and node["username"]==username:
                return "REGOK 9998" # append length before send
            elif node["ip"]==ip and node["port"]==port:
                return "REGOK 9997" # append length before send
        else:
            self.nodes.append({"ip": ip, "port": port, "username": username})
            # send info regarding other nodes
            return "REGOK 0"




import socket

bs = BootstrapServer()

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 60000        # Port to listen on (non-privileged ports are > 1023)

buffer_size = 10 # Can be configured accordingly

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    while True:
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            req = ""
            while True:
                data = conn.recv(buffer_size)
                req += data.decode("utf-8") # default "utf-8"
                if len(data)<buffer_size:
                    break

            response = ""
            # decode the request
            # 1. length REG IP_address port_no username
            decoded_req = req.split()

            if decoded_req[1]=="REG":
                ip = decoded_req[2]
                port = decoded_req[3]
                username = decoded_req[4]
                response = bs.REG(ip, port, username)

            # attach length to response
            response = "b'%04d %s'"%(len(response)+4, response)

            # send acknowledgement
            conn.sendall(response.encode("utf-8")) # default "utf-8"