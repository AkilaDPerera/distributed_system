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
        return self.ip == other.ip and self.port == other.port

    def __repr__(self):
        return "%s %d" % (self.ip, self.port)


class Server(threading.Thread):
    buffer_size = 2048

    def __init__(self, address):
        threading.Thread.__init__(self)
        self.ip = address.ip
        self.port = address.port

    def decodeMessage(self, message):
        res = message.split()
        if res[1].lower() == 'give':
            address = Address(res[2], int(res[3]), res[4])
            addNewNode(address)
            if len(nodes) > 0:
                if len(nodes) == 1:
                    msg = "TAKE 1 %s %d %s" % (nodes[0].ip, nodes[0].port, nodes[0].username)
                    print(msg)
                    return msg
                else:
                    first = random.randint(0, len(nodes) - 1)
                    second = -1;
                    while True:
                        second = random.randint(0, len(nodes) - 1)
                        if second != first:
                            break
                    msg = "TAKE 2 %s %d %s %s %d %s" % (
                        nodes[first].ip, nodes[first].port, nodes[first].username, nodes[second].ip, nodes[second].port,
                        nodes[second].username)
                    print(msg)
                    return msg
        else:
            return "Hi"

    def run(self):
        print("Starting client-side server...")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind((self.ip, self.port))

            while True:
                req, address = server.recvfrom(buffer_size)
                incoming_msg = req.decode()
                incoming_address = address[0]
                incoming_port = int(address[1])

                print("Message received: '%s' \t Address received: %s:%d" % (
                    incoming_msg, incoming_address, incoming_port))

                server.sendto(attach_length(self.decodeMessage(incoming_msg)).encode(), address)


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


my_ip = netifaces.ifaddresses('wlp3s0')[netifaces.AF_INET][0]['addr']  # you need to change eth0 accordingly.
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

nodeLimit = 3


def main():
    global nodes

    # Let's start the listening socket
    server_thread = Server(my_address)
    server_thread.start()

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

    gosip = Gather()
    gosip.start()

    print("continue main thread...")

    while True:
        query()


def unreg(address):
    # Unregister from boostrap
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        reg_msg = "UNREG %s %d %s" % (address.ip, address.port, address.username)
        s.sendall(attach_length(reg_msg).encode())


def sendMessage(msg, address, retFun):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.settimeout(3)
        for shy in range(2):
            try:
                connection.sendto(attach_length(msg).encode(), (address.ip, address.port))
                res, address = connection.recvfrom(buffer_size)
                retFun(res.decode())
                break
            except:
                print(shy)
                pass
        else:
            unreg(address)
            nodes.remove(address)


def show_neighbours():
    print(nodes)


def hi(neighbour):
    # Say hi to node
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        req = "Hi, I am %s. What is name?" % (my_address.username)
        connection.sendto(req.encode(), (neighbour.ip, neighbour.port))


def query():
    command = input("Enter your command: ").strip().lower()

    if command == "show":
        show_neighbours()

    elif command == "my":
        print("My Ip: %s %d %s" % (my_ip, my_port, my_name))

    elif command.startswith("hi"):
        cmd_list = command.split()
        try:
            ip = cmd_list[1]
            port = int(cmd_list[2])
            neighbour = Address(ip, port)
            hi(neighbour)
        except:
            print("Wrong syntax...")


def addNewNode(address):
    exist = False
    for node in nodes:
        if node.ip == address.ip and node.port == address.port:
            exist = True
            break
    if (not exist) and address != my_address:
        nodes.append(address)


def takeIPsOfPeer(msgRet):
    print("msg recieved: %s" % (msgRet))
    res = msgRet.strip().split()
    if res[1].lower() == 'take':
        peerCount = int(res[2])
        if peerCount == 2:
            print("Count 2: %s %s %s | %s %s %s" % (res[3], res[4], res[5], res[6], res[7], res[8]))
            addNewNode(Address(res[3], int(res[4]), res[5]))
            addNewNode(Address(res[6], int(res[7]), res[8]))
        elif peerCount == 1:
            print("Count 1: %s %s %s" % (res[3], res[4], res[5]))
            addNewNode(Address(res[3], int(res[4]), res[5]))


class Gather(threading.Thread):
    buffer_size = 2048

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print("Gossiping solution start...")
        while True:
            if 0 < len(nodes) < nodeLimit:
                address = nodes[random.randint(0, len(nodes) - 1)]
                msg = "GIVE %s %d %s" % (my_ip, my_port, my_name)
                sendMessage(msg, address, takeIPsOfPeer)
            time.sleep(4)


main()
