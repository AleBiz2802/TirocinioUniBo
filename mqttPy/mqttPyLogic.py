import paho.mqtt.client as mqtt

import threading
import os 
import time as tm
from datetime import time, timedelta, datetime
import sqlite3 as db
from influxdb_client_3 import (
  InfluxDBClient3, InfluxDBError, Point, WritePrecision,
  WriteOptions, write_client_options)
from dotenv import load_dotenv

load_dotenv("INFLUX_ENV.env")
print(load_dotenv("INFLUX_ENV.env"))

host = os.getenv('HOST')
token = os.getenv('TOKEN')
influxdb = os.getenv('DATABASE')


influxClient = InfluxDBClient3(host=host,
                        token=token,
                        database=influxdb) 
IP = input("Inserisci l'indirizzo ip del broker mqtt:")
database = db.connect("datiSensori.db",check_same_thread=False)

cursor = database.cursor()

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connesso con risultato {reason_code}")
    client.subscribe("acquari/nome")
    
def on_message(client,userdata,msg):
    
    topicBuilder(client,msg,"sensori")
    print(msg.topic+" "+str(msg.payload.decode('utf-8')))
     
    checkValuesAndTakeAction(msg)
    
def topicBuilder(client,msg,subtopic):
    subTopic = f"/{subtopic}/"
    if(msg.topic.split("/")[-1] == "nome"):
        client.subscribe("acquari/"+str(msg.payload.decode('utf-8'))+subTopic+"#")
        client.subscribe("acquari/" + str(msg.payload.decode('utf-8')) + "/manual") 

