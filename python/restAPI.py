from client import *
from restFileServer import *
import os
import webbrowser


main()
app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/show_nodes", methods=['POST'])
def show_nodes(): 
    return render_template('index.html', data = query("show"))

@app.route("/search_files", methods=['POST'])
def search_files(): 
    # print(request.form["filename"])
    return render_template('index.html', data = query("search "+ request.form["filename"]))

@app.route("/download_file", methods=['POST'])
def download_file(): 
    print("http://"+request.form["ip"] + ":" + request.form["port"] + "/" + request.form["filename"])
    return redirect("http://"+request.form["ip"] + ":" + request.form["port"] + "/" + request.form["filename"])

url = "http://"+my_ip+":"+str(my_web_server_port)+"/"

threading.Timer(1.25, lambda: webbrowser.open(url)).start()


def app1():
    app.run(host= my_ip, port=my_web_server_port)

def app2():
    fileServer.run(host= my_ip, port=my_file_server_port)

if __name__=='__main__':
    threading.Thread(target=app1).start()
    threading.Thread(target=app2).start()
