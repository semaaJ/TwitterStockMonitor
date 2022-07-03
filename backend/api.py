import os
import json

from flask_cors import CORS
from flask import Flask, jsonify, request
from constants import DIRECTORIES
  
app = Flask(__name__)
CORS(app)

@app.route('/', methods = ['GET'])
def index():
    if request.method == 'GET':
        response_obj = { directory: {} for directory in DIRECTORIES}
        for directory in DIRECTORIES:
            files = os.listdir(f'{os.curdir}/{directory}/')

            for f in files:
                name = f.split(".")[0]
                with open(f'./{directory}/{f}', 'r') as nf:
                    response_obj[directory][name] = json.load(nf)

        return response_obj

    return {}


  
if __name__=='__main__':
    app.run(debug=True)