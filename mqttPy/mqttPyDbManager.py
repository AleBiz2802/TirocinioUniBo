import paho.mqtt.client as mqtt
import sqlite3 as db
import os
from influxdb_client_3 import (
  InfluxDBClient3, InfluxDBError, Point, WritePrecision,
  WriteOptions, write_client_options)
from dotenv import load_dotenv
from datetime import datetime
load_dotenv("INFLUX_ENV.env")
print(load_dotenv("INFLUX_ENV.env"))  
IP = input("Inserisci l'indirizzo ip del broker mqtt:")
#definizione del db serietemporale :
host = os.getenv('HOST')
token = os.getenv('TOKEN')
influxdb = os.getenv('DATABASE')


influxClient = InfluxDBClient3(host=host,
                        token=token,
                        database=influxdb) 

#definizione db sqlite
database = db.connect("datiSensori.db")
cursor = database.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS acquario(
        nome VARCHAR(30) NOT NULL PRIMARY KEY,
        mode VARCHAR(30) NOT NULL,
        litri DECIMAL(10,2),
        vuoto DECIMAL(10,2),
        pieno DECIMAL(10,2)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS statoAcquario(
        nomeAcquario VARCHAR (30) NOT NULL PRIMARY KEY,
        stato VARCHAR (20),
        FOREIGN KEY (nomeAcquario) REFERENCES acquario(nome) ON DELETE CASCADE
     )
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS configurazioneTemperatura(
    nomeAcquario VARCHAR(30) NOT NULL PRIMARY KEY,
    tempMin DECIMAL(10,2),
    tempMax DECIMAL(10,2),
    FOREIGN KEY (nomeAcquario) REFERENCES acquario(nome) ON DELETE CASCADE
   )
''')
cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS configurazionePh(
        nomeAcquario VARCHAR(30) NOT NULL PRIMARY KEY,
        phMin DECIMAL(10,2),
        phMax DECIMAL(10,2),
        FOREIGN KEY (nomeAcquario) REFERENCES acquario(nome) ON DELETE CASCADE
    )
    '''
)

cursor.execute(
    '''
        CREATE TABLE IF NOT EXISTS configurazioneLivello(
            nomeAcquario VARCHAR(30) NOT NULL PRIMARY KEY,
            min_val DECIMAL(10,2),
            max_val DECIMAL(10,2),
            FOREIGN KEY (nomeAcquario) REFERENCES acquario(nome) ON DELETE CASCADE
        )
    '''
)

cursor.execute(
    '''
        CREATE TABLE IF NOT EXISTS configurazioneLuci(
            nomeAcquario VARCHAR(30) NOT NULL PRIMARY KEY,
            accensione TEXT,
            spegnimento TEXT,
            FOREIGN KEY (nomeAcquario)REFERENCES acquario(nome)ON DELETE CASCADE
        );
    '''
)



def acquarioEsiste(nome):
    return cursor.execute(
        "SELECT 1 FROM acquario WHERE nome = ?", (nome,)
    ).fetchone() is not None


def on_connect(client,userdata,flags, reason_code,properties):
    print(f"Connesso al broker con risultato {reason_code}")
    client.subscribe("acquari/nome")
    client.subscribe("stato/#")
    client.subscribe("elimina")
    
    

def addValToDbInflux(msg):
    datiAcquario = [
        Point("Acquari")
        .tag("Acquario",msg.topic.split("/")[-3])
        .field(msg.topic.split("/")[-1],float(msg.payload.decode()))
    ]
    return datiAcquario

def logActuatorState(msg):
    attuatori = [
        Point("Attuatori")
        .tag("Attuatore",msg.topic.split("/")[-1])
        .field(msg.topic.split("/")[-3],msg.payload.decode("utf-8"))
    ]
    return attuatori

def topicBuilder(client,userdata,msg,subtopic):
    if(msg.topic.split("/")[-1] == "nome"):
        client.subscribe("acquari/"+str(msg.payload.decode('utf-8'))+subtopic)
        print(f"Iscritto al topic: acquari/"+str(msg.payload.decode('utf-8'))+subtopic)

def on_message(client,userdata,msg):
    try:
        gestisciMessaggio(client,userdata,msg)
    except Exception as e:
        # un errore su un messaggio non deve fermare il client MQTT
        database.rollback()
        print(f"on_message errore su {msg.topic}: {e!r}")


