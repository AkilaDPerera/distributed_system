from client import *
from flask import Flask, request, render_template, send_file, redirect
import os
import webbrowser
import requests


main()
app = Flask(__name__)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/show_nodes", methods=['POST'])
def show_nodes():
    if request.form["submit_button"] == "show_nodes":
        return render_template('index.html', data = query("show"))
    elif request.form["submit_button"] == "show_files":
        return render_template('index.html', data = query("showfiles"))

@app.route("/search_files", methods=['POST'])
def search_files(): 
    return render_template('index.html', data = query("search "+ request.form["filename"]), formTypeSearch = True)

@app.route("/download_file", methods=['POST'])
def download_file(): 
    print("http://"+request.form["ip"] + ":" + request.form["port"] + "/" + request.form["filename"])
    return redirect("http://"+request.form["ip"] + ":" + request.form["port"] + "/" + request.form["filename"])

@app.route("/kill_node", methods=['POST'])
def kill_node():
    try:
        requests.get("http://"+my_ip+":"+str(my_file_server_port)+"/kill")
    except:
        pass
    query("exit")
    shutdown_server()
    return "KILLED THE NODE"
    

url = "http://"+my_ip+":"+str(my_web_server_port)+"/"

threading.Timer(1.25, lambda: webbrowser.open(url)).start()
