from flask import Flask, request, render_template, send_file, redirect
import os

fileServer = Flask(__name__)

@fileServer.route("/<filename>", methods=['GET'])
def download_files(filename): 
    print(filename)
    return send_file('files/'+ filename, attachment_filename=filename)

@fileServer.route("/favicon.ico", methods=['GET'])
def davicon():
    return send_file('static/favicon.ico', attachment_filename='favicon.ico')