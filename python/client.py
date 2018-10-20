#!/usr/bin/env python3

import socket
import random
import threading
import netifaces
import string
import sys
import time

class Address():
    def __init__(self, ip, port, username=""):
        self.ip = ip
        self.port = int(port)
        self.username = username

    def __eq__(self, other):
        return (self.ip==other.ip) and (self.port==other.port)

    def __repr__(self):
        return "%s %d %s" % (self.ip, self.port, self.username)

class LinkTest(threading.Thread):
    def __init__(self, socket, sender, to):
        threading.Thread.__init__(self)
        self.socket = socket
        self.sender = sender
        self.to = to
    
    def is_link_connected(self, address):
        req = "ACTIVE %s %d %s" % (address.ip, address.port, address.username)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.settimeout(1)
            for shy in range(2):
                try:
                    connection.sendto(attach_length(req).encode(), (address.ip, address.port))
                    res, address = connection.recvfrom(buffer_size)
                    return True
                except:
                    pass
            else:
                return False

    def run(self):
        addresses = nodes[:] # make a copy
        if (self.sender in addresses): addresses.remove(self.sender) # remove sender from the list

        # check for valid addresses
        take_addresses = []
        while len(take_addresses)<2 and len(addresses)>0:
            addr = random.choice(addresses)
            is_connected = self.is_link_connected(addr)

            if is_connected: 
                take_addresses.append(addr)
            else:
                remove_from_nodes(addr)
            
            addresses.remove(addr)
        
        take_res = ""
        if len(take_addresses)==0:
            take_res = "ACTIVEOK"

        elif len(take_addresses)==1:
            take_res = "TAKE 1 %s %d %s"%(take_addresses[0].ip, take_addresses[0].port, take_addresses[0].username)

        elif len(take_addresses)==2:
            take_res = "TAKE 2 %s %d %s %s %d %s"%(take_addresses[0].ip, take_addresses[0].port, take_addresses[0].username, take_addresses[1].ip, take_addresses[1].port, take_addresses[1].username)
        
        self.socket.sendto(attach_length(take_res).encode(), self.to)

    

class Server(threading.Thread):
    def __init__(self, address):
        threading.Thread.__init__(self)
        self.ip = address.ip
        self.port = address.port

    def decode_give_request(self, req):
        req = req.split()

        num_char = int(req.pop(0))
        command = req.pop(0)

        addresses_ip = req.pop(0)
        addresses_port = int(req.pop(0))
        addresses_username = req.pop(0)

        addr = Address(addresses_ip, addresses_port, addresses_username)

        if not(addr in nodes):
            nodes.append(addr)
        
        return addr
    
    def decode_leave_request(self, req):
        req = req.split()

        num_char = int(req.pop(0))
        command = req.pop(0)

        addresses_ip = req.pop(0)
        addresses_port = int(req.pop(0))
        addresses_username = req.pop(0)

        addr = Address(addresses_ip, addresses_port, addresses_username)

        remove_from_nodes(addr)

    def run(self):
        print("Starting client-side server...")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind((self.ip, self.port))

            while True:
                req, address = server.recvfrom(buffer_size)
                incoming_msg = req.decode()
                incoming_address = address[0]
                incoming_port = int(address[1])

                req = incoming_msg.split()
                req_length = int(req[0])
                req_command = req[1]

                # Check kill switch first
                if kill_switch==1: 
                    print("Client-side server shutdown...")
                    break

                if req_command=="GIVE":
                    sender_addr = self.decode_give_request(incoming_msg)
                    LinkTest(server, sender_addr, address).start()

                elif req_command=="ACTIVE":
                    server.sendto(attach_length("ACTIVEOK").encode(), address)

                elif req_command=="LEAVE":
                    self.decode_leave_request(incoming_msg)

                elif req_command=="Hi":
                    print(incoming_msg)

