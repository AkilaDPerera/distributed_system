class Address():
    def __init__(self, ip, port, username=""):
        self.ip = ip
        self.port = int(port)
        self.username = username

    def __eq__(self, other):
        return (self.ip==other.ip) and (self.port==other.port)

    def __repr__(self):
        return "%s %d %s" % (self.ip, self.port, self.username)