def gestisciMessaggio(client,userdata,msg):
    if msg.topic == "elimina":
        nome = msg.payload.decode("utf-8")
        client.unsubscribe(f"acquari/{nome}/sensori/#")
        client.unsubscribe(f"acquari/{nome}/configurazione/#")
        client.unsubscribe(f"acquari/{nome}/ultraSuoni/#")
        client.unsubscribe(f"acquari/{nome}/mode")
        cursor.execute("DELETE FROM acquario WHERE nome = ?", (nome,))
        database.commit()
        # svuota il messaggio retained, altrimenti alla prossima connessione
        # arriva uno stato per un acquario che non esiste piu'
        client.publish(f"stato/{nome}", None, retain=True)
        return
    elif msg.topic.split("/")[0]=="acquari":
        if msg.topic.split("/")[-1]=="nome":
            cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM acquario
                        WHERE nome = ?
                    )
                """, (msg.payload.decode('utf-8'),))
            acquario = cursor.fetchone()[0]
            if(not acquario):
                cursor.execute('''INSERT INTO acquario(nome,mode)VALUES(?,?);''',(msg.payload.decode('utf-8'),"AUTO",))
                database.commit()
            topicBuilder(client,userdata,msg,"/sensori/#")
            topicBuilder(client,userdata,msg,"/configurazione/#")
            topicBuilder(client,userdata,msg,"/ultraSuoni/#")
            topicBuilder(client,userdata,msg,"/mode")
            topicBuilder(client,userdata,msg,"/attuatori/#")
        if msg.topic.split("/")[-2]=="sensori":
                influxClient.write(addValToDbInflux(msg), write_precision='s')
        if msg.topic.split("/")[-2]=="attuatori":
                influxClient.write(logActuatorState(msg), write_precision='s')
        if msg.topic.split("/")[-2]in  ("valoreLimite","litraggio","luce"):
            inserisciConfigurazione(msg)
        if msg.topic.split("/")[-2]=="ultraSuoni":
            nome = msg.topic.split("/")[-3]
            if msg.topic.split("/")[-1]=="minLvl":
                
                cursor.execute('''
                                UPDATE acquario
                                SET vuoto = ?
                                WHERE nome = ?
                            ''',(float(msg.payload.decode()),nome))
                database.commit()
                
            elif msg.topic.split("/")[-1]=="maxLvl":
                cursor.execute('''
                    UPDATE acquario
                    SET pieno = ?
                    WHERE nome = ?
                ''',(float(msg.payload.decode()),nome))
                database.commit()
        if msg.topic.split("/")[-1]=="mode":
            nome = msg.topic.split("/")[-2]
            cursor.execute(
                        "UPDATE acquario SET mode = ? WHERE nome = ?",
                        (str(msg.payload.decode("utf-8")), nome),
                    )
            database.commit()
       
         
    elif msg.topic.split("/")[-2]=="stato":
        nome = msg.topic.split("/")[-1]
        stato = msg.payload.decode('utf-8')
        
        if not stato:
            return  # retained cancellato
        if not acquarioEsiste(nome):
            print(f"Stato ignorato: acquario '{nome}' non presente nel DB")
            return

        cursor.execute(
            """
            INSERT INTO statoAcquario(nomeAcquario, stato) VALUES (?, ?)
            ON CONFLICT(nomeAcquario) DO UPDATE SET stato = excluded.stato
            """,
            (nome, stato),
        )
        database.commit()
 
        


def inserisciConfigurazione(msg):
    nome = msg.topic.split("/")[-4]
    if not acquarioEsiste(nome):
        print(f"Configurazione ignorata: acquario '{nome}' non presente nel DB")
        return
    match msg.topic.split("/")[-1]:
        case "ph":
            
            ph_min, ph_max = float(msg.payload.decode().split(",")[0]),float(msg.payload.decode().split(",")[1])

            cursor.execute(
                "INSERT OR IGNORE INTO configurazionePh(nomeAcquario, phMin, phMax) VALUES (?, ?, ?)",
                (nome, ph_min, ph_max),
            )
            cursor.execute(
                "UPDATE configurazionePh SET phMin = ?, phMax = ? WHERE nomeAcquario = ?",
                (ph_min, ph_max, nome),
            )
            database.commit()
        case "tmp":
            tempMin, tempMax =  float(msg.payload.decode().split(",")[0]),float(msg.payload.decode().split(",")[1])
            
            cursor.execute(
                "INSERT OR IGNORE INTO configurazioneTemperatura(nomeAcquario, tempMin, tempMax) VALUES (?, ?, ?)",
                (nome, tempMin, tempMax),
            )
            cursor.execute(
                "UPDATE configurazioneTemperatura SET tempMin = ?, tempMax = ? WHERE nomeAcquario = ?",
                (tempMin, tempMax, nome),
            )
            database.commit()
        case "lvl":
            lvlMin, lvlMax =float(msg.payload.decode().split(",")[0]),float(msg.payload.decode().split(",")[1])
           
            cursor.execute(
                "INSERT OR IGNORE INTO configurazioneLivello(nomeAcquario, min_val, max_val) VALUES (?, ?, ?)",
                (nome, lvlMin,lvlMax),
            )
            cursor.execute(
                "UPDATE configurazioneLivello SET min_val = ?, max_val = ? WHERE nomeAcquario = ?",
                (lvlMin, lvlMax, nome),
            )
            database.commit()
        case "luce":
            accensione,spegnimento = str(msg.payload.decode("utf-8").split(",")[0]),str(msg.payload.decode("utf-8").split(",")[1])
            cursor.execute(
                            "INSERT OR IGNORE INTO configurazioneLuci(nomeAcquario, accensione, spegnimento) VALUES (?, ?, ?)",
                            (nome, accensione,spegnimento),
                        )
            cursor.execute(
                            "UPDATE configurazioneLuci SET accensione= ?, spegnimento= ? WHERE nomeAcquario = ?",
                            (accensione, spegnimento, nome),
                        )
            database.commit()

        case "litri":
            cursor.execute('''
                UPDATE acquario
                SET litri = ?
                WHERE nome = ?
            ''',(float(msg.payload.decode()),nome))
            database.commit()
 
 
mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message
mqttClient.connect(IP,1883,60)


mqttClient.loop_forever()