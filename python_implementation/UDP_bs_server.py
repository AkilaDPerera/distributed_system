#!/usr/bin/env python3

import random

# bootstrap server

# BS: 60000
# Nodes: 80000 - 90000

class BootstrapServer:
    def __init__(self):
        self.max_nodes = 5 # Change the max connections
        self.nodes = []
        self.current_number_nodes = 0
    
    def REG(self, ip, port, username):
        if len(self.nodes)==self.max_nodes: 
            return "REGOK 9996"

        for node in self.nodes:
            if node["ip"]==ip and node["port"]==port and node["username"]==username:
                return "REGOK 9998" # append length before send
            elif node["ip"]==ip and node["port"]==port:
                return "REGOK 9997" # append length before send
        else:
            # REGOK no_nodes IP_1 port_1 IP_2 port_2
            response = "REGOK {} {} {} {} {}"
            if self.current_number_nodes==0:
                response = "REGOK 0"
            elif self.current_number_nodes==1:
                node1 = self.nodes[0]
                response = "REGOK 1 {} {}".format(node1["ip"], node1["port"])
            elif self.current_number_nodes==2:
                node1 = self.nodes[0]
                node2 = self.nodes[1]
                response = response.format(2, node1["ip"], node1["port"], node2["ip"], node2["port"])
            else:
                node1 = random.choice(self.nodes)
                node2 = random.choice(self.nodes)
                while node1==node2: node2 = random.choice(self.nodes) # this will guarentee unique two nodes
                response = response.format(len(self.nodes), node1["ip"], node1["port"], node2["ip"], node2["port"])

            # Add the new node
            self.current_number_nodes += 1 
            self.nodes.append({"ip": ip, "port": port, "username": username})
            return response




import socket

bs = BootstrapServer()

BS_HOST = '0.0.0.0'  # Standard loopback interface address (localhost)
BS_PORT = 60000       # Port to listen on (non-privileged ports are > 1023)

buffer_size = 2048 # Can be configured accordingly

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
    server.bind((BS_HOST, BS_PORT))
    print("BS server started to listen...")

    while True:
        req, address = server.recvfrom(buffer_size)
        incoming_req = req.decode("utf-8") # default "utf-8"
        
        incoming_address = address[0]
        incoming_port = address[1]
        print("Message received: %s \t Address received: %s:%s"%(incoming_req, incoming_address, incoming_port))

        response = ""
        # decode the request
        # 1. length REG IP_address port_no username
        decoded_req = incoming_req.split()

        if decoded_req[1]=="REG":
            ip = decoded_req[2]
            port = decoded_req[3]
            username = decoded_req[4]
            response = bs.REG(ip, port, username)




        # Common
        # attach length to response
        response = "%04d %s"%(len(response)+4, response)

        # send acknowledgement
        server.sendto(response.encode("utf-8"), address) # default "utf-8"