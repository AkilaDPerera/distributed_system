from globalVariables import *

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