import paho.mqtt.client as mqtt


def on_connect(client,userdata,flags,reason_code,properties):
    print(f"Connesso con risultato {reason_code}")
    client.subscribe("acquari/nome")

def on_message(client,userdata,msg):
    topicBuilder(client,userdata,msg)
    print(msg.topic+" "+str(msg.payload.decode('utf-8')))
   # if msg.topic.split("/")[-3] == "acquario1" : 
    match msg.topic.split("/")[-1]: 
        case "tmp": 
            if float(msg.payload.decode()) > 28.0:
                #mqttClient.publish("acquari/acquario1/attuatori/risc","LOW")
                topicPublisher(msg,"LOW")
                print("Spegnere il riscaldatore")
            elif float(msg.payload.decode()) < 22:
                #mqttClient.publish("acquari/acquario1/attuatori/risc","HIGH")
                topicPublisher(msg,"HIGH")
                print("Accendere il riscaldatore")
        case "lvl": 
            if float(msg.payload.decode()) < 50:
                #mqttClient.publish("acquari/acquario1/attuatori/pr", "HIGH")
                topicPublisher(msg,"HIGH")
                print("Accendere la pompa")
            elif float(msg.payload.decode()) == 100:
                #mqttClient.publish("acquari/acquario1/attuatori/pr","LOW")
                topicPublisher(msg,"LOW")
                print("Spegnere la pompa")
        case "ph": 
            if float(msg.payload.decode())>7.5 or float(msg.payload.decode())<6.5:
                #mqttClient.publish("acquari/acquario1/attuatori/ps","HIGH")
                topicPublisher(msg,"HIGH")
                print("Accendere pompa di svuotamento")

def topicBuilder(client,userdata,msg):
    if(msg.topic.split("/")[-1] == "nome"):
        client.subscribe("acquari/"+str(msg.payload.decode('utf-8'))+"/sensori/"+"#")
def topicPublisher(msg,val):
    
    match msg.topic.split("/")[-1]:
        case "tmp":
            mqttClient.publish("acquari/"+str(msg.topic.split("/")[-3])+"/"+"attuatori/"+"risc",val)
        case "lvl":
            mqttClient.publish("acquari/"+str(msg.topic.split("/")[-3])+"/"+"attuatori/"+"pr",val)
        case "ph":
            mqttClient.publish("acquari/"+str(msg.topic.split("/")[-3])+"/"+"attuatori/"+"ps",val)
    
            
mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message

mqttClient.connect("172.20.10.2",1883,60)

mqttClient.loop_forever()