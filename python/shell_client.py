#!/usr/bin/env python3

import socket
import random
import threading
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
            connection.settimeout(40)
            try:
                connection.sendto(attach_length(req).encode(), (address.ip, address.port))
                res, address = connection.recvfrom(buffer_size)
                return True
            except:
                print("Error is link connected\n")
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

class FileTransfer(threading.Thread):
    def __init__(self, address):
        threading.Thread.__init__(self)
        self.ip = address.ip
        self.port = address.port
    
    def is_file_available(self, filename):
        for f_name in files:
            if filename.lower()==f_name.lower():
                return f_name
        else:
            return False

    def run(self):
        print("Starting file transfer server...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.ip, self.port))
            while True:
                s.listen()
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(buffer_size)
                    data = data.decode()
                    parts = data.split()

                    num_char = int(parts[0])
                    command = parts[1]

                    # Check kill switch
                    if kill_switch==1: 
                        print("File transfer server shutdown...")
                        break

                    if command=="DOWNLOAD":
                        filename = parts[2].replace("_", " ")
                        # check availability of file
                        filename = self.is_file_available(filename)
    
                        if filename!=False:
                            # send file
                            with open(file_source+filename, 'rb') as f:
                                conn.sendall(f.read())
                        else:
                            res = "Invalid filename"
                            conn.sendall(res.encode())
                
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

    def decode_search_request(self, req, server):
        # length SER IP port file_name hops
        req = req.split()
        num_char = int(req.pop(0))
        command = req.pop(0)

        initiator_ip = req.pop(0)
        initiator_port = int(req.pop(0))
        filename = req.pop(0)
        hops = int(req.pop(0))

        # Check availability of file
        matching_files = []
        for f_name in files:
            filename_spaces = filename.replace("_", " ")
            if filename_spaces.lower() in f_name.lower():
                matching_files.append(f_name)
        
        if len(matching_files)==0:
            if hops<hops_limit:
                # pass req to neighbors
                req2 = "SER %s %d %s %d"%(initiator_ip, initiator_port, filename, hops+1)
                req2 = attach_length(req2)

                # Send to all neighbors
                for node in nodes:
                    server.sendto(req2.encode(), (node.ip, node.port))
        else:
            # length SEROK no_files IP port hops filename1 filename2 ... ...
            res = "SEROK %d %s %d %d "%(len(matching_files), my_address.ip, my_file_server_port, hops+1)
            res += " ".join(matching_files)
            res = attach_length(res)
            server.sendto(res.encode(), (initiator_ip, initiator_port))

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

                elif req_command=="SER":
                    self.decode_search_request(incoming_msg, server)
                
                elif req_command=="SEROK":
                    print()
                    print(incoming_msg)

class Gossiping(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def is_link_connected(self):
        address = random.choice(nodes)
        req = "ACTIVE %s %d %s" % (address.ip, address.port, address.username)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.settimeout(40)
            try:
                connection.sendto(attach_length(req).encode(), (address.ip, address.port))
                res, address = connection.recvfrom(buffer_size)
                break
            except:
                remove_from_nodes(address)
                print("Gossiping Error is link connected\n")
                

    def request_addresses(self): # GIVE Request
        if len(nodes)>0:
            to = random.choice(nodes)
            req = "GIVE %s %d %s" % (my_ip, my_port, my_name)

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
                connection.settimeout(40)
                try:
                    connection.sendto(attach_length(req).encode(), (to.ip, to.port))
                    res, address = connection.recvfrom(buffer_size)
                    return res.decode()
                except:
                    remove_from_nodes(to)
                    print("Gossiping Error request_address")

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
                self.is_link_connected()
                time.sleep(20)
                
            elif len(nodes) < node_limit:
                res = self.request_addresses() # response = None | ACTIVEOK | IPs
                if (res!=None):
                    if res.split()[1]!="ACTIVEOK":
                        self.update_nodes(res)
                time.sleep(20)
            
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

def get_available_port(ip, init_port):
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

def get_available_tcp_port(ip, init_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        print("Error remove_from_nodes")

def unreg():
    # Unregister from boostrap
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        reg_msg = "UNREG %s %d %s" % (my_address.ip, my_address.port, my_address.username)
        s.sendall(attach_length(reg_msg).encode())

def show_neighbours():
    print(nodes)

def show_files():
    print(files)

def show_me():
    print("My Details: %s %d %s | FileTPort: %d" % (my_ip, my_port, my_name, my_file_server_port))

def search(filename):
    # first check whether I'm having the file
    matching_files = []
    filename_spaces = filename.replace("_", " ")
    for f_name in files:
        if filename_spaces.lower() in f_name.lower():
            matching_files.append(f_name)

    # length SER IP port file_name hops
    req = "SER %s %d %s 0"%(my_address.ip, my_address.port, filename)
    req = attach_length(req)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        # Send to all neighbors
        for node in nodes:
            connection.sendto(req.encode(), (node.ip, node.port))
            
    if len(matching_files)>0:
        # length SEROK no_files IP port hops filename1 filename2 ... ...
        res = "SEROK %d %s %d %d "%(len(matching_files), my_address.ip, my_file_server_port, 0)
        res += " ".join(matching_files)
        res = attach_length(res)
        print("\n"+res)

def leave():
    global kill_switch
    kill_switch = 1

    req = "LEAVE %s %d %s"%(my_ip, my_port, my_name)
    req = attach_length(req)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection: #UDP socket
        # shutdown gossiping self destruction
        # shutdown server (need to trigger)
        connection.sendto(req.encode(), (my_ip, my_port))

        # Tell neighbors #length LEAVE IP_address port_no
        for node in nodes:
            connection.sendto(req.encode(), (node.ip, node.port))
        
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # TCP socket
        s.connect((my_ip, my_file_server_port))
        # shutdown file server (need to trigger)
        s.sendall(req.encode())

    # Tell BS
    unreg()

    exit(0)
    
def download(frm, filename):
    filename = filename.replace(" ", "_")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((frm.ip, frm.port))
        req = "DOWNLOAD %s"%(filename)
        s.sendall(attach_length(req).encode())
        msg_bytes = []
        while True:
            data = s.recv(buffer_size)
            if not data:
                break
            else:
                msg_bytes.append(data)
                

        if msg_bytes[0]==b'Invalid filename':
            print("Invalid Filename. Check the filename and retry.")
        else:
            with open(download_loc+filename, "wb") as f:
                for msg_byte in msg_bytes:
                    f.write(msg_byte)
            print("File has been downloaded ...")


def query():
    command = input("Enter your command: ").strip().lower()

    if command=="show":
        show_neighbours()
    elif command=="my":
        show_me()
    elif command=="showfiles":
        show_files()
    elif command=="exit":
        leave()
    elif command.startswith("search"):
        cmmd = command.split()
        try:
            filename = "_".join(cmmd[1:])
            search(filename)
        except:
            pass
    elif command.startswith("download"): # download ip port filename
        cmmd = command.split()
        try:
            ip = cmmd[1]
            port = int(cmmd[2])
            filename = " ".join(cmmd[3:])
            download(Address(ip, port), filename)
        except:
            print("Something went wrong. Please check the ip, port and filename again.")

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

    # Let's start file server
    file_server_thread = FileTransfer(Address(my_ip, my_file_server_port)).start()

    # Let's start the gossiping
    gossiping_thread = Gossiping().start()

    print("continue main thread...")

    while True:
        query()

all_files = [
    "Adventures of Tintin.jpg",
    "Jack and Jill.jpg",
    "Glee.jpg",
    "The Vampire Diarie.jpg",
    "King Arthur.jpg",
    "Windows XP.jpg",
    "Harry Potter.jpg",
    "Kung Fu Panda.png",
    "Lady Gaga.jpg",
    "Twilight.png",
    "Windows 8.webp",
    "Mission Impossible.jpg",
    "Turn Up The Music.jpg",
    "Super Mario.jpg",
    "American Pickers.jpg",
    "Microsoft Office 2010.jpg",
    "Happy Feet.jpg",
    "Modern Family.jpg",
    "American Idol.jpg",
    "Hacking for Dummies.jpg",
]

# select 3-5 files randomly from above
file_count = random.randint(3, 5)
files = []
while len(files)<file_count:
    filename = random.choice(all_files)
    if not(filename in files):
        files.append(filename)

file_source = "./files/"
download_loc = "./download/"

# my_ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']  # you need to change eth0 accordingly.
my_ip = sys.argv[3].strip()
my_port = get_available_port(my_ip, 6000)
my_file_server_port = get_available_tcp_port(my_ip, 9000)
my_name = "".join([random.choice(string.ascii_letters) for i in range(5)])
my_address = Address(my_ip, my_port, my_name)

# Boostrap server config

HOST = my_ip
PORT = 65000
if len(sys.argv) >= 3:
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

node_limit = 3

hops_limit = 3

kill_switch = 0

main()
