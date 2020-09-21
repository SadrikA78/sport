import json
from collections import Counter
#basedir = os.path.abspath(os.path.dirname(__file__))

def updateDataFrame(centr,phone):
    #table = pd.read_csv("table.csv")
    slovar = readData()
    if centr in slovar.keys():
        slovar[centr].append(phone)
    else:
        slovar.update({centr:[(phone)]})
    writeData(slovar)
    return ("ok")

def returnCount(centr):
    try:
        slovar = readData()
        return len(Counter(slovar[centr]))
    except:
        return 0

def readData():
    with open('history.json', 'r',encoding='utf-8') as fh: #открываем файл с данными о исполнителях на чтение
        slovar = json.load(fh)
    return(slovar)

def writeData(new):
    with open("history.json", "w", encoding='utf-8') as write_file:
        json.dump(new, write_file)
    return ('ok')