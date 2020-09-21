import os
from flask import Flask, render_template, request, send_from_directory, jsonify, make_response, json
import json
from read_write import updateDataFrame, returnCount
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)


@app.route('/', methods=['GET'])
def upload():
    try:
        centr = request.args.get('centr')
        section = request.args.get('section')
        data = request.args.get('data')
        return render_template('index.html', centr = centr, section = section, data = data)
    except:
        return render_template('index.html')

@app.route('/authorization/', methods=['POST'])
def authorization():
    try:
        req = json.loads(request.data)
        print('-'*30)
    except:
        print('+'*30)
        return 'O_o'
    updateDataFrame(req['centr'],req['number'])
    updateDataFrame(req['section'],req['number'])
    #_____________Путь к папке с файлами конкретного запроса  
    
    resp = make_response(jsonify({"count_section":returnCount(req['section'])})) #here you could use make_response(render_template(...)) too
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/attachments/<filename>',methods=['GET'])
def send(filename):
    basedir = os.path.abspath(os.path.dirname(__file__))
    #path = os.path.abspath(os.path.join(app.config['UPLOADED_PATH']))
    #print(path + "/" + filename)
    #celery_logger.info(f'{key} - oke. document is available on /attachments/{key}/{filename}')
    return send_from_directory(basedir, filename, as_attachment=False)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1111)