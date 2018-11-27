# distributed_system
System that is going to share some set of files among many number of nodes

# starting virtual env
source env/bin/activate

# start the client when bootsrap on port 65000
source env/bin/activate
python3 python/restService.py 65000


# start the shell_client when bootsrap on port 65000
source env/bin/activate
cd python
python3 shell_client.py 65000

# Get permission
sudo chmod -R a+rwX *