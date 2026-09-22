import paho.mqtt.client as mqtt
import sqlite3 as db
 
database = db.connect("datiSensori.db")
cursor = database.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS acquario(
        nome VARCHAR(30) NOT NULL PRIMARY KEY,
        litri DECIMAL(10,2) NOT NULL
    )
''')
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
    client.subscribe("acquari/#")
    
def addValToDb(nome,tipoMisurazione,misurazione):
    cursor.execute('''
                    INSERT INTO datiAcquario(nomeAcquario,
                                             tipoMisurazione,
                                             misurazione
                                            )VALUES(?,?,?);
                    ''',(nome,tipoMisurazione,misurazione))
    database.commit()
    print(f"Salvato sul db : {nome}, {tipoMisurazione}, {misurazione}")

def on_message(client,userdata,msg):
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM acquario
            WHERE nome = ?
        )
    """, (msg.topic.split("/")[-3],))
    acquario = cursor.fetchone()[0]
    if(acquario): 
        addValToDb(msg.topic.split("/")[-3],msg.topic.split("/")[-1],float(msg.payload.decode()))

        
    else:
        cursor.execute('''
            INSERT INTO acquario(nome,litri)VALUES(?,?);
        ''',(msg.topic.split("/")[-3],0.0))
        database.commit()
        



mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message

mqttClient.connect("172.20.10.2",1883,60)


mqttClient.loop_forever()