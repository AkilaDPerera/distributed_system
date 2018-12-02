python3 is required to run the system.
Since there is a user interface, following two modules should be installed
if they are not already present.

1. flask
2. requests

    installation: pip3 install flask requests

How to run nodes?
    
    commands to run a node.
    python3 serverNode.py portOftheBootstrapServer BootstrapServerIp IpOfTheMachineNodeIsIn

    Example: python3 serverNode.py 9000 192.168.42.244 192.168.42.242
             port of the bootstrap server = 9000
             ip address of the bootstrap server = 192.168.42.244
             ip of the node = 192.168.42.242