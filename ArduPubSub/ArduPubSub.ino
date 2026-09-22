#include<WiFi.h>
#include <PubSubClient.h>
#include "TOPIC.h"
const char* ssid = "Alessio";
const char* password = "ale2802_";
const char* mqttbkr = "172.20.10.2";
WiFiClient clientWiFi;
PubSubClient client(clientWiFi);
char* nome = "Acquario4";



/* Spazio per sensori e valori */
float ph = 8.0;
float livelloAcqua =  49.0;
float temperatura  = 12.0;
int check = 0;



/*Spazio per attuatori*/
void setup() {
  Serial.begin(115200); 
  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED){
    delay(1000);
    Serial.println("Connessione al wifi in corso");
  }
  Serial.println("Connesso al wifi");
  client.setServer(mqttbkr,1883);
  client.setCallback(callback);
  while(!client.connected()){
    Serial.println("CONNESSIONE AL BROKER MQTT");
    if(client.connect(nome)){
      Serial.println("CONNESSIONE EFFETTUATA");
       client.subscribe(createTopic(nome,8));
    }else{
      Serial.print("Fallito, rc = ");
      Serial.print(client.state());
      Serial.println("Riprovare"); 
      delay(5000);
    }
  }

}

void loop() {
  if(!client.connected()){
    Serial.println("Riconnessione al broker ");
    client.connect(nome);
  }
  if(check == 0){
    client.publish("acquari/nome",nome);
  }
  client.loop();
 //client.publish("test/mqtt","Messaggio di test da arduino giga");
  publishFloatVals(client,ph,createTopic(nome,0));
  publishFloatVals(client,livelloAcqua,createTopic(nome,1));
  publishFloatVals(client,temperatura,createTopic(nome,2));


  Serial.println("Messaggio inviato"); 
  delay(5000); 
}

void publishFloatVals(PubSubClient& t, float val, const char* topic) {
    char msg[20];
    snprintf(msg, sizeof(msg), "%1.2f", val);
    t.publish(topic, msg);
}   

void callback(char* topic, byte* payload, unsigned int length) {
    String msg;
    for (unsigned int i = 0; i < length; i++) {
        msg += (char)payload[i];
    }

    Serial.print("Ricevuto su: ");
    Serial.print(topic);
    Serial.print(" → ");
    Serial.println(msg);

    if (strcmp(topic, createTopic(nome,4)) == 0) {
        // pompa a immersione
       // digitalWrite(PIN_POMPAR, msg == "ON" ? HIGH  
       Serial.println("POMPA RIEMPIMENTO: ");Serial.print(msg+"\n");

    } else if (strcmp(topic, createTopic(nome,5)) == 0) {
        // pompa a superficie
       // digitalWrite(PIN_POMPAS, msg == "ON" ? HIGH : LOW);
       Serial.println("POMPA SVUOTAMENTO: "); Serial.print(msg+"\n");

    } else if (strcmp(topic, createTopic(nome,6)) == 0) {
        // riscaldatore
       // digitalWrite(PIN_RISC, msg == "ON" ? HIGH : LOW);
       Serial.println("RISCALDATORE: "); Serial.print(msg+"\n");
       
      }
}

char* createTopic(char* nome, int pos) {
    static char topic[100];

    const char* suffix[9] = {
        "sensori/ph",
        "sensori/lvl",
        "sensori/tmp",
        "sensori/time",
        "attuatori/pr",
        "attuatori/ps",
        "attuatori/risc",
        "attuatori/luce",
        "attuatori/#"
    };

    snprintf(topic, sizeof(topic), "acquari/%s/%s", nome, suffix[pos]);

    return topic;
}
