from globalVariables import *

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