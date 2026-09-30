import paho.mqtt.client as mqtt
IP = input("Inserisci l'indirizzo ip del broker mqtt:")
NOME_ACQUARIO = input("Inserisci il nome dell'acquario:")
def on_connect(client,userdata,flags,reason_code,properties):
    print(f"Connesso con risultato {reason_code}")
    campionamentoPh = input("Inserisci il tempo di campionamento del ph:")
    campionamentoLivelloAcqua = input("Inserisci il tempo di campionamento del livello dell'acqua: ")
    campionamentoTemperatura = input("Inserisci il tempo di campionamento della temperatura: ")

    topicPublisher(NOME_ACQUARIO,"configurazione/temporizzazione","ph",campionamentoPh)
    topicPublisher(NOME_ACQUARIO,"configurazione/temporizzazione","livello_acqua",campionamentoLivelloAcqua)
    topicPublisher(NOME_ACQUARIO,"configurazione/temporizzazione","temperatura",campionamentoTemperatura)

def on_message(client,userdata,msg):
    print(f"Messaggio ricevuto su {msg.topic}: {msg.payload.decode()}")

def topicPublisher(nome,tipoTopic,tipoMisurazione,tempoCampionamento):
    mqttClient.publish("acquari/"+str(nome)+"/"+str(tipoTopic)+"/"+str(tipoMisurazione),str(tempoCampionamento))


mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message

mqttClient.connect(IP,1883,60)

mqttClient.loop_forever()