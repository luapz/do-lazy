#!/usr/bin/env python
# -*- coding:utf-8 -*-

#from board import app
#app.run(host="0.0.0.0", debug=True)

# test.pyとして保存します
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

#if __name__ == "__main__":
 #   app.run()

