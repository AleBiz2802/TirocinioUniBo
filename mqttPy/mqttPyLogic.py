import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

def on_connect(client,userdata,flags,reason_code,properties):
    print(f"Connesso con risultato {reason_code}")
    client.subscribe("acquari/acquario1/sensori/#")
    

def on_message(client,userdata,msg):
    print(msg.topic+" "+str(msg.payload.decode('utf-8')))
    if msg.topic.split("/")[-3] == "acquario1" : 
        match msg.topic.split("/")[-1]: 
            case "tmp": 
                if float(msg.payload.decode()) > 28.0:
                    mqttClient.publish("acquari/acquario1/attuatori/risc","LOW")
                    print("Spegnere il riscaldatore")
                elif float(msg.payload.decode()) < 22:
                    mqttClient.publish("acquari/acquario1/attuatori/risc","HIGH")
                    print("Accendere il riscaldatore")
            case "lvl": 
                if float(msg.payload.decode()) < 50:
                    mqttClient.publish("acquari/acquario1/attuatori/pr", "HIGH")
                    print("Accendere la pompa")
                elif float(msg.payload.decode()) == 100:
                    mqttClient.publish("acquari/acquario1/attuatori/pr","LOW")
                    print("Spegnere la pompa")
            case "ph": 
                if float(msg.payload.decode())>7.5 or float(msg.payload.decode())<6.5:
                    mqttClient.publish("acquari/acquario1/attuatori/ps","HIGH")
                    print("Accendere pompa di svuotamento")
            
mqttClient = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttClient.on_connect = on_connect
mqttClient.on_message = on_message

mqttClient.connect("192.168.0.34",1883,60)

mqttClient.loop_forever()