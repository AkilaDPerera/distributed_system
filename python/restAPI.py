from flask import Flask, request, render_template
from globalVariables import *
app = Flask(__name__)

@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/show_nodes", methods=['POST'])
def show_nodes(): 
    return render_template('index.html', data = query("show"))

@app.route("/search_files", methods=['POST'])
def search_files(): 
    return render_template('index.html', data = [12, 45])

# if __name__ == '__main__':
app.run(host= my_ip, port=my_file_server_port)