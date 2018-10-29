#!/usr/bin/env python3

from globalVariables import *
from linkTest import LinkTest
from gossipping import Gossiping
from fileTransfer import FileTransfer
                
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

    # while True:
    #     query()

main()
