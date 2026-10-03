import paho.mqtt.client as mqtt
IP = input("Inserisci l'indirizzo ip del broker mqtt:")
NOME_ACQUARIO = input("Inserisci il nome dell'acquario:")
def on_connect(client,userdata,flags,reason_code,properties):
    print(f"Connesso con risultato {reason_code}")
    #da inviare ad arduino
    campionamentoPh = input("Inserisci il tempo di campionamento del ph:")
    campionamentoLivelloAcqua = input("Inserisci il tempo di campionamento del livello dell'acqua: ")
    campionamentoTemperatura = input("Inserisci il tempo di campionamento della temperatura: ")
    #da inviare via mqtt al broker e devono essere ricevuti da mqttPyLogic.py e mqttPySaver.py
    minPh = input("Inserisci il valore minimo consentito del ph:")
    maxPh = input("inserisci il valore massimo consentito del ph:")
    minTemperatura = input("Inserisci il valore minimo consentito della temperatura:")
    maxTemperatura = input("Inserisci il valore massimo consentito della temperatura:")
    minLvl = input("Inserisci il valore minimo consentito del livello dell'acqua :")
    maxLvl = input("Inserisci il valore massimo consentito del livello dell'acqua:")
    intervalloPh = f"{minPh},{maxPh}"
    intervalloTemperatura = f"{minTemperatura},{maxTemperatura}"
    intervalloLivello = f"{minLvl},{maxLvl}"
    topicPublisher(NOME_ACQUARIO,"configurazione/temporizzazione","tempoPh",campionamentoPh)
    topicPublisher(NOME_ACQUARIO,"configurazione/temporizzazione","tempoLivelloAcqua",campionamentoLivelloAcqua)
    topicPublisher(NOME_ACQUARIO,"configurazione/temporizzazione","tempoTemperatura",campionamentoTemperatura)
    topicPublisher(NOME_ACQUARIO,"configurazione/valoreLimite","ph",intervalloPh)
    topicPublisher(NOME_ACQUARIO,"configurazione/valoreLimite","tmp",intervalloTemperatura)
    topicPublisher(NOME_ACQUARIO,"configurazione/valoreLimite","lvl",intervalloLivello)
def on_message(client,userdata,msg):
    print(f"Messaggio ricevuto su {msg.topic}: {msg.payload.decode()}")

def topicPublisher(nome,tipoTopic,tipoMisurazione,tempoCampionamento):
    mqttClient.publish("acquari/"+str(nome)+"/"+str(tipoTopic)+"/"+str(tipoMisurazione),str(tempoCampionamento))
    

mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message

mqttClient.connect(IP,1883,60)

mqttClient.loop_forever()