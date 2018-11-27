import random
import netifaces
import socket
import threading
import string
import sys
import time
from address import Address

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
        pass

def unreg():
    # Unregister from boostrap
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        reg_msg = "UNREG %s %d %s" % (my_address.ip, my_address.port, my_address.username)
        s.sendall(attach_length(reg_msg).encode())

def show_neighbours():
    print(nodes)
    # return nodes

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
        return show_neighbours()
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

my_ip = netifaces.ifaddresses('wlp2s0')[netifaces.AF_INET][0]['addr']  # you need to change eth0 accordingly.
my_port = get_available_port(my_ip, 6000)
my_file_server_port = get_available_tcp_port(my_ip, 9000)
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

node_limit = 3

hops_limit = 3

kill_switch = 0