def topicPublisher(msg):
    topic = msg.topic.split("/")
    acquario = topic[-3]
    tipo = topic[-1]

    if tipo not in ("tmp","lvl"):
        return

    val = float(msg.payload.decode())
    baseTopic = "acquari/" + acquario + "/attuatori/"

    # fetchone() ritorna una tupla (o None): estraggo il valore
    riga = cursor.execute('''
                        SELECT stato
                        FROM statoAcquario
                        WHERE nomeAcquario = ?
                        ''',(acquario,)).fetchone()
    statoAcquario = riga[0] if riga else None

    intervallo = searchValInDb(acquario,tipo)
    if intervallo is None:
        return
    valMin,valMax = intervallo

    match tipo:
        case "tmp":
            if val>valMax:
                mqttClient.publish(baseTopic+"risc","LOW")
            elif val<valMin:
                mqttClient.publish(baseTopic+"risc","HIGH")

        case "lvl":
            dati = cursor.execute('''
                                   SELECT litri,vuoto,pieno
                                   FROM acquario
                                   WHERE nome = ?
                                   ''',(acquario,)).fetchone()
            
            if dati is None:
                return
            litri,vuoto,pieno = dati[0],dati[1],dati[2]
            if None in (litri,vuoto,pieno):
                return
            if pieno == vuoto:
                return
            
            max = litri*(valMax/100)
            min = litri*(valMin/100)
            
            cambio = litri-(0.2*litri)
            attuale =(litri/(pieno-vuoto))*(float(msg.payload.decode())-vuoto)
            
            print(f"valore massimo:{valMax}, valore minimo: {valMin}, valCambio: {cambio}")
            if statoAcquario != "CAMBIO_ACQUA":
                if not(min<=attuale<=max):
                    if attuale<min:
                        mqttClient.publish(baseTopic+"pr","HIGH")
            else:
                if attuale<=cambio:
                   mqttClient.publish(baseTopic+"pr","HIGH")
                elif attuale>=max:
                    mqttClient.publish(baseTopic+"pr","LOW")
                
            
                        
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
            SELECT min_val, max_val
            FROM configurazioneLivello
            WHERE nomeAcquario = ?
        ''',(nomeAcquario,))
    else:
        # tipo non gestito: evito di leggere i risultati di una query precedente
        return None
        
    result = cursor.fetchone()
    if result is None or result[0] is None or result[1] is None:
        return None
    return result

def manualMode(msg):
    if msg.topic.split("/")[-1] == "manual":
        baseTopic = "acquari/" + msg.topic.split("/")[-2] + "/attuatori/"
        match str(msg.payload.decode("utf-8")):
            case "svuotamento":
                mqttClient.publish(baseTopic+"ps","HIGH")
                mqttClient.publish(baseTopic+"pr","LOW")
            case "riempimento":
                mqttClient.publish(baseTopic+"ps","LOW")
                mqttClient.publish(baseTopic+"pr","HIGH")
            case "stop":
                mqttClient.publish(baseTopic+"ps","LOW")
                mqttClient.publish(baseTopic+"pr","LOW")
            case  "riscaldamento":
                mqttClient.publish(baseTopic+"risc","HIGH")
            case "raffreddamento":
                mqttClient.publish(baseTopic+"risc","LOW")
            case "spegni":
                   mqttClient.publish(baseTopic+"ps","LOW")
                   mqttClient.publish(baseTopic+"pr","LOW")
                   mqttClient.publish(baseTopic+"luce","LOW")
                   mqttClient.publish(baseTopic+"filtro","LOW")
                   mqttClient.publish(baseTopic+"risc","LOW")
        
            
            
def checkValuesAndTakeAction(msg):
    parts = msg.topic.split("/")
    if len(parts) < 3:
        return
    nome_acquario = parts[1]

    row = cursor.execute(
        "SELECT mode FROM acquario WHERE nome = ?",
        (nome_acquario,)
    ).fetchone()
    mode = row[0].upper() if row and row[0] else None

    if mode == "AUTO":
        if parts[-2] == "sensori":
            topicPublisher(msg)
    elif mode == "MANUAL":
        manualMode(msg)
        
                

def computePhMean():
    phValues = influxClient.query(
            query="""
                SELECT "Acquario", AVG(ph) as ph_medio
                FROM "Acquari"
                WHERE time >= current_date()
                AND time < current_date() + INTERVAL '1 day'
                GROUP BY "Acquario"
                """,
            language="sql",
            timeout=10
        ).to_pylist()
    
    for p in phValues:
        intervallo = searchValInDb(str(p["Acquario"]),"ph")
        if intervallo is None:
            continue

        phMin,phMax = intervallo

        if phMin is None or phMax is None or p["ph_medio"] is None:
            continue

        if not (phMin<=p["ph_medio"]<=phMax):
            mqttClient.publish("acquari/"+str(p["Acquario"])+"/attuatori/ps", "HIGH")
            mqttClient.publish("stato/"+str(p["Acquario"]),"CAMBIO_ACQUA")


def trigger(target: time):

    targettime = datetime.now().replace(hour=target.hour, minute=target.minute, second=0, microsecond=0)
    if targettime<= datetime.now():
        targettime += timedelta(days=1)

    while datetime.now() < targettime:
        tm.sleep(1)

    computePhMean()

#impostare sessione di gestione luci, quando si è fuori dal tempo di illuminazione si spengono le luci
def setLights():
    while True:
        try:
            righe = cursor.execute(
                "SELECT nomeAcquario, accensione, spegnimento FROM configurazioneLuci"
            ).fetchall()
            adesso = datetime.now().time()
            for nome, acc, spe in righe:
                if not acc or not spe:
                    continue
                on = datetime.strptime(acc.strip(), "%H:%M").time()
                off = datetime.strptime(spe.strip(), "%H:%M").time()
                if on <= off:
                    accesa = on <= adesso < off
                else:  # l'intervallo attraversa la mezzanotte
                    accesa = adesso >= on or adesso < off
                mqttClient.publish(f"acquari/{nome}/attuatori/luce",
                                   "LOW" if accesa else "HIGH", retain=True)
        except Exception as e:
            print("setLights:", e)
        tm.sleep(30)

    


        
mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message

mqttClient.connect(IP,1883,60)

threading.Thread(target=trigger, args=(time(22,30),),daemon=True).start()
threading.Thread(target=setLights,daemon=True).start()
mqttClient.loop_forever()