import socket
from ttypes import Node
from random import shuffle

class BootstrapServerConnection:
    def __init__(self, bs, me):
        self.bs = bs
        self.me = me
        self.users = []

    def __enter__(self):
        self.users = self.connect_to_bs()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.unreg_from_bs()

    def message_with_length(self, message):
        '''
        Helper function to prepend the length of the message to the message itself
        Args:
            message (str): message to prepend the length
        Returns:
            str: Prepended message
        '''
        message = " " + message
        message = str((10000+len(message)+5))[1:] + message
        return message

    def connect_to_bs(self):
        '''
        Register node at bootstrap server.
        Args:
            bs (Node): Bootstrap server node
            me (Node): This node
        Returns:
            list(Node) : List of other nodes in the distributed system
        Raises:
            RuntimeError: If server sends an invalid response or if registration is unsuccessful
        '''
        self.unreg_from_bs()
        buffer_size = 1024
        message = "REG "+ self.me.ip + " " +str(self.me.port) +" " + self.me.name

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.bs.ip, self.bs.port))
        s.send(self.message_with_length(message))
        data = s.recv(buffer_size)
        s.close()
        print(data)
        
        toks = data.split()
        
        if (len(toks) < 3):
            raise RuntimeError("Invalid message")
        
        if (toks[1] != "REGOK"):
            raise RuntimeError("Registration failed")
        
        num = int(toks[2])
        if (num < 0):
            raise RuntimeError("Registration failed")
            
        if (num == 0):
            return []
        elif (num == 1):
            return [Node(toks[3], int(toks[4]), toks[5])]
        else:
            l = range(1, num+1)
            shuffle(l)
            return [Node(toks[l[0]*3], int(toks[l[0]*3+1]), toks[l[0]*3+2]), Node(toks[l[1]*3], int(toks[l[1]*3+1]), toks[l[1]*3+2])]
        
    def unreg_from_bs(self):
        '''
        Unregister node at bootstrap server.
        Args:
            bs (tuple(str, int)): Bootstrap server IP address and port as a tuple.
            me (tuple(str, int)): This node's IP address and port as a tuple.
            myname (str)        : This node's name
        Returns:
            list(tuple(str, int)) : List of other nodes in the distributed system
        Raises:
            RuntimeError: If unregistration is unsuccessful
        '''
        buffer_size = 1024
        message = "UNREG "+ self.me.ip + " " +str(self.me.port) +" " + self.me.name

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.bs.ip, self.bs.port))
        s.send(self.message_with_length(message))
        data = s.recv(buffer_size)
        s.close()
        
        toks = data.split()
        if (toks[1] != "UNROK"):
            raise RuntimeError("Unreg failed")