class Gossiping(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def request_addresses(self): # GIVE Request
        if len(nodes)>0:
            to = random.choice(nodes)
            req = "GIVE %s %d %s" % (my_ip, my_port, my_name)

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
                connection.settimeout(1)
                for shy in range(2):
                    try:
                        connection.sendto(attach_length(req).encode(), (to.ip, to.port))
                        res, address = connection.recvfrom(buffer_size)
                        return res.decode()
                        break
                    except:
                        pass
                else:
                    remove_from_nodes(to)

    def update_nodes(self, res_of_give):
        res = res_of_give.split()

        num_char = int(res.pop(0))
        status = res.pop(0)
        num_addresses = int(res.pop(0))

        addr = []
        for address_no in range(num_addresses):
            ip = res.pop(0)
            port = int(res.pop(0))
            username = res.pop(0)
            addr.append(Address(ip, port, username))
        
        for add in addr:
            if not(add in nodes):
                nodes.append(add)

    def run(self):
        print("Gossiping solution start...")
        while True:
            if len(nodes) >= node_limit:
                # TODO Let's have a suitable logic here

                # # isactive request should be here                                          TODO
                # res = self.request_addresses() # response = None | ACTIVEOK | IPs
                # if (res!=None):
                #     if res.split()[1]!="ACTIVEOK":
                #         self.update_nodes(res)
                # time.sleep(3)
                print("Exit gossiping...")
                break

            elif len(nodes) < node_limit:
                res = self.request_addresses() # response = None | ACTIVEOK | IPs
                if (res!=None):
                    if res.split()[1]!="ACTIVEOK":
                        self.update_nodes(res)
                time.sleep(5)
            
            # Check kill switch
            if kill_switch==1: 
                print("Gossiping shutdown...")
                break

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

    if num_addresses == 9999:
        return 0, "Failed, There is an error in the command"
    elif num_addresses == 9998:
        return 0, "Failed, Already registered to you, unregister first"
    elif num_addresses == 9997:
        return 0, "Failed, Registered to another user, try a different IP and Port"
    elif num_addresses == 9996:
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

def get_available_port(ip):
    init_port = 6000
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    result = False
    while True:
        try:
            sock.bind((ip, init_port))
            sock.close()
            result = True
            break
        except:
            init_port += 1
    return init_port

def attach_length(message):
    length = len(message) + 5
    return "%04d %s" % (length, message)

def remove_from_nodes(node_address):
    try:
        nodes.remove(node_address)
    except:
        pass

def unreg():
    # Unregister from boostrap
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        reg_msg = "UNREG %s %d %s" % (my_address.ip, my_address.port, my_address.username)
        s.sendall(attach_length(reg_msg).encode())


def main():
    global nodes

    # Let's start the listening socket
    server_thread = Server(my_address).start()

    # Registration with bootstrap
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        reg_msg = "REG %s %d %s" % (my_address.ip, my_address.port, my_address.username)
        s.sendall(attach_length(reg_msg).encode())
        data = s.recv(buffer_size).decode()

        isSuccess, addresses = decode_reg_response(data)

        if isSuccess:
            if len(addresses) > 2:
                # Select two random links
                address_1 = random.randint(0, len(addresses) - 1)
                address_2 = random.randint(0, len(addresses) - 1)
                while address_1 == address_2:
                    address_2 = random.randint(0, len(addresses) - 1)
                nodes.append(addresses[address_1])
                nodes.append(addresses[address_2])
            else:
                nodes = addresses
    # Registration with bootstrap done

    # Let's start the gossiping
    gossiping_thread = Gossiping().start()

    print("continue main thread...")

    while True:
        query()

def show_neighbours():
    print(nodes)

def show_me():
    print("My Details: %s %d %s" % (my_ip, my_port, my_name))

def say_hi(address):
    msg = "Hi my name is %s. What's your's?"%(my_name)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.sendto(attach_length(msg).encode(), (address.ip, address.port))
    
def leave():
    global kill_switch
    kill_switch = 1

    # Tell neighbors #length LEAVE IP_address port_no
    req = "LEAVE %s %d %s"%(my_ip, my_port, my_name)
    req = attach_length(req)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        for node in nodes:
            connection.sendto(req.encode(), (node.ip, node.port))

    # Tell BS
    unreg()
    exit(0)
    

def query():
    command = input("Enter your command: ").strip().lower()

    if command=="show":
        show_neighbours()
    elif command=="my":
        show_me()
    elif command=="exit":
        leave()
    elif command.startswith("hi"): # hi ip port
        cmmd = command.split()
        try:
            add = Address(cmmd[1], int(cmmd[2]))
            say_hi(add)
        except:
            pass

my_ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']  # you need to change eth0 accordingly.
my_port = get_available_port(my_ip)
my_name = "".join([random.choice(string.ascii_letters) for i in range(5)])
my_address = Address(my_ip, my_port, my_name)

# Boostrap server config
HOST = my_ip
PORT = 65000
if len(sys.argv) == 3:
    # port and ip given
    try:
        PORT = int(sys.argv[1])
        HOST = sys.argv[2].strip()
    except:
        print("Error in input parameters")
        exit(0)
elif len(sys.argv) == 2:
    # port given
    try:
        PORT = int(sys.argv[1])
    except:
        print("Error in input parameters")
        exit(0)

nodes = []

buffer_size = 2048

node_limit = 10

kill_switch = 0

main()
