#include<WiFi.h>
#include <PubSubClient.h>
const char* ssid = "Alessio";
const char* password = "ale2802_";
const char* mqttbkr = "172.17.0.1 ";
WiFiClient clientWiFi;
PubSubClient client(clientWiFi);
char* nome = "Acquario1";
void setup() {
  Serial.begin(115200); 
  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED){
    delay(1000);
    Serial.println("Connessione al wifi in corso");
  }
  Serial.println("Connesso al wifi");
  client.setServer(mqttbkr,1883);
  while(!client.connected()){
    Serial.println("CONNESSIONE AL BROKER MQTT");
    if(client.connect(nome)){
      Serial.println("CONNESSIONE EFFETTUATA");
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
  client.publish("test/mqtt","Messaggio di test da arduino giga"); 
  Serial.println("Messaggio inviato"); 
  delay(5000); 
  client.loop();
}
