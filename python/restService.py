from restAPI import *

fileServer = Flask(__name__)

@fileServer.route("/<filename>", methods=['GET'])
def download_files(filename): 
    print(filename)
    if filename in files:
        return send_file('files/'+ filename, attachment_filename=filename)
    else:
        return "I AM NOT SERVING THE FILE " + filename

@fileServer.route("/favicon.ico", methods=['GET'])
def favicon():
    return send_file('static/favicon.ico', attachment_filename='favicon.ico')

@fileServer.route("/kill", methods=['GET'])
def kill():
    shutdown_server()
    return "Server Shutting DOWN"

def app1():
    app.run(host= my_ip, port=my_web_server_port)

def app2():
    fileServer.run(host= my_ip, port=my_file_server_port)

if __name__=='__main__':
    threading.Thread(target=app1).start()
    threading.Thread(target=app2).start()