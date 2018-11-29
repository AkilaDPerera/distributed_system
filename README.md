# distributed_system
System that is going to share some set of files among many number of nodes

# starting virtual env
source env/bin/activate

# start the client when bootsrap on port 65000
source env/bin/activate <br/>
python3 python/restService.py 65000 <br/>


# start the shell_client when bootsrap on port 65000
source env/bin/activate <br/>
cd python <br/>
python3 shell_client.py 65000 <br/>

# Get permission
sudo chmod -R a+rwX *

# Run python file 
python3 shell_client.py port bootsrapIp myIp
