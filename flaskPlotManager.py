import time, multiprocessing, subprocess, os, jsonConf
from tinydb import *

from flask import Flask, request
app = Flask(__name__)
db = TinyDB('db.json')
conf = jsonConf.getConf('conf.json')
searchDb = Query()
totalRequest = 0
hpoolPath = "\""+conf.hpoolControl.path+"/hpool-miner-chia-gui.exe"+"\""

#Checka se o diretorio do HPOOL existe
if conf.hpoolControl.enabled:
    if not os.path.exists(conf.hpoolControl.path):
        print("\nNao foi possivel encontrar o diretorio do HPOLL\nVerifique se o arquivo de configuracao esta correto!\n")
        exit()

@app.route('/addPlotToDelete', methods=["POST"])
def addToPlotsDelete():
    global totalRequest
    totalRequest += 1
    json_data = request.json
    db.insert({"id": str(totalRequest), "deletePath": json_data["deletePath"]})
    return str(db.all())

def runApp():
    app.run(host='0.0.0.0', port=6343)

def killer(process_name):
    try:
        os.system("taskkill /im "+process_name+".exe")
    except:
        pass
    else:
        pass

def hpoolStart():
    if conf.hpoolControl.enabled:
        hpoolProcess = subprocess.Popen(hpoolPath)
        return hpoolProcess

def hpoolFirstStart():
    if conf.hpoolControl.enabled:
        killer('hpool-miner-chia-gui')
        time.sleep(2)
        hpoolProcess = hpoolStart()
        return hpoolProcess
    return None

def hpoolFinish(hpoolProcess):
    if conf.hpoolControl.enabled:
        hpoolProcess.terminate()

def getPlotFiles(plotsPath):
    plotsList = [f for f in os.listdir(plotsPath) if len(f.split('.plot')) == 2]
    return plotsList

def deleteDbItem(db, dbItem):
    db.remove(searchDb.id == dbItem["id"])

if __name__ == "__main__":
    multiprocessing.freeze_support()
    p = multiprocessing.Process(target=runApp)
    p.start()
    hpoolControl = hpoolFirstStart()

    while True:
        dbitens = db.all()
        if len(dbitens) > 0:
            print("\nDeletando:", dbitens)
            hpoolFinish(hpoolControl)
            time.sleep(2)
            for pathItem in dbitens:
                deletePath = pathItem["deletePath"]
                if os.path.exists(deletePath):
                    plotsList = getPlotFiles(deletePath)
                    if len(plotsList) > 0:
                        fileDelete = deletePath+"/"+plotsList[0]
                        try:
                            os.remove(fileDelete)
                        except Exception as e:
                            print("Nao foi possivel deletar o arquivo:", fileDelete, "\n\nA seguinte excecao aconteceu:\n", e)
                        else:
                            print("Para o item:", pathItem, "\nDeletou:", fileDelete)
                    else:
                        print("Para o item:", pathItem, "\nNao foi necessario deletar, diretorio nao tem plots")
                else:
                    print("Nao foi encontrado o diretorio:", deletePath, "para deletar!")
                deleteDbItem(db, pathItem)
            hpoolControl = hpoolStart()
        time.sleep(2)