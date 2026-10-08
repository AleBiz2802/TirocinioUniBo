import paho.mqtt.client as mqtt
import time
from datetime import datetime
import sqlite3 as db
IP = input("Inserisci l'indirizzo ip del broker mqtt:")
database = db.connect("datiSensori.db")
utlima_ora = 0 
cursor = database.cursor()
def on_connect(client,userdata,flags,reason_code,properties):
    print(f"Connesso con risultato {reason_code}")
    client.subscribe("acquari/nome")
def on_message(client,userdata,msg):
    topicBuilder(client,userdata,msg,"sensori")
    print(msg.topic+" "+str(msg.payload.decode('utf-8')))
    
    checkValuesAndTakeAction(msg)
        
   # if msg.topic.split("/")[-3] == "acquario1" : 
    '''
    match msg.topic.split("/")[-1]: 
       case "tmp": 
            if float(msg.payload.decode()) > searchValInDb(msg.topic.split("/")[-3],"tmp")[1]:
                topicPublisher(msg,"LOW")
                print("Spegnere il riscaldatore")
            elif float(msg.payload.decode()) < searchValInDb(msg.topic.split("/")[-3],"tmp")[0]:
                topicPublisher(msg,"HIGH")
                print("Accendere il riscaldatore")
       case "lvl": 
            if float(msg.payload.decode()) < 50:
               
                topicPublisher(msg,"HIGH")
                print("Accendere la pompa")
            elif float(msg.payload.decode()) == 100:
                
                topicPublisher(msg,"LOW")
                print("Spegnere la pompa")
       case "ph": 
            if float(msg.payload.decode())>7.5 or float(msg.payload.decode())<6.5:
                
                topicPublisher(msg,"HIGH")
                print("Accendere pompa di svuotamento")
    '''
    
def topicBuilder(client,userdata,msg,subtopic):
    subTopic = f"/{subtopic}/"
    if(msg.topic.split("/")[-1] == "nome"):
        client.subscribe("acquari/"+str(msg.payload.decode('utf-8'))+subTopic+"#")
def topicPublisher(msg,val):
    
    match msg.topic.split("/")[-1]:
        case "tmp":
            mqttClient.publish("acquari/"+str(msg.topic.split("/")[-3])+"/"+"attuatori/"+"risc",val)
        case "lvl":
            mqttClient.publish("acquari/"+str(msg.topic.split("/")[-3])+"/"+"attuatori/"+"pr",val)
        case "ph":
            mqttClient.publish("acquari/"+str(msg.topic.split("/")[-3])+"/"+"attuatori/"+"ps",val)

def searchValInDb(nomeAcquario,tipoMisurazione):
    if tipoMisurazione == "ph":

        cursor.execute('''
                    SELECT phMin, phMax 
                    FROM configurazionePh
                    WHERE nomeAcquario = ?
                    ''',(nomeAcquario,))
    elif tipoMisurazione == "tmp":
        cursor.execute('''
                    SELECT tempMin, tempMax 
                    FROM configurazioneTemperatura
                    WHERE nomeAcquario = ?
                    ''',(nomeAcquario,)) 
    elif tipoMisurazione == "lvl":
        cursor.execute('''
            SELECT lvlMin, lvlMax
            FROM configurazioneLivello
            WHERE nomeAcquario = ?
        ''',(nomeAcquario,))
        
    result = cursor.fetchone()
    if result is not None:
        return result
    else:   
        return None
"""
def checkValuesAndTakeAction(msg):
    intervalloValori = searchValInDb(msg.topic.split("/")[-3], msg.topic.split("/")[-1])
    if intervalloValori is not None:
        valoreMin, valoreMax = intervalloValori
        if float(msg.payload.decode()) < valoreMin or float(msg.payload.decode()) > valoreMax:
            topicPublisher(msg,val = "HIGH" if float(msg.payload.decode())<valoreMin else "LOW")
        else : 
            print(f"Valore di {msg.topic.split('/')[-1]} per l'acquario {msg.topic.split('/')[-3]} è nella norma : {msg.payload.decode('utf-8')}")
"""
def checkValuesAndTakeAction(msg):
    if msg.topic.split("/")[-2]=="sensori":
        tipoMisurazione,acquario = msg.topic.split("/")[-1], msg.topic.split("/")[-3] 
        intervalloValori = searchValInDb(acquario, tipoMisurazione)
        valoreMin, valoreMax = intervalloValori if intervalloValori is not None else (None,None)
        valoreAttuale = float(msg.payload.decode())
        if(valoreMin and valoreMax is not None):
            match tipoMisurazione:
                case "tmp":
                    if valoreAttuale < valoreMin:
                        topicPublisher(msg,"HIGH")
                        print(f"Valore di {tipoMisurazione} per l'acquario{acquario} è troppo basso: {valoreAttuale}. Riscaldatore acceso.")
                    elif valoreAttuale >= valoreMax:
                        topicPublisher(msg,"LOW")
                        print(f"Acquario {acquario} in temperatura:{valoreAttuale}. Riscaldatore spento.")
                case "lvl":
                    if valoreAttuale < valoreMin:
                        topicPublisher(msg,"HIGH")
                        print(f"Livello dell'acqua troppo basso: {valoreAttuale}.Pompa di riempimento attivata")
                    elif valoreAttuale >= valoreMax:
                        topicPublisher(msg,"LOW")
                        print(f"Livello dell'acqua ripristinato {valoreAttuale}. Pompa di riempimento disattivata")


def computePhMean(data):
    cursor.execute("""
        SELECT datiAcquario.nomeAcquario, AVG(misurazione)
        FROM datiAcquario,configurazionePh
        WHERE datiAcquario.nomeAcquario = configurazionePh.nomeAcquario AND tipoMisurazione = 'ph' AND data >= ? 
        GROUP BY datiAcquario.nomeAcquario
        HAVING AVG(misurazione)>phMax OR AVG(misurazione)<phMin;
    """,(data,))
    risultato = cursor.fetchall()
    for r in risultato: 
        print(f"{r[0]}")    
"""
Progettare la funzione che gestisce il ciclo di cambio di acqua quando il ph differisce dalla soglia. 

COSA DEVE FARE: 
Ogni ora il servizio richiede la media dei valori del ph. 
Controlla che la media dei valori ora dopo ora sia all'interno dell'intervallo stabilito nella configurazionePh
Se il valore è superiore o inferiore -> Scrive sul topic "Notifiche" 
L'app, iscritta al topic "Notifiche", successivamente invierà una notifica all'utente "Il Ph dell'acquario x è fuori soglia, necessario  cambio d'acqua"

Durante il cambio dell'acqua, quell'acquario non può eseguire nient'altro tranne che l'interruzione da parte dell'utente
"""


mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message

mqttClient.connect(IP,1883,60)

mqttClient.loop_forever()


