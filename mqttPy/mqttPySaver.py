import paho.mqtt.client as mqtt
import sqlite3 as db
IP = input("Inserisci l'indirizzo ip del broker mqtt:")
database = db.connect("datiSensori.db")
cursor = database.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS acquario(
        nome VARCHAR(30) NOT NULL PRIMARY KEY,
        litri DECIMAL(10,2)
    )
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS configurazioneTemperatura(
    nomeAcquario VARCHAR(30) NOT NULL PRIMARY KEY,
    tempMin DECIMAL(10,2),
    tempMax DECIMAL(10,2)
   )
''')
cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS configurazionePh(
        nomeAcquario VARCHAR(30) NOT NULL PRIMARY KEY,
        phMin DECIMAL(10,2),
        phMax DECIMAL(10,2)
    )
    '''
)
cursor.execute(
    '''
        CREATE TABLE IF NOT EXISTS configurazioneLivello(
            nomeAcquario VARCHAR(30) NOT NULL PRIMARY KEY,
            lvlMin DECIMAL(10,2),
            lvlMax DECIMAL(10,2 )
        )
    '''
)

#CREARE LA TABELLA CHE RAPPRESENTA I DATI INVIATI DA ARDUINO 
cursor.execute('''
    CREATE TABLE IF NOT EXISTS datiAcquario(
        idMisurazione INTEGER PRIMARY KEY AUTOINCREMENT,
        nomeAcquario TEXT NOT NULL,
        data DATETIME,
        tipoMisurazione VARCHAR(30) NOT NULL,
        misurazione DECIMAL(10,2),
        FOREIGN KEY (nomeAcquario) REFERENCES acquario(nome) ON DELETE CASCADE
    )
''')   
def on_connect(client,userdata,flags, reason_code,properties):
    print(f"Connesso al broker con risultato {reason_code}")
    client.subscribe("acquari/nome")
    
    
def addValToDb(nome,tipoMisurazione,misurazione):
    cursor.execute('''
                    INSERT INTO datiAcquario(nomeAcquario,
                                             tipoMisurazione,
                                             misurazione
                                            )VALUES(?,?,?);
                    ''',(nome,tipoMisurazione,misurazione))
    database.commit()
    print(f"Salvato sul db : {nome}, {tipoMisurazione}, {misurazione}")

def topicBuilder(client,userdata,msg,subtopic):
    if(msg.topic.split("/")[-1] == "nome"):
        client.subscribe("acquari/"+str(msg.payload.decode('utf-8'))+subtopic)
        print(f"Iscritto al topic: acquari/"+str(msg.payload.decode('utf-8'))+subtopic)

def on_message(client,userdata,msg):
    if msg.topic.split("/")[0]=="acquari":
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
                cursor.execute('''INSERT INTO acquario(nome)VALUES(?);''',(msg.payload.decode('utf-8'),))
                database.commit()
            topicBuilder(client,userdata,msg,"/sensori/#")
            topicBuilder(client,userdata,msg,"/configurazione/valoreLimite/#")
        if msg.topic.split("/")[-2]=="sensori":
                addValToDb(msg.topic.split("/")[-3],msg.topic.split("/")[-1],float(msg.payload.decode()))
        if msg.topic.split("/")[-2]=="valoreLimite":
            inserisciConfigurazione(msg.topic.split("/")[-4],
                                    msg.topic.split("/")[-1],
                                    float(msg.payload.decode().split(",")[0]),
                                    float(msg.payload.decode().split(",")[1]))
        
                 

def inserisciConfigurazione(nomeAcquario,tipoMisurazione,valoreMin,valoreMax):
    match tipoMisurazione:
        case "ph":
            cursor.execute('''
                INSERT INTO configurazionePh(nomeAcquario,phMin,phMax
                ) VALUES(?,?,?);
            ''',(nomeAcquario,valoreMin,valoreMax))        
            database.commit()
        case "tmp":
            cursor.execute('''
                INSERT INTO configurazioneTemperatura(nomeAcquario,tempMin,tempMax
                ) VALUES(?,?,?);
            ''',(nomeAcquario,valoreMin,valoreMax))
            database.commit()
        case "lvl":
            cursor.execute('''
                INSERT INTO configurazioneLivello(nomeAcquario,lvlMin,lvlMax)VALUES(?,?,?)
            ''',(nomeAcquario,valoreMin,valoreMax))
mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message

mqttClient.connect(IP,1883,60)


mqttClient.loop_forever() 