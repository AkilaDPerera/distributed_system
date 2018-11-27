from globalVariables import *

class Gossiping(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def is_link_connected(self):
        address = random.choice(nodes)
        req = "ACTIVE %s %d %s" % (address.ip, address.port, address.username)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.settimeout(1)
            for shy in range(2):
                try:
                    connection.sendto(attach_length(req).encode(), (address.ip, address.port))
                    res, address = connection.recvfrom(buffer_size)
                    break
                except:
                    pass
            else:
                remove_from_nodes(address)

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
                self.is_link_connected()
                time.sleep(5)
                
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