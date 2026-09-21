#include<WiFi.h>
#include <PubSubClient.h>
#include "TOPIC.h"
const char* ssid = "Veradsl-Bizzarri";
const char* password = "15172830";
const char* mqttbkr = "192.168.0.34";
WiFiClient clientWiFi;
PubSubClient client(clientWiFi);
char* nome = "Acquario1";



/* Spazio per sensori e valori */
float ph = 8.0;
float livelloAcqua = 50.0;
float temperatura  = 28.0;




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
       client.subscribe("acquari/acquario1/attuatori/#");
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
  client.loop();
 //client.publish("test/mqtt","Messaggio di test da arduino giga");
  publishFloatVals(client,ph,PH);
  publishFloatVals(client,livelloAcqua,LIVELLO_ACQUA);
  publishFloatVals(client,temperatura,TEMPERATURA);


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

    if (strcmp(topic, POMPAR) == 0) {
        // pompa a immersione
       // digitalWrite(PIN_POMPAR, msg == "ON" ? HIGH  
       Serial.println("POMPA RIEMPIMENTO: ");Serial.print(msg+"\n");

    } else if (strcmp(topic, POMPAS) == 0) {
        // pompa a superficie
       // digitalWrite(PIN_POMPAS, msg == "ON" ? HIGH : LOW);
       Serial.println("POMPA SVUOTAMENTO: "); Serial.print(msg+"\n");

    } else if (strcmp(topic, RISCALDATORE) == 0) {
        // riscaldatore
       // digitalWrite(PIN_RISC, msg == "ON" ? HIGH : LOW);
       Serial.println("RISCALDATORE: "); Serial.print(msg+"\n");
       
      }
}   