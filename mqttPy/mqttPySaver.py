import paho.mqtt.client as mqtt
import sqlite3 as db

database = db.connect("datiSensori.db")
cursor = database.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS acquario(
        nome TEXT NOT NULL PRIMARYKEY,
        litri DECIMAL(10,2))
    )
    '''
)
#CREARE LA TABELLA CHE RAPPRESENTA I DATI DI TIPO PH
def on_connect(client,userdata,flags, reason_code,properties):
    print(f"Connesso al broker con risultato {reason_code}")
    client.subscribe("acquari/#")


def on_message(client,userdata,msg):
    if(msg.topic.split("/")[-3]=="acquario1"):
        print("wakawaka eheh")



mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message

mqttClient.connect("192.168.0.34",1883,60)


mqttClient.loop_forever